"""
All test that don't require an internet connection
"""
from .test_model.test_model import *
from .test_model.test_model_signals import *
from .test_api_endpoints.test_product_api import *
from .test_api_endpoints.test_product_list_api import *
from .test_api_endpoints.test_vendor_api import *
from .test_api_endpoints.test_api_interaction import *
from .test_datatables_api import *
from .test_celery_task_creation import *
from .test_crawler.test_cisco_eox_crawler import *
from .test_excel_import import *
from .test_backup import *
