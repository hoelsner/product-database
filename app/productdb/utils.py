import re
import jtextfsm as textfsm
import io
from django.core.cache import cache
from app.config.settings import AppSettings

DEFAULT_DATE_FORMAT = "%Y/%m/%d"


def convert_product_to_dict(product_object, date_format=DEFAULT_DATE_FORMAT):
    """
    convert a product object to a dictionary with a specific date_format representation

    :param product_object:
    :param date_format:
    :return:
    """
    result = dict()
    result['product_id'] = product_object.product_id
    result['description'] = product_object.description
    result['eol_reference_number'] = product_object.eol_reference_number
    result['eol_reference_url'] = product_object.eol_reference_url

    date_attributes = [
        'end_of_new_service_attachment_date',
        'end_of_routine_failure_analysis',
        'end_of_sale_date',
        'end_of_service_contract_renewal',
        'end_of_support_date',
        'end_of_sw_maintenance_date',
        'eol_ext_announcement_date',
        'eox_update_time_stamp',
    ]

    for attr in date_attributes:
        result[attr] = getattr(product_object, attr).strftime(format=date_format)\
            if getattr(product_object, attr) else ""

    return result


def is_valid_regex(regex_pattern):
    """
    test that the given pattern is a valid regular expression
    """
    result = True

    if type(regex_pattern) is not str:
        result = False

    else:
        # check curly brackets (compile function won't throw an exception)
        open = len([e for e in regex_pattern if e == "{"])
        close = len([e for e in regex_pattern if e == "}"])
        if open == close:
            try:
                re.compile(regex_pattern, re.IGNORECASE)
            except:
                result = False
        else:
            # unbalanced curly brackets, invalid statement
            result = False

    return result


def login_required_if_login_only_mode(request):
    """
    Test if the login only mode is enabled. If this is the case, test if a user is authentication. If this is not the
    case, redirect to the login form.
    """
    login_only_mode = cache.get("LOGIN_ONLY_MODE_SETTING", None)

    if not login_only_mode:
        # key not in cache
        app_settings = AppSettings()
        login_only_mode = app_settings.is_login_only_mode()

        # add setting to cache
        cache.set("LOGIN_ONLY_MODE_SETTING", login_only_mode, 60 * 60)

    if login_only_mode:
        if not request.user.is_authenticated:
            return True

    return False


def parse_cisco_show_inventory(content):
    """
    convert the output of a show inventory command to a list of product IDs
    :param content:
    :return:
    """
    if type(content) is not str:
        raise AttributeError("content must be a string data type")

    # remove empty lines and leading and trailing whitespace
    sanitized_content = "\n".join([line.strip() for line in content.splitlines() if line != ""])

    template = io.StringIO()
    template.write("""\
Value name (.+)
Value description (.*)
Value productid (\S*)
Value vid (\S*)
Value Required serialnumber (\S+)

Start
  ^NAME: "${name}", DESCR: "${description}"
  ^PID: ${productid}.*VID: ${vid}.*SN: ${serialnumber} -> Record
""")
    template.seek(0)

    show_inventory_template = textfsm.TextFSM(template)
    fsm_results = show_inventory_template.ParseText(sanitized_content)

    return [line[2] for line in fsm_results if line[2] != ""]


def split_string(string, length=65536):
    """
    small utility to split string
    :param string:
    :param length:
    :return:
    """
    while string:
        yield string[:length]
        string = string[length:]
