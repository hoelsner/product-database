from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient

# verification and error string delivered by the API
STRING_VERIFICATION_ERROR = "Spaces are not allowed"
STRING_UNIQUE_FIELD_REQUIRED = "This field must be unique."
STRING_INVALID_CHARACTER = "Invalid character detected"
STRING_JSON_VERIFICATION_FAILED = "JSON string not parseable, invalid format"
STRING_LIST_PRICE_VERIFICATION_FAILED = "A valid number is required."
STRING_LIST_PRICE_GREATER_OR_EQUAL_ZERO = "Ensure this value is greater than or equal to 0."
STRING_PRODUCT_NOT_FOUND_MESSAGE = "Product name '%s' not found"
STRING_PRODUCT_LIST_NOT_FOUND_MESSAGE = "Product list name '%s' not found"
STRING_PRODUCT_INVALID_CURRENCY_VALUE = '"%s" is not a valid choice.'


class BaseApiUnitTest(APITestCase):
    USERNAME = "admin"
    PASSWORD = "admin"

    def setUp(self):
        u = User.objects.create_user(username=self.USERNAME, password=self.PASSWORD, email="admin@local.local")
        u.save()
        client = APIClient()

        if not client.login(username=self.USERNAME, password=self.PASSWORD):
            self.fail("Login to API failed")
        self.client = client

    def tearDown(self):
        self.client.logout()