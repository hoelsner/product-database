"""

All Functional Tests, which require no internet connection
(will destruct the entire database on the target machine when using the liveserver parameter)

"""
from tests.functional_tests.api.test_api_interaction import *
from tests.functional_tests.api.test_swagger_interface import *

from tests.functional_tests.complete_use_case.test_bulk_eol_check import *

from tests.functional_tests.productdb_views.test_browse_products_by_product_list import *
from tests.functional_tests.productdb_views.test_browse_products_by_vendor import *
from tests.functional_tests.productdb_views.test_views_with_empty_db import *
from tests.functional_tests.productdb_views.test_home_page import *
from tests.functional_tests.productdb_views.test_lifecycle_view_by_vendor import *

from tests.functional_tests.settings_tests.test_cisco_api_settings_view import *
from tests.functional_tests.settings_tests.test_settings_permissions import *
