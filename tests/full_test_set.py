"""

Test-Set for the entire application (including all Unit-Tests (Online and Offline) and Functional Tests
(will destruct the entire database on the target machine when using the liveserver parameter)

"""
from app.productdb.tests.all_tests import *
from tests.functional_tests.all_offline_fts import *
from tests.functional_tests.all_online_fts import *
