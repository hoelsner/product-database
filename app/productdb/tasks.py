from django_project.celery import app as app
from app.productdb.models import Settings
import app.productdb.crawler.cisco_eox_api_crawler as cisco_eox_api_crawler
import logging


logger = logging.getLogger(__name__)


@app.task(serializer='json', name="synchronize_with_cisco_eox_api")
def execute_task_to_synchronize_cisco_eox_states():
    """
    This task will automatically synchronize the Cisco EoX states with the local database. It will execute the
    configured queries and saves the information to the local database. There are two types of operation:
      * cisco_eox_api_auto_sync_auto_create_elements is set to true - will create any element which is not part of the blacklist and not in the
                                              database
      * cisco_eox_api_auto_sync_auto_create_elements is set to false - will only update entries, which are already included in the database

    :return:
    """
    logger.info("execute synchronize Cisco EoX update task...")
    # update based on the configured query settings
    result = cisco_eox_api_crawler.synchronize_with_cisco_eox_api()
    logger.info("result: %s" % str(result))
    s = Settings.objects.get(id=1)
    s.eox_api_sync_task_id = ""
    s.save()
    return result
