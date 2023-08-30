# Target.com Spider

This Scrapy spider is designed to scrape product data from www.target.com.

## Running the Spider

To run the spider, use the following command:
scrapy crawl target_com -a url=https://www.target.com/p/-/A-79344798

If you want the output in a JSON file for testing purposes, append `-o .json` to the above command:
scrapy crawl target_com -a url=https://www.target.com/p/-/A-79344798 -o target_data.json

## Installation

1. Create a Python 3 virtual environment:
virtualenv -p python3 <env_name>

2. Install the required dependencies from the `requirements.txt` file:
pip install -r requirements.txt

## Assumptions
- `specs`: This field is assumed to be the field present on the website as "Specifications".
## Example Data
A JSON file `target_data.json` is provided, which contains data from three example URLs.
