import logging

import app.ciscoeox.api_crawler as cisco_eox_api_crawler
from app.config import AppSettings
from django_project.celery import app as app

logger = logging.getLogger(__name__)


@app.task(serializer='json', name="synchronize_with_cisco_eox_api")
def execute_task_to_synchronize_cisco_eox_states():
    """
    This task synchronize the local database with the Cisco EoX API. It executes all configured queries and stores the
    results in the local database. There are two types of operation:
      * cisco_eox_api_auto_sync_auto_create_elements is set to true - will create any element which is not part of the
                                                                      blacklist and not in the database
      * cisco_eox_api_auto_sync_auto_create_elements is set to false - will only update entries, which are already
                                                                       included in the database

    :return:
    """
    logger.info("start sync with Cisco EoX API...")

    # update the local database based on the Cisco API
    result = cisco_eox_api_crawler.synchronize_with_cisco_eox_api()
    logger.info("result: %s" % str(result))

    # clean task from configuration
    app_config = AppSettings()
    app_config.read_file()
    app_config.set(value="", key="eox_api_sync_task_id", section=AppSettings.CISCO_EOX_CRAWLER_SECTION)

    return result
