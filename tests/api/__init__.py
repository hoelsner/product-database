from tests.base.rest_calls import *


def drop_all_products(server, username, password):
    """
    drop all products from the given server using the REST API
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


def get_vendor_id_by_name(server, vendor_name, username, password):
    """
    convert the vendor name to an ID using the REST API
    """
    vendors_api = server + VENDORS_API_ENDPOINT

    response = get_rest_call(
        vendors_api + "?name=" + vendor_name.replace(" ", "%20"),
        username, password
    )
    if response.status_code != 200:
        raise Exception("Failed to get vendor name '%s'\n%s" % (vendor_name,
                                                                response.content.decode("utf-8")))
    vendor = json.loads(response.content.decode("utf-8"))
    if len(vendor["data"]) == 0:
        raise Exception("Failed to get vendor name '%s', "
                        "entry not found\n%s" % (vendor_name,
                                                 response.content.decode("utf-8")))

    return vendor["data"][0]['id']


def get_product_group_id_by_name(server, product_group_name, username, password):
    """
    convert the product group name to an ID using the REST API
    """
    product_groups_api = server + PRODUCT_GROUPS_API_ENDPOINT

    response = get_rest_call(
        product_groups_api + "?name=" + product_group_name.replace(" ", "%20"),
        username, password
    )
    if response.status_code != 200:
        raise Exception("Failed to get product group name '%s'\n%s" % (product_group_name,
                                                                       response.content.decode("utf-8")))
    product_group = json.loads(response.content.decode("utf-8"))
    if len(product_group["data"]) == 0:
        raise Exception("Failed to get product group name '%s', "
                        "entry not found\n%s" % (product_group_name,
                                                 response.content.decode("utf-8")))

    return product_group["data"][0]['id']


def create_real_test_data(server, username, password, test_data_paths=None):
    """
    create real test data on the given server using the json files located in the test_data directory
    :param test_data_paths:
    :param server:
    :param username:
    :param password:
    :return:
    """
    products_api = server + PRODUCTS_API_ENDPOINT
    product_groups_api = server + PRODUCT_GROUPS_API_ENDPOINT
    vendors_api = server + VENDORS_API_ENDPOINT

    if test_data_paths is None:
        test_data_paths = [
            "tests/data/create_cisco_test_data.json",
            "tests/data/create_juniper_test_data.json",
        ]

    #
    # create elements
    #
    for test_data_file in test_data_paths:
        # load data
        data = json.loads(open(test_data_file, "r").read())

        # create product groups
        if "product_groups" in data.keys():
            for product_group_dict in data["product_groups"]:
                # translate vendor object
                product_group_dict['vendor'] = get_vendor_id_by_name(
                    server,
                    product_group_dict['vendor'],
                    username,
                    password
                )
                response = post_rest_call(product_groups_api,
                                          product_group_dict,
                                          username,
                                          password)
                if response.status_code != 201:
                    exists = "The fields name, vendor must make a unique set." in response.content.decode("utf-8")
                    if not exists:
                        raise Exception("Failed to create product group '%s'\n%s" % (product_group_dict['name'],
                                                                                     response.content.decode("utf-8")))

        # create products from file
        if "products" in data.keys():
            for product_dict in data['products']:
                # translate vendor object
                response = get_rest_call(
                    vendors_api + "?name=" + product_dict['vendor'].replace(" ", "%20"),
                    username, password
                )
                if response.status_code != 200:
                    raise Exception("Failed to get vendor name '%s'\n%s" % (product_dict['vendor'],
                                                                            response.content.decode("utf-8")))
                vendor = json.loads(response.content.decode("utf-8"))
                if len(vendor["data"]) == 0:
                    raise Exception("Failed to get vendor name '%s', "
                                    "entry not found\n%s" % (product_dict['vendor'],
                                                             response.content.decode("utf-8")))

                product_dict['vendor'] = vendor["data"][0]['id']

                # check for product group
                if "product_group" in product_dict.keys():
                    product_dict["product_group"] = get_product_group_id_by_name(
                        server,
                        product_dict["product_group"],
                        username,
                        password
                    )

                response = post_rest_call(products_api,
                                          product_dict,
                                          username,
                                          password)
                if response.status_code != 201:
                    exists = "Product with this product id already exists." in response.content.decode("utf-8")
                    if not exists:
                        raise Exception("Failed to create product '%s'\n%s" % (product_dict['product_id'],
                                                                               response.content.decode("utf-8")))
