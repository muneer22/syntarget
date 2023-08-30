# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SyntargetItem(scrapy.Item):
    url = scrapy.Field()
    tcin = scrapy.Field()
    upc = scrapy.Field()
    price_amount = scrapy.Field()
    currency = scrapy.Field()
    description = scrapy.Field()
    specs = scrapy.Field()
    ingredients = scrapy.Field()
    bullets = scrapy.Field()
    features = scrapy.Field()
    questions = scrapy.Field()
