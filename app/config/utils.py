from app.ciscoeox.base_api import CiscoHelloApi, CiscoEoxApi

CISCO_EOX_API_TASK_NAME = "Cisco EoX API crawler"


def check_cisco_hello_api_access(client_id, client_secret, drop_credentials=True):
    """
    test the Cisco Hello API access
    """
    try:
        base_api = CiscoHelloApi()
        base_api.load_client_credentials()

        if drop_credentials:
            base_api.drop_cached_token()

        base_api.client_id = client_id
        base_api.client_secret = client_secret

        base_api.hello_api_call()

        return True

    except:
        return False


def check_cisco_eox_api_access(client_id, client_secret, drop_credentials=True):
    """
    test the Cisco EoX V5 API access
    """
    try:
        base_api = CiscoEoxApi()
        base_api.load_client_credentials()

        if drop_credentials:
            base_api.drop_cached_token()

        base_api.client_id = client_id
        base_api.client_secret = client_secret

        base_api.query_product("WS-C2960-24T")

        return True

    except Exception as ex:
        return False
