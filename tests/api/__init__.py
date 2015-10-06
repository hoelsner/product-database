from tests.base.rest_calls import *
import sys


def drop_all_product_lists(server, username, password):
    """
    drop all product lists from the given server
    :param server:
    :param username:
    :param password:
    :return:
    """
    product_lists_api = server + PRODUCT_LISTS_API_ENDPOINT

    result = []
    pages = 1
    current_page = 1

    while current_page <= pages:
        response = get_rest_call(product_lists_api + "?page=%d" % current_page, username, password)

        json_data = json.loads(response.content.decode("utf-8"))
        pages = int(json_data['pagination']['last_page'])
        result += json_data['data']
        current_page += 1

    for elem in result:
        urlcall = "%s%s/" % (product_lists_api, elem['id'])
        delete_rest_call(urlcall, username, password)


def drop_all_products(server, username, password):
    """
    drop all products from the given server
    :param server:
    :param username:
    :param password:
    :return:
    """
    products_api = server + PRODUCTS_API_ENDPOINT

    result = []
    pages = 1
    current_page = 1

    while current_page <= pages:
        response = get_rest_call(products_api + "?page=%d" % current_page, username, password)

        json_data = json.loads(response.content.decode("utf-8"))
        pages = int(json_data['pagination']['last_page'])
        result += json_data['data']
        current_page += 1

    for elem in result:
        urlcall = "%s%s/" % (products_api, elem['id'])
        delete_rest_call(urlcall, username, password)


def create_real_test_data(server, username, password, test_data_paths=None):
    """
    create real test data on the given server using the json files located in the test_data directory
    :param server:
    :param username:
    :param password:
    :return:
    """
    products_api = server + PRODUCTS_API_ENDPOINT
    product_list_api = server + PRODUCT_LISTS_API_ENDPOINT
    vendors_api = server + VENDORS_API_ENDPOINT

    if test_data_paths is None:
        test_data_paths = [
            "tests/data/create_cisco_test_data.json",
            "tests/data/create_juniper_test_data.json",
        ]

    products = {}
    product_lists = {}

    #
    # create elements
    #
    for test_data_file in test_data_paths:
        # load data
        data = json.loads(open(test_data_file, "r").read())
        # create product_lists from file
        if "product_lists" in data.keys():
            for product_list_dict in data['product_lists']:
                response = post_rest_call(product_list_api,
                                          product_list_dict,
                                          username,
                                          password)
                if response.status_code != 201:
                    exists = "This field must be unique." in response.content.decode("utf-8")
                    if not exists:
                        raise Exception("Failed to create product_list '%s'\n%s" % (product_list_dict['product_list_name'],
                                                                                    response.content.decode("utf-8")))
                    else:
                        break
                product_lists[product_list_dict['product_list_name']] = json.loads(response.content.decode("utf-8"))

        # create products from file
        if "products" in data.keys():
            for product_dict in data['products']:
                # translate Vendor Object
                response = post_rest_call(vendors_api + "byname/", {"name": product_dict['vendor']}, username, password)
                if response.status_code != 200:
                    raise Exception("Failed to get vendor name '%s'\n%s" % (product_dict['vendor'],
                                                                            response.content.decode("utf-8")))
                vendor = json.loads(response.content.decode("utf-8"))
                product_dict['vendor'] = vendor['id']

                response = post_rest_call(products_api,
                                          product_dict,
                                          username,
                                          password)
                if response.status_code != 201:
                    exists = "This field must be unique." in response.content.decode("utf-8")
                    if not exists:
                        raise Exception("Failed to create product '%s'\n%s" % (product_dict['product_id'],
                                                                               response.content.decode("utf-8")))
                    else:
                        break
                products[product_dict['product_id']] = json.loads(response.content.decode("utf-8"))
                for product_list_name in product_dict['lists']:
                    product_lists[product_list_name]['products'].append(products[product_dict['product_id']]['id'])

        # associate products to product list
        for product_list_name in product_lists:
            response = put_rest_call(product_list_api + "%d/" % product_lists[product_list_name]['id'],
                                     product_lists[product_list_name],
                                     username,
                                     password)
            if response.status_code != 200:
                raise Exception("Failed to associate product_list '%s'\n%s" % (product_list_name,
                                                                               response.content.decode("utf-8")))
