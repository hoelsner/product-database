"""
Functions to test the API interface

These functions are used to create and remove test data during the execution of the unit tests for the API endpoints.
"""
import json
from requests.auth import HTTPBasicAuth

import app.productdb.tests.base.api_endpoints as apiurl


def create_product(client, product_name, username, password):
    url = apiurl.PRODUCT_API_ENDPOINT
    product_api_call = {
        "product_id": product_name
    }
    response = client.post(url, product_api_call, auth=HTTPBasicAuth(username, password), format='json')
    if response.status_code != 201:
        raise Exception("Fail to create product: %s\n"
                        "URL/Code: %s/%s\n"
                        "Response content: %s" % (json.dumps(product_api_call, indent=4),
                                                  url,
                                                  response.status_code,
                                                  response.content))
    return json.loads(response.content.decode("utf-8"))


def get_product_by_name(client, product_name, username, password):
    url = apiurl.PRODUCT_API_ENDPOINT + "?product_id=" + product_name
    response = client.get(url, auth=HTTPBasicAuth(username, password), format='json')

    if response.status_code != 200:
        raise Exception("Fail to get product by name:\n"
                        "URL/Code: %s/%s\n"
                        "Response content: %s" % (url,
                                                  response.status_code,
                                                  response.content))
    result = json.loads(response.content.decode("utf-8"))["data"]
    if len(result) == 0:
        raise Exception("Query returned no results:\n"
                        "URL/Code: %s/%s\n"
                        "Response content: %s" % (url,
                                                  response.status_code,
                                                  response.content))
    return result[0]


def get_products(client, username, password):
    url = apiurl.PRODUCT_API_ENDPOINT

    result = []
    pages = 1
    current_page = 1

    while current_page <= pages:
        response = client.get(url + "?page=%d" % current_page, auth=HTTPBasicAuth(username, password), format='json')

        if response.status_code != 200:
            raise Exception("Fail to get all product: ---\n"
                            "URL/Code: %s/%s\n"
                            "Response content: %s" % (url,
                                                      response.status_code,
                                                      response.content))

        json_data = json.loads(response.content.decode("utf-8"))
        pages = int(json_data['pagination']['last_page'])
        result += json_data['data']
        current_page += 1

    return result


def update_product(client, product_dict, username, password):
    url = apiurl.PRODUCT_DETAIL_API_ENDPOINT % product_dict['id']
    response = client.put(url, product_dict, auth=HTTPBasicAuth(username, password), format='json')

    if response.status_code != 200:
        raise Exception("Fail to put product: %s\n"
                        "URL/Code: %s/%s\n"
                        "Response content: %s" % (json.dumps(product_dict, indent=4),
                                                  url,
                                                  response.status_code,
                                                  response.content))
    return json.loads(response.content.decode("utf-8"))


def delete_product(client, product_name, username, password):
    product = get_product_by_name(client, product_name, username=username, password=password)
    url = apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id']
    response = client.delete(url, auth=HTTPBasicAuth(username, password))

    if response.status_code != 204:
        raise Exception("Fail to delete product: %s\n"
                        "URL/Code: %s/%s\n"
                        "Response content: %s" % (json.dumps(product, indent=4),
                                                  url,
                                                  response.status_code,
                                                  response.content))


def clean_db(client, username, password):
    """
    Remove all elements from the models that is available using the API
    :param client:
    :return:
    """
    products = get_products(client, username=username, password=password)

    for product in products:
        delete_product(client, product['product_id'], username=username, password=password)


def result_contains_error(api_test_case, error_msg, json_key, content):
    """
    verifies that the given error message is product of the given JSON content

    :param api_test_case:
    :param json_key:
    :param error_msg:
    :param content:
    :return:
    """
    json_results = json.loads(content)
    if json_key in json_results.keys():
        found = False
        if type(json_results[json_key]) is list:
            for msg in json_results[json_key]:
                if error_msg in msg:
                    found = True
                    break
        else:
            if error_msg in json_results[json_key]:
                found = True

        if found:
            return True
        else:
            api_test_case.fail("Invalid response, key '%s' not found, content\n%s" % (json_key, content))
    else:
        api_test_case.fail("Invalid response, key '%s' not found, content\n%s" % (json_key, content))