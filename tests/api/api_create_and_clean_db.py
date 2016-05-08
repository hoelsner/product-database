from tests.api import create_real_test_data
from tests.api import drop_all_products
import sys

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("invalid argument, use api_create_test_data.py <server_name> [<type of data>]")
        print("\ttype of data: real - real test data")
    else:
        print("Use Server: %s" % sys.argv[1])
        create_real_test_data(sys.argv[1], "admin", "admin")

    input("Press any key to continue")
    drop_all_products(sys.argv[1], "admin", "admin")
