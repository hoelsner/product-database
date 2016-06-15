from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient

# verification and error string delivered by the API
STRING_VERIFICATION_ERROR = "Spaces are not allowed"
STRING_UNIQUE_FIELD_REQUIRED = "already exists."
STRING_INVALID_CHARACTER = "Invalid character detected"
STRING_JSON_VERIFICATION_FAILED = "JSON string not parseable, invalid format"
STRING_LIST_PRICE_VERIFICATION_FAILED = "A valid number is required."
STRING_LIST_PRICE_GREATER_OR_EQUAL_ZERO = "Ensure this value is greater than or equal to 0."
STRING_PRODUCT_NOT_FOUND_MESSAGE = "Product name '%s' not found"
STRING_PRODUCT_LIST_NOT_FOUND_MESSAGE = "Product list name '%s' not found"
STRING_PRODUCT_INVALID_CURRENCY_VALUE = '"%s" is not a valid choice.'


class BaseApiUnitTest(APITestCase):
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
    API_USERNAME = "api"
    API_PASSWORD = "api"

    def setUp(self):
        try:
            User.objects.get(username=self.ADMIN_USERNAME)

        except:
            u = User.objects.create_superuser(
                username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD, email="admin@local.local"
            )
            u.save()

        try:
            User.objects.get(username=self.API_USERNAME)

        except:
            u = User.objects.create_user(
                username=self.API_USERNAME, password=self.API_PASSWORD, email="api@local.local"
            )
            u.save()

        client = APIClient()

        if not client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD):
            self.fail("Login to API failed")
        self.client = client

    def tearDown(self):
        self.client.logout()