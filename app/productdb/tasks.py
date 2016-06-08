import logging

from app.config.models import NotificationMessage
from app.productdb.excel_import import ImportProductsExcelFile, InvalidImportFormatException
from app.productdb.models import JobFile
from django_project.celery import app, TaskState

logger = logging.getLogger(__name__)


@app.task(serializer='json', name="productdb.import_price_list", bind=True)
def import_price_list(self, job_file_id, create_notification_on_server=True):
    """
    import products from the given price list
    """
    self.update_state(state=TaskState.PROCESSING, meta={
        "status_message": "Try to import uploaded product list..."
    })

    try:
        import_excel_file = JobFile.objects.get(id=job_file_id)

    except:
        msg = "Cannot find file that was uploaded."
        logger.error(msg, exc_info=True)
        result = {
            "error_message": msg
        }
        return result

    # verify that file exists
    try:
        import_products_excel = ImportProductsExcelFile(path_to_excel_file=import_excel_file.file)
        import_products_excel.verify_file()

        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": "File valid, start import/update of the database..."
        })
        import_products_excel.import_products_to_database()

        summary_msg = "Product list imported, %s Products changed." % import_products_excel.valid_imported_products
        detail_msg = "<div style=\"text-align:left;\">%s " \
                     "Products successful imported. " % import_products_excel.valid_imported_products

        if import_products_excel.invalid_products != 0:
            detail_msg += "%s entries are faulty. Please check the following messages for additional details."

        if len(import_products_excel.import_result_messages) != 0:
            detail_msg += "<ul>"
            for e in import_products_excel.import_result_messages:
                detail_msg += "<li>%s</li>" % e
            detail_msg += "</ul></div>"

        # if the task was executed eager, set state to SUCCESS (required for testing)
        if self.request.is_eager:
            self.update_state(state=TaskState.SUCCESS, meta={
                "status_message": detail_msg
            })

        if create_notification_on_server:
            NotificationMessage.objects.create(
                title="Import product list",
                type=NotificationMessage.MESSAGE_INFO,
                summary_message=summary_msg,
                detailed_message=detail_msg
            )

        # drop the file
        import_excel_file.delete()

        result = {
            "status_message": detail_msg
        }

    except InvalidImportFormatException as ex:
        msg = "import failed, invalid file format (%s)" % ex
        logger.error(msg, ex)
        result = {
            "error_message": msg
        }

    except Exception as ex:
        msg = "Unexpected exception occurred while importing product list (%s)" % ex
        logger.error(msg, ex)
        result = {
            "error_message": msg
        }

    return result
