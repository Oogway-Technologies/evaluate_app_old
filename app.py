import pandas as pd
import streamlit as st
from src.const import (CACHED_PRODUCTS_LIST, CACHED_RESTAURANT_LIST)
from src.processor import (extract_pro_con, extract_restaurant_pro_con, get_url_from_product_map)
from src.utils import (average, is_inverted_pro_con, validate_url)

# App title
st.title("Evaluate")

# Search bars are always at the top of the page after the title    # Add the search boxes
input_url_1 = st.text_input("Product 1", key="url_1")
input_url_2 = st.text_input("Product 2", key="url_2")
input_restaurant = ""


def prepare_layout():
    global input_url_1
    global input_url_2

    st.sidebar.markdown("### Pro-Con Evaluation")
    st.sidebar.markdown("This evaluation engine performs sentiment analysis and extract pros and cons for "
                        "[Amazon](https://www.amazon.com/) products.")
    st.sidebar.markdown('#### Instructions:')
    instructions = """
    1. Select a product on the drop-down box below to review a list of pros-cons comparing two similar products
       on Amazon; OR
    2. Use the search boxes to paste the URL of two Amazon products and calculate pros-cons on-the-fly (
       this can take some time):
        * [https://www.amazon.com/Celestron-71198-Cometron...](https://www.amazon.com/Celestron-71198-Cometron-Binoculars-Black/dp/B00DV6SI3Q?ref_=Oct_DLandingS_D_1318bab5_61&smid=ATVPDKIKX0DER&th=1)
        * [https://www.amazon.com/SWAROVSKI-10x42-NL-Pure-...](https://www.amazon.com/SWAROVSKI-10x42-NL-Pure-Binoculars/dp/B08HP9LMQ8/ref=sr_1_77?crid=251XT9ZSI48AU&keywords=binoculars&qid=1639191462&refinements=p_72%3A1248882011&rnid=1248877011&s=electronics&sprefix=bino%2Celectronics%2C184&sr=1-77&th=1)
    """
    st.sidebar.markdown(instructions)
    selected = st.sidebar.selectbox('Products:', CACHED_PRODUCTS_LIST,
                                    format_func=lambda x: 'Select a product' if x == '' else x)
    if selected:
        curr_url_1, curr_url_2 = get_url_from_product_map(selected)

        # Reset restaurant, if any
        # input_restaurant = ""

        input_url_1 = curr_url_1
        input_url_2 = curr_url_2
    with st.sidebar.expander('Want more?'):
        st.write("Evaluation is the step in which you can compare options to make an informed decision."
                 "It is not strictly related to consumer products. In fact, all options generated during "
                 "the search and filter step should be evaluated to pick the one that is best for you.")
        st.write("For example, let's assume you are going out for a fancy dinner where you want to impress your "
                 "partner, friend, or family. You have a list of few restaurants in mind. Wouldn't it be great if "
                 "you had an easy way to compare those restaurants and pick the one that you find more interesting?")
        selected_restaurant = st.selectbox('Restaurant:', CACHED_RESTAURANT_LIST,
                                           format_func=lambda x: 'Select a restaurant' if x == '' else x)
        st.markdown("**Note**: to display Amazon products reset the restaurant choice to the default "
                    "'Select a restaurant'")
        if selected_restaurant:
            global input_restaurant

            # Reset product cards, if any
            input_url_1 = ""
            input_url_2 = ""
            input_restaurant = selected_restaurant


def build_restaurant_card(card_meta):
    """
    Build a restaurant Card.
    :param card_meta: the Card MetaData.
    :return: None
    """
    st.markdown("#### " + card_meta['name'])

    # Print MetaData
    meta_data = card_meta["meta"]
    st.markdown("Price:    " + str(meta_data['price']))
    st.markdown("Reviews:  " + str(meta_data['num_reviews']))
    st.markdown("Rating:   " + str(meta_data['rating']))
    st.markdown("Sentiment:")
    sent = card_meta['sentiment_map']
    best_key = ""
    best_avg = 0
    for key, val in sent.items():
        avg_val = average(val)
        if avg_val > best_avg:
            best_avg = avg_val
            best_key = key
    best_key = int(best_key.split()[0].strip())
    st.progress(1 / 5 * best_key)
    st.markdown("[Link to restaurant]" + "(" + meta_data['url'] + ")")
    with st.expander("Summary Reviews"):
        st.write(card_meta['summary'])
    with st.expander("Positive and Critical review"):
        st.markdown("##### Top positive review")
        st.write("Rating: " + str(card_meta['best_review'][0]))
        st.write(card_meta['best_review'][1])
        st.markdown("##### Top critical review")
        if card_meta['worst_review'][0] > 4:
            st.markdown("**All reviews seem to be positive!**")
        st.write("Rating: " + str(card_meta['worst_review'][0]))
        st.write(card_meta['worst_review'][1])
    with st.expander("Restaurant Overview"):
        for key, val in card_meta["category_map"].items():
            if val["num_entries"] > 0:
                if key == 'other':
                    # Skip other
                    continue
                st.markdown("**" + key.title() + "**")
                if val["perc"] == 0:
                    st.progress(0.01)
                else:
                    st.progress(val["perc"] / 100)
    with st.expander("Pros and Cons"):
        # Note: some pros/cons need to be manually checked and inverted.
        # For example: price
        pro_con_table = dict()
        pro_con_table["Pros"] = list()
        pro_con_table["Cons"] = list()
        for val in card_meta["gen_pro_con_map"]["pos"]:
            if is_inverted_pro_con(val, is_pos=True):
                pro_con_table["Cons"].append(val)
            else:
                pro_con_table["Pros"].append(val)
        for val in card_meta["gen_pro_con_map"]["neg"]:
            if is_inverted_pro_con(val, is_pos=False):
                pro_con_table["Pros"].append(val)
            else:
                pro_con_table["Cons"].append(val)
        num_elements = max(len(pro_con_table["Pros"]), len(pro_con_table["Cons"]))
        for _ in range(len(pro_con_table["Pros"]), num_elements):
            pro_con_table["Pros"].append("")
        for _ in range(len(pro_con_table["Cons"]), num_elements):
            pro_con_table["Cons"].append("")
        df = pd.DataFrame(pro_con_table)
        st.table(df)


