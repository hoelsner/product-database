"""
utility functions
"""
import re


def normalize_date(product_object, date_format="%Y/%m/%d"):
    """
    reformat the date entries within a product object to display it on the pages

    :param product_object:
    :param date_format:
    :return:
    """
    result = dict()
    result['product_id'] = product_object.product_id
    result['description'] = product_object.description
    result['eol_reference_number'] = product_object.eol_reference_number
    result['eol_reference_url'] = product_object.eol_reference_url

    if product_object.end_of_sale_date:
        result['end_of_sale_date'] = product_object.end_of_sale_date.strftime(format=date_format)

    if product_object.eox_update_time_stamp:
        result['eox_update_time_stamp'] = product_object.eox_update_time_stamp.strftime(format=date_format)
    else:
        result['eox_update_time_stamp'] = ""

    if product_object.end_of_sale_date:
        result['end_of_sale_date'] = product_object.end_of_sale_date.strftime(format=date_format)
    else:
        result['end_of_sale_date'] = ""

    if product_object.end_of_support_date:
        result['end_of_support_date'] = product_object.end_of_support_date.strftime(format=date_format)
    else:
        result['end_of_support_date'] = ""

    if product_object.eol_ext_announcement_date:
        result['eol_ext_announcement_date'] = product_object.eol_ext_announcement_date.strftime(format=date_format)
    else:
        result['eol_ext_announcement_date'] = ""

    if product_object.end_of_sw_maintenance_date:
        result['end_of_sw_maintenance_date'] = product_object.end_of_sw_maintenance_date.strftime(format=date_format)
    else:
        result['end_of_sw_maintenance_date'] = ""

    if product_object.end_of_routine_failure_analysis:
        result['end_of_routine_failure_analysis'] = product_object.end_of_routine_failure_analysis.strftime(format=date_format)
    else:
        result['end_of_routine_failure_analysis'] = ""

    if product_object.end_of_service_contract_renewal:
        result['end_of_service_contract_renewal'] = product_object.end_of_service_contract_renewal.strftime(format=date_format)
    else:
        result['end_of_service_contract_renewal'] = ""

    if product_object.end_of_new_service_attachment_date:
        result['end_of_new_service_attachment_date'] = product_object.end_of_new_service_attachment_date.strftime(format=date_format)
    else:
        result['end_of_new_service_attachment_date'] = ""

    return result


def is_valid_regex(regex_pattern):
    """
    test that the given pattern is a valid regular expression
    """
    result = True

    if regex_pattern:
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
    else:
        result = False

    return result