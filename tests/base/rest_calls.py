import json
import requests
from requests.auth import HTTPBasicAuth

#
# API endpoints for tests
#
PRODUCTS_API_ENDPOINT = "/productdb/api/v0/products/"
VENDORS_API_ENDPOINT = "/productdb/api/v0/vendors/"


#
# REST calls
#
def get_rest_call(api_url, username, password):
    """
    get call against REST API to test the API interface of the Product DB

    :param api_url:
    :param username:
    :param password:
    :return:
    """
    response = requests.get(api_url,
                            auth=HTTPBasicAuth(username, password),
                            verify=False,
                            timeout=4)
    return response


def post_rest_call(api_url, data_dict, username, password, print_output=False):
    """
    post call against REST API to test the API interface of the Product DB

    :param api_url:
    :param data_dict:
    :param username:
    :param password:
    :param print_output:
    :return:
    """
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(api_url,
                             auth=HTTPBasicAuth(username, password),
                             data=json.dumps(data_dict),
                             headers=headers,
                             verify=False,
                             timeout=4)

    if print_output:
        if response.status_code == 201:
            print("POST   OK %s (code %d)" % (api_url, response.status_code))
        elif response.status_code == 200:
            print("POST   OK %s (code %d)" % (api_url, response.status_code))
        elif response.status_code == 204:
            print("POST   OK %s (code %d)" % (api_url, response.status_code))
        else:
            print("POST   Failed for: %s (code %d)" % (api_url, response.status_code))
            print(" - Data: %s" % json.dumps(data_dict))
            print(" - Text: %s" % response.text)
    return response


def put_rest_call(api_url, data_dict, username, password, print_output=False):
    """
    put call against REST API to test the API interface of the Product DB

    :param api_url:
    :param data_dict:
    :param username:
    :param password:
    :param print_output:
    :return:
    """
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.put(api_url,
                            auth=HTTPBasicAuth(username, password),
                            data=json.dumps(data_dict),
                            headers=headers,
                            verify=False,
                            timeout=4)

    if print_output:
        if response.status_code == 201:
            print("PUT    OK %s (code %d)" % (api_url, response.status_code))
        elif response.status_code == 200:
            print("PUT    OK %s (code %d)" % (api_url, response.status_code))
        elif response.status_code == 204:
            print("PUT    OK %s (code %d)" % (api_url, response.status_code))
        else:
            print("PUT    Failed for: %s (code %d)" % (api_url, response.status_code))
            print(" - Data: %s" % json.dumps(data_dict))
            print(" - Text: %s" % response.text)
    return response


def delete_rest_call(api_url, username, password, print_output=False):
    """
    delete call against REST API to test the API interface of the Product DB

    :param api_url:
    :param username:
    :param password:
    :param print_output:
    :return:
    """
    response = requests.delete(api_url,
                               auth=HTTPBasicAuth(username, password),
                               verify=False,
                               timeout=4)

    if print_output:
        if response.status_code == 201:
            print("DELETE OK %s (code %d)" % (api_url, response.status_code))
        elif response.status_code == 200:
            print("DELETE OK %s (code %d)" % (api_url, response.status_code))
        elif response.status_code == 204:
            print("DELETE OK %s (code %d)" % (api_url, response.status_code))
        else:
            print("DELETE Failed for: %s (code %d)" % (api_url, response.status_code))
            print(" - Text: %s" % response.text)
    return response
