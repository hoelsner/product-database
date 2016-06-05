"""
Unit tests for the Datatables API endpoints
"""
from django.core.urlresolvers import reverse
from django.test import TestCase
import json


class DatatablesApiEndpointTest(TestCase):
    fixtures = ['default_vendors.yaml']

    # just smoke tests to verify the basic operation of the datatables server side processing
    def test_get_data_from_datatables_vendor_products_endpoint(self):
        url = reverse('productdb:datatables_vendor_products_endpoint', kwargs={'vendor_id': 1})

        result = self.client.get(url)
        self.assertTrue(result.status_code, 200)
        result_json = json.loads(result.content.decode("utf-8"))

        self.assertTrue("data" in result_json.keys())
        self.assertTrue("draw" in result_json.keys())
        self.assertTrue("recordsTotal" in result_json.keys())
        self.assertTrue("recordsFiltered" in result_json.keys())
