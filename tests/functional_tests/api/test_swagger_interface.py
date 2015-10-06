from tests.base.django_test_cases import DestructiveProductDbFunctionalTest


class SwaggerApiDocs(DestructiveProductDbFunctionalTest):
    """
    contains "smoke" test for the swagger API interface
    """
    fixtures = ['default_vendors.yaml']

    def test_swagger_has_no_internal_error(self):
        # a user hits  the API documentation pages
        self.browser.get(self.server_url + "/productdb/api-docs/")
        self.browser.implicitly_wait(3)

        # check that the user sees a table
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn("INTERNAL SERVER ERROR", page_text, "loading Swagger sites failed.")

