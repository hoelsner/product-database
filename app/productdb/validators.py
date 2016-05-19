import json
from django.core.exceptions import ValidationError


def validate_json(value):
    """
    a simple JSON validator for the model
    :param value:
    :return:
    """
    try:
        json.loads(value)
    except:
        raise ValidationError("Invalid format of JSON data string")
