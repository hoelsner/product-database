"""
Test suite for the productdb.views utils
"""
import pytest
from datetime import datetime
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.core.cache import cache
from mixer.backend.django import mixer
from app.productdb import utils
from app.productdb.utils import login_required_if_login_only_mode

pytestmark = pytest.mark.django_db


class LoginOnlyModelSettingsMock:
    def read_file(self):
        pass

    def is_login_only_mode(self):
        return True


class NoLoginOnlyModelSettingsMock:
    def read_file(self):
        pass

    def is_login_only_mode(self):
        return False


@pytest.mark.usefixtures("import_default_vendors")
def test_convert_product_to_dict():
    today = datetime.today()
    today_str = today.strftime(utils.DEFAULT_DATE_FORMAT)
    date_fields = {
        'end_of_new_service_attachment_date': today,
        'end_of_routine_failure_analysis': today,
        'end_of_sale_date': today,
        'end_of_service_contract_renewal': today,
        'end_of_support_date': today,
        'end_of_sw_maintenance_date': today,
        'eol_ext_announcement_date': today,
        'eox_update_time_stamp': today,
    }
    p = mixer.blend("productdb.Product", **date_fields)
    expected_result = {
        'description': p.description,
        'end_of_new_service_attachment_date': today_str,
        'end_of_routine_failure_analysis': today_str,
        'end_of_sale_date': today_str,
        'end_of_service_contract_renewal': today_str,
        'end_of_support_date': today_str,
        'end_of_sw_maintenance_date': today_str,
        'eol_ext_announcement_date': today_str,
        'eol_reference_number': p.eol_reference_number,
        'eol_reference_url': p.eol_reference_url,
        'eox_update_time_stamp': today_str,
        'product_id': p.product_id
    }

    result = utils.convert_product_to_dict(p)
    assert result == expected_result

    custom_date_format = "%Y-%m-%d"
    today_str = today.strftime(custom_date_format)
    date_fields = {
        'end_of_new_service_attachment_date': today,
        'end_of_routine_failure_analysis': today,
        'end_of_sale_date': today,
        'end_of_service_contract_renewal': today,
        'end_of_support_date': today,
        'end_of_sw_maintenance_date': today,
        'eol_ext_announcement_date': today,
        'eox_update_time_stamp': today,
    }
    p = mixer.blend("productdb.Product", **date_fields)
    expected_result = {
        'description': p.description,
        'end_of_new_service_attachment_date': today_str,
        'end_of_routine_failure_analysis': today_str,
        'end_of_sale_date': today_str,
        'end_of_service_contract_renewal': today_str,
        'end_of_support_date': today_str,
        'end_of_sw_maintenance_date': today_str,
        'eol_ext_announcement_date': today_str,
        'eol_reference_number': p.eol_reference_number,
        'eol_reference_url': p.eol_reference_url,
        'eox_update_time_stamp': today_str,
        'product_id': p.product_id
    }
    result = utils.convert_product_to_dict(p, custom_date_format)
    assert result == expected_result

    # work with none value
    p.end_of_sw_maintenance_date = None
    expected_result["end_of_sw_maintenance_date"] = ""

    result = utils.convert_product_to_dict(p, custom_date_format)
    assert result == expected_result


def test_is_valid_regex():
    valid_pattern = [
        r"Test",
        r"\d+",
        r"^test1234",
        r"^\s{4}",
        r"(asdf)*"
    ]
    invalid_pattern = [
        r"\g++",
        r"^tes[t1234",
        r"^\s4}",
        r"(asdf*"
    ]

    for pattern in valid_pattern:
        assert utils.is_valid_regex(pattern) is True, pattern

    for pattern in invalid_pattern:
        assert utils.is_valid_regex(pattern) is False, pattern

    assert utils.is_valid_regex(None) is False
    assert utils.is_valid_regex(2) is False
    assert utils.is_valid_regex(["moh"]) is False


