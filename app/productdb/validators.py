import json
from django.core.exceptions import ValidationError
import app.productdb.models


def validate_json(value):
    """a simple JSON validator

    :param value:
    :return:
    """
    try:
        json.loads(value)
    except:
        raise ValidationError("Invalid format of JSON data string")


def validate_product_list_string(value):
    """
    verifies that a product list string contains only valid Product IDs that are stored in the database
    """
    values = []
    missing_products = []

    for line in value.splitlines():
        values += line.split(";")
    values = sorted([e.strip() for e in values])

    for value in values:
        try:
            app.productdb.models.Product.objects.get(product_id=value)

        except:
            missing_products.append(value)

    if len(missing_products) != 0:
        msg = "The following products are not found in the database: %s" % ",".join(missing_products)
        raise ValidationError(msg, code="invalid")
