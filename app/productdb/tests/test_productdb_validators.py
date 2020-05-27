"""
Test suite for the productdb.validators module
"""
import pytest
import json
from django.core.exceptions import ValidationError
from mixer.backend.django import mixer
from app.productdb.validators import validate_json, validate_product_list_string

pytestmark = pytest.mark.django_db


def test_validate_json():
    json_string = json.dumps({"key": "value"})

    # should not raise an exception
    validate_json(json_string)

    json_string = '{"my key": value}'

    # should raise an exception
    with pytest.raises(ValidationError):
        validate_json(json_string)


def test_validate_product_list_string():
    v = mixer.blend("productdb.Vendor", name="unassigned", id=0)
    mixer.blend("productdb.Product", product_id="myprod1", vendor=v)
    mixer.blend("productdb.Product", product_id="myprod2", vendor=v)
    mixer.blend("productdb.Product", product_id="myprod3", vendor=v)

    # valid test strings
    test_product_string = "myprod1;myprod2;myprod3"
    validate_product_list_string(test_product_string, v.id)

    test_product_string = "myprod1\nmyprod2;myprod3"
    validate_product_list_string(test_product_string, v.id)

    test_product_string = "myprod1;myprod2\nmyprod3"
    validate_product_list_string(test_product_string, v.id)

    # invalid test strings
    test_product_string = "myprod1;myprod4;myprod3"
    expected_error_msg = "The following products are not found in the database for the vendor unassigned: myprod4"
    with pytest.raises(ValidationError) as exinfo:
        validate_product_list_string(test_product_string, v.id)
    assert exinfo.match(expected_error_msg)

    test_product_string = "myprod4;myprod2\nmyprod3"

    with pytest.raises(ValidationError) as exinfo:
        validate_product_list_string(test_product_string, v.id)
    assert exinfo.match(expected_error_msg)

    test_product_string = "myprod1\nmyprod2;myprod4"

    with pytest.raises(ValidationError) as exinfo:
        validate_product_list_string(test_product_string, v.id)
    assert exinfo.match(expected_error_msg)