def test_login_required_if_login_only_mode(monkeypatch):
    user = mixer.blend("auth.User")

    # enabled Login only mode
    monkeypatch.setattr(utils, "AppSettings", LoginOnlyModelSettingsMock)

    request = RequestFactory().get(reverse("productdb:home"))
    request.user = AnonymousUser()
    assert login_required_if_login_only_mode(request) is True, \
        "Anonymous users must login and should be redirected"

    request = RequestFactory().get(reverse("productdb:home"))
    request.user = user
    assert login_required_if_login_only_mode(request) is False, \
        "Authenticated users are logged in and should not be redirected"

    # value should be cached
    assert cache.get("LOGIN_ONLY_MODE_SETTING", None) is not None

    # disable Login only mode and clear cache value
    cache.delete("LOGIN_ONLY_MODE_SETTING")
    monkeypatch.setattr(utils, "AppSettings", NoLoginOnlyModelSettingsMock)

    request = RequestFactory().get(reverse("productdb:home"))
    request.user = AnonymousUser()
    assert login_required_if_login_only_mode(request) is False, \
        "Anonymous users are logged in and should not be redirected"

    request = RequestFactory().get(reverse("productdb:home"))
    request.user = user
    assert login_required_if_login_only_mode(request) is False, \
        "Authenticated users are logged in and should not be redirected"


def test_parse_cisco_show_inventory():
    with pytest.raises(AttributeError):
        # test invalid parameter
        utils.parse_cisco_show_inventory([])

    # returns a list
    assert type(utils.parse_cisco_show_inventory("asdf")) is list

    example_string = """\
NAME: "1", DESCR: "WS-C3750X-24"
PID: WS-C3750X-24T-S , VID: V04 , SN: 12345ABCD
NAME: "Switch 1 - Power Supply 0", DESCR: "FRU Power Supply"
PID: C3KX-PWR-350WAC , VID: V02 , SN: 12345ABCD
NAME: "Switch 1 - FRULink Slot 1 - FRULink Module", DESCR: "FRULink 1G Module"
PID: C3KX-NM-1G , VID: V01 , SN: 12345ABCD"""

    expected_list = [
        "WS-C3750X-24T-S",
        "C3KX-PWR-350WAC",
        "C3KX-NM-1G",
    ]

    assert utils.parse_cisco_show_inventory(example_string) == expected_list

    example_string_with_whitespace = """\
    NAME: "1", DESCR: "WS-C3750X-24"
    PID: WS-C3750X-24T-S , VID: V04 , SN: 12345ABCD
    NAME: "Switch 1 - Power Supply 0", DESCR: "FRU Power Supply"
    PID: C3KX-PWR-350WAC , VID: V02 , SN: 12345ABCD
    NAME: "Switch 1 - FRULink Slot 1 - FRULink Module", DESCR: "FRULink 1G Module"
    PID: C3KX-NM-1G , VID: V01 , SN: 12345ABCD"""

    assert utils.parse_cisco_show_inventory(example_string_with_whitespace) == expected_list

    example_string_with_empty_lines = """\
NAME: "1", DESCR: "WS-C3750X-24"
PID: WS-C3750X-24T-S , VID: V04 , SN: 12345ABCD

NAME: "Switch 1 - Power Supply 0", DESCR: "FRU Power Supply"
PID: C3KX-PWR-350WAC , VID: V02 , SN: 12345ABCD

NAME: "Switch 1 - FRULink Slot 1 - FRULink Module", DESCR: "FRULink 1G Module"
PID: C3KX-NM-1G , VID: V01 , SN: 12345ABCD"""

    assert utils.parse_cisco_show_inventory(example_string_with_empty_lines) == expected_list

    example_string_with_empty_product_id = """\
NAME: "1", DESCR: "WS-C3750X-24"
PID:      VID: V04 , SN: 12345ABCD

NAME: "Switch 1 - Power Supply 0", DESCR: "FRU Power Supply"
PID: C3KX-PWR-350WAC , VID: V02 , SN: 12345ABCD

NAME: "Switch 1 - FRULink Slot 1 - FRULink Module", DESCR: "FRULink 1G Module"
PID: C3KX-NM-1G , VID: V01 , SN: 12345ABCD"""

    expected_list = [
        "C3KX-PWR-350WAC",
        "C3KX-NM-1G",
    ]

    assert utils.parse_cisco_show_inventory(example_string_with_empty_product_id) == expected_list
