import json
import re
import jmespath
import scrapy
from scrapy import Request
import logging

from syntarget.items import SyntargetItem
from datetime import datetime



class TargetComSpider(scrapy.Spider):
    name = "target_com"

    start_urls = [
        "https://www.target.com/p/-/A-79344798",
        "https://www.target.com/p/-/A-13493042",
        "https://www.target.com/p/-/A-85781566",
    ]

    # def __init__(self, *args, **kwargs):
    #     super(TargetComSpider, self).__init__(*args, **kwargs)
    #     self.start_urls = [kwargs.get('url')]

    HEADER_LIST = {
        'authority': 'r2d2.target.com',
        'accept': 'application/json',
        'accept-language': 'en-IN,en;q=0.9,ar;q=0.8,en-GB;q=0.7,en-US;q=0.6,pa;q=0.5',
        'origin': 'https://www.target.com',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }

    products_jp = jmespath.compile(
        """
        queries[].product.{
            tcin: tcin,
            upc: item.primary_barcode,
            url: item.enrichment.buy_url,
            brand: item.primary_brand.name,
            specs: item.product_description.bullet_descriptions,
            description: item.product_description.downstream_description,
            bullets: item.product_description.join(``,soft_bullets.bullets),
            features: item.product_description.bullet_descriptions,
            title: item.product_description.title,
            ingredients: item.enrichment.nutrition_facts.ingredients,
            current_price: price.current_retail_min,
            regular_price: price.reg_retail,
            currency_symbol: price.formatted_current_price
        }
        """
        )

    questions_jp = jmespath.compile(
        """
        results[].{
            "question_id":id,
            "submission_date": submitted_at,
            "question_summary":text,
            "user_nickname":author.nickname,
            "answers":
                answers[].{
                    "answer_id":id,
                    "answer_summary":text,
                    "submission_date": submitted_at,
                    "user_nickname":author.nickname
                }
            }
            """
    )

    CURRENCY_SYMBOL_TO_CODE = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        # Add more currency symbols and their corresponding codes here
    }

    def extract_jdata(self, response):
        script_xpath = "//script[contains(text(), 'window.__PRELOADED_STATE__')]/text()"
        script = response.xpath(script_xpath).get()


        if script:
            json_text = re.sub(r'window\.__PRELOADED_STATE__\s*=\s*', '', script)

        else:
            json_data = re.findall(r'\'__TGT_DATA__\': { configurable: false, enumerable: true, value: deepFreeze\(\s*JSON\.parse\("(.+)"\)', response.text)
            jdata = json.loads(json_data[0].encode('utf-8').decode('unicode_escape'))

            return jdata

    def clean_data(self, raw_data):
        cleaned_data = []
        for item in raw_data:
            cleaned_item = re.sub(r'<[^>]+>', '', item)  # Remove HTML tags
            cleaned_data.append(cleaned_item.strip())  # Remove leading/trailing whitespace
        return cleaned_data

    def extract_currency_from_code(self, formatted_price):
        return self.CURRENCY_SYMBOL_TO_CODE.get(re.search(r'([^\d.,])', formatted_price).group(1))


    def parse(self, response):
        jdata = self.extract_jdata(response)

        products_data = self.products_jp.search(jdata['__PRELOADED_QUERIES__'])

        description_jmespath = "__PRELOADED_QUERIES__.queries[0][1].data.metadata.seo_data.seo_description"
        description = jmespath.search(description_jmespath, jdata)


        for product_data in products_data:
            item = SyntargetItem()  
            item['url']  = product_data.get('url')
            tcin = product_data.get('tcin')
            item['tcin'] = tcin
            item['upc']  = product_data.get('upc')
            if product_data.get('regular_price'):
                item['price_amount'] = product_data.get('regular_price')
            else:
                item['price_amount'] = product_data.get('current_price')
            formatted_price  = product_data.get('currency_symbol')
            item['currency'] = self.extract_currency_from_code(formatted_price)
            item['description'] = description
            item['specs']   =  product_data.get('specs')
            item['ingredients'] = product_data.get('ingredients')
            item['bullets'] = product_data.get('bullets')
            item['features'] = self.clean_data(product_data.get('features'))
            item['name'] = product_data.get('title')
            yield self.get_question_request(tcin, item)

    def get_question_request(self, id, item, page=0): 

        question_url = ("https://r2d2.target.com/ggc/Q&A/v1/question-answer?"
               "key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
               f"&page={page}&questionedId={id}"
               "&type=product&size=10&sortBy=MOST_ANSWERS"
        )
        return Request(
            url=question_url,
            headers = self.HEADER_LIST, 
            callback=self.parse_questions,
            dont_filter=True,
            cb_kwargs={"id":id, "item":item}
            )

    def parse_questions(self, response, id, item):
        try:
            qdata = json.loads(response.text)
            logging.debug("Response URL: %s", response.url)
            logging.debug("Parsed JSON Data: %s", qdata)

        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON: %s", e)
            logging.debug("Response Content: %s", response.text)

        questions_data = self.questions_jp.search(qdata)

        if 'questions' not in item.keys():
            item['questions'] = []
        
        for question in questions_data:
            submission_date_question = question.get("submission_date")
            formatted_date_question = self.format_submission_date(submission_date_question)
            question["submission_date"] = formatted_date_question

            answers = question.get("answers", [])
            for answer in answers:
                submission_date_answer = answer.get("submission_date")
                formatted_date_answer = self.format_submission_date(submission_date_answer)
                answer["submission_date"] = formatted_date_answer
            
        item['questions'].extend(questions_data)

        # Request Next Page
        page = qdata["page"]
        total_pages = qdata["total_pages"]
        if page < total_pages:
            yield self.get_question_request(id, item, page + 1)
        else:
            yield item

    def format_submission_date(self, submission_date):
        try:
            date_obj = datetime.strptime(submission_date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            return formatted_date
        except ValueError:
            return None
