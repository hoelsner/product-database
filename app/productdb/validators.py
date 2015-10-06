import json
from django.core.exceptions import ValidationError


"""
CUSTOM Validators
"""


def validate_json(value):
    """
    a simple JSON validator for the model
    :param value:
    :return:
    """
    try:
        json.loads(value)
    except:
        raise ValidationError("JSON string not parseable, invalid format")
