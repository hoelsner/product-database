import logging
from app.ciscoeox.base_api import CiscoHelloApi, CiscoEoxApi
from django_project import celery

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

    except Exception as ex:
        logging.error("Cisco Hello API test access failed (%s)" % ex, exc_info=True)
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

        base_api.query_product("WS-C2960-24T*")

        return True

    except Exception as ex:
        logging.error("Cisco EoX API test access failed (%s)" % ex, exc_info=True)
        return False


def get_celery_worker_state_html():
    state = celery.is_worker_active()
    if state:
        worker_status = """
            <div class="alert alert-success" role="alert">
                <span class="fa fa-info-circle"></span>
                Backend worker found.
            </div>"""

    else:
        worker_status = """
            <div class="alert alert-danger" role="alert">
                <span class="fa fa-exclamation-circle"></span>
                No backend worker found, asynchronous and scheduled tasks are not executed.
            </div>"""

    return worker_status
