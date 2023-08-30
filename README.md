## syntarget
- Run the spider with this cmd scrapy crawl target_com -a url=https://www.target.com/p/-/A-79344798
- If you want the output in a json file for testing purpose append -o <filename>.json with the above cmd e.g: "scrapy crawl target_com -a url=https://www.target.com/p/-/A-79344798 -o target_data.json"
- To install dependencies requirements.txt file is added.
##To run the project 
    - Create a python3 virtualenv: virtualenv -p python3 <env_name>
    - Install requirements file: pip install -r requirements.txt

##Assumptions:
    - specs: This filed is assumed to be the field present on website as Specifications.

- A JSON file is also attached target_data.json which contains the data of three URLs given as examples.
