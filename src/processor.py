from src.const import *
from src.utils import (call_pro_con_endpoint, call_restaurant_pro_con_endpoint)


def get_url_from_product_map(product: str):
    prod_map = {
        'Books': [PROD_BOOK_URL_1, PROD_BOOK_URL_2],
        'Binoculars': [PROD_BINOCULARS_URL_1, PROD_BINOCULARS_URL_2],
        'Sneakers': [PROD_SNEAKERS_URL_1, PROD_SNEAKERS_URL_2],
    }
    if product in prod_map:
        return prod_map[product][0], prod_map[product][1]
    return ''


def extract_pro_con(url: str):
    # Call the service endpoint
    prod_data = call_pro_con_endpoint(prod_url=url)
    return prod_data


def extract_restaurant_pro_con(restaurant_name: str):
    # Call the service endpoint
    res_data = call_restaurant_pro_con_endpoint(restaurant_name=restaurant_name)
    return res_data
