from tests.api import drop_all_product_lists, drop_all_products
import sys


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("invalid argument, use api_create_test_data.py <server_name>")
    else:
        # clean DB
        print("Use Server: %s" % sys.argv[1])
        drop_all_product_lists(sys.argv[1], "admin", "admin")
        drop_all_products(sys.argv[1], "admin", "admin")

