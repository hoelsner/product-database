import json
import os
from django.utils.six import BytesIO
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from app.productdb.models import Product
from app.productdb.models import ProductList
from app.productdb.serializers import ProductBackupSerializer
from app.productdb.serializers import ProductListBackupSerializer

PRODUCT_BACKUP_FILE_NAME = "products.json"
PRODUCT_LIST_BACKUP_FILE_NAME = "product_lists.json"


def create_backup(backup_directory=os.path.join("..", "backup")):
    """
    create the backup files within the given backup directory

    :param backup_directory: directory, where the files should be saved
    :return:
    """
    os.makedirs(backup_directory, exist_ok=True)

    # backup product objects
    products = Product.objects.all()
    data = []

    for p in products:
        serializer = ProductBackupSerializer(p)
        json_data = JSONRenderer().render(serializer.data).decode("utf-8")
        data.append(json.loads(json_data))

    product_backup = {
        "version": "0.2",
        "data": data
    }

    f = open(os.path.join(backup_directory, PRODUCT_BACKUP_FILE_NAME), "w")
    f.write(json.dumps(product_backup))
    f.close()

    # backup product list objects
    product_lists = ProductList.objects.all()
    data = []

    for pl in product_lists:
        serializer = ProductListBackupSerializer(pl)
        json_data = JSONRenderer().render(serializer.data).decode("latin")
        data.append(json.loads(json_data))

    product_list_backup = {
        "version": "0.2",
        "data": data
    }

    f = open(os.path.join(backup_directory, PRODUCT_LIST_BACKUP_FILE_NAME), "w")
    f.write(json.dumps(product_list_backup))
    f.close()


def restore_backup(backup_directory=os.path.join("..", "backup")):
    """
    restore a backup from the files that are located at the given directory

    Please note: only non-existing objects are created during the update, there is no partial update

    :param backup_directory: directory with the backup files
    :return:
    """
    if os.path.exists(backup_directory):
        if not os.path.isdir(backup_directory):
            # not a directory
            raise NotADirectoryError("given directory is not a directory")
    else:
        # backup path not exists, raise exception
        raise FileNotFoundError("given directory does not exist")

    product_lists = json.load(open(os.path.join(backup_directory, PRODUCT_LIST_BACKUP_FILE_NAME), "r"))
    products = json.load(open(os.path.join(backup_directory, PRODUCT_BACKUP_FILE_NAME), "r"))

    # verify backup data version
    if product_lists["version"] != "0.2":
        raise BaseException("unsupported version of product list backup file")
    if products["version"] != "0.2":
        raise BaseException("unsupported version of product backup file")

    # create product lists from backup
    for pl_data in product_lists["data"]:
        stream = BytesIO(json.dumps(pl_data).encode("utf-8"))
        data = JSONParser().parse(stream)
        pl = ProductListBackupSerializer(data=data)
        if pl.is_valid():
            pl.save()

    # create products from backup
    for p_data in products["data"]:
        stream = BytesIO(json.dumps(p_data).encode("utf-8"))
        data = JSONParser().parse(stream)
        p = ProductBackupSerializer(data=data)
        if p.is_valid():
            p.save()
            prod = Product.objects.get(product_id=p_data["product_id"])

            # add product to lists (not part of the Backup serializer)
            for l in p_data["lists"]:
                pl, _ = ProductList.objects.get_or_create(product_list_name=l)
                prod.lists.add(pl)