def build_prod_card(card_meta, url):
    """
    Build a product Card.
    :param card_meta: the Card MetaData.
    :param url: the URL of the Amazon product.
    :return: None
    """
    meta = card_meta['meta']
    st.markdown("#### " + meta['title'])
    col1, col2 = st.columns(2)
    with col1:
        image_url = meta['image']
        st.image(
            image_url,
            width=250,
        )
    with col2:
        st.markdown("Price:    " + meta['price'])
        st.markdown("Reviews:  " + meta['glb_num_ratings'])
        st.markdown("Rating:   " + str(meta['glb_rating']))
        st.markdown("Sentiment:")
        sent = card_meta['sentiment_map']
        best_key = ""
        best_avg = 0
        for key, val in sent.items():
            avg_val = average(val)
            if avg_val > best_avg:
                best_avg = avg_val
                best_key = key
        best_key = int(best_key.split()[0].strip())
        st.progress(1/5 * best_key)
        st.markdown("[Link to product]" + "(" + url + ")")
    with st.expander("Summary Reviews"):
        st.markdown("##### " + card_meta['title'])
        st.write(card_meta['summary'])
    with st.expander("Positive and Critical review"):
        st.markdown("##### Top positive review")
        st.write("Rating: " + str(card_meta['best_review'][0]))
        st.write(card_meta['best_review'][1])
        st.markdown("##### Top critical review")
        if card_meta['worst_review'][0] > 4:
            st.markdown("**All reviews seem to be positive!**")
        st.write("Rating: " + str(card_meta['worst_review'][0]))
        st.write(card_meta['worst_review'][1])
    with st.expander("Product Overview"):
        for key, val in card_meta["category_map"].items():
            if val["num_entries"] > 0:
                st.markdown("**" + key.title() + "**")
                if key == 'price':
                    val["perc"] = 100 - val["perc"]
                if val["perc"] == 0:
                    st.progress(0.01)
                else:
                    st.progress(val["perc"] / 100)
    with st.expander("Pros and Cons"):
        # Note: some pros/cons need to be manually checked and inverted.
        # For example: price
        pro_con_table = dict()
        pro_con_table["Pros"] = list()
        pro_con_table["Cons"] = list()
        for val in card_meta["gen_pro_con_map"]["pos"]:
            if is_inverted_pro_con(val, is_pos=True):
                pro_con_table["Cons"].append(val)
            else:
                pro_con_table["Pros"].append(val)
        for val in card_meta["gen_pro_con_map"]["neg"]:
            if is_inverted_pro_con(val, is_pos=False):
                pro_con_table["Pros"].append(val)
            else:
                pro_con_table["Cons"].append(val)
        num_elements = max(len(pro_con_table["Pros"]), len(pro_con_table["Cons"]))
        for _ in range(len(pro_con_table["Pros"]), num_elements):
            pro_con_table["Pros"].append("")
        for _ in range(len(pro_con_table["Cons"]), num_elements):
            pro_con_table["Cons"].append("")
        df = pd.DataFrame(pro_con_table)
        st.table(df)


def run_code(url1: str, url2: str):
    """
    Runs the pro-con service to extract pros and cons
    and displays information.
    :param url1: the url of the first Amazon product.
    :param url2: the url of the second Amazon product.
    :return: None
    """
    # Validate URLs
    if not validate_url(url1) or not validate_url(url2):
        st.error('Not a valid Amazon URL')
        return

    # If everything is okay, run the service
    with st.spinner('Analyzing data...'):
        review_card_1 = extract_pro_con(url=url1)
        review_card_2 = extract_pro_con(url=url2)

        # Now build the cards for the products
        st.markdown("***")
        build_prod_card(review_card_1, url=url1)
        st.markdown("***")
        build_prod_card(review_card_2, url=url2)


def run_restaurant_code(restaurant_name: str):
    """
    Runs the pro-con service to extract pros and cons
    and displays information.
    :param restaurant_name: name of the restaurant
    :return: None
    """
    # Retrieve restaurant MetaData
    restaurant_meta = extract_restaurant_pro_con(restaurant_name=restaurant_name)

    # Print restaurant Card
    build_restaurant_card(restaurant_meta)


def run():
    # Empty URLs are okay
    if (not input_url_1 or not input_url_2) and (not input_restaurant):
        return

    # Products take priority
    if input_url_1 and input_url_2:
        # Just run the code
        run_code(input_url_1, input_url_2)
    elif input_restaurant:
        # Just run the restaurant code
        run_restaurant_code(input_restaurant)


if __name__ == "__main__":
    # Prepare layout
    prepare_layout()

    # Run the app
    run()
