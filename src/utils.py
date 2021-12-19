import json
import requests
import spacy
from src.const import *
from urllib.parse import urlparse


utils_nlp = spacy.load('en_core_web_md')


def average(lst):
    return sum(lst) / len(lst)


def validate_url(url: str):
    url_obj = urlparse(url)
    prefix = url_obj.scheme + '://' + url_obj.netloc
    if prefix != AMAZON_BASE_URL:
        return False
    if '/dp/' not in url_obj.path:
        return False
    return True


def call_pro_con_endpoint(prod_url: str) -> dict:
    url = PRO_CON_ENDPOINT + PRO_CON_KEY
    payload = json.dumps({
        "url": prod_url
    })
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except:
        return {}

    if response.status_code != 200:
        return {}

    return json.loads(response.text)


def calculate_similarity(text1, text2):
    base = utils_nlp(text1)
    compare = utils_nlp(text2)
    return base.similarity(compare)


def is_inverted_pro_con(pro_con: str, is_pos: bool) -> bool:
    low_price_tags = ["low price", "low cost", "low payment",
                      "little price", "little cost", "little payment"]
    high_price_tags = ["high price", "high cost", "high payment",
                       "big price", "big cost", "big payment"]
    if not is_pos:
        for tag in low_price_tags:
            if calculate_similarity(tag, pro_con) > 0.9:
                # It is an inverted pro-con
                return True
    if is_pos:
        for tag in high_price_tags:
            if calculate_similarity(tag, pro_con) > 0.9:
                # It is an inverted pro-con
                return True
    return False


def call_restaurant_pro_con_endpoint(restaurant_name: str) -> dict:
    url = PRO_CON_RESTAURANT_ENDPOINT + PRO_CON_KEY
    payload = json.dumps({
        "restaurant_name": restaurant_name,
        "city": "Boston",
        "max_num_reviews": PRO_CON_RESTAURANT_NUM_REVIEWS
    })
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except:
        return {}

    if response.status_code != 200:
        return {}

    return json.loads(response.text)
