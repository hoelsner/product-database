"""

All functional tests, which can also be used to test an instance on another server
(will destruct the entire database on the target machine when using the liveserver parameter)

"""
from tests.functional_tests.all_offline_fts import *
from tests.functional_tests.all_online_fts import *
