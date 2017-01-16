import logging
from django.contrib.auth.models import User
from app.config.models import NotificationMessage
from app.productdb.excel_import import ProductsExcelImporter, InvalidImportFormatException, InvalidExcelFileFormat, \
    ProductMigrationsExcelImporter
from app.productdb.models import JobFile, ProductCheck
from django_project.celery import app, TaskState
import time

logger = logging.getLogger("productdb")


@app.task(name="productdb.delete_all_product_checks")
def delete_all_product_checks():
    ProductCheck.objects.all().delete()


@app.task(serializer="json", name="productdb.perform_product_check", bind=True)
def perform_product_check(self, product_check_id):
    """
    process the Product Check
    :param self:
    :param product_check_id:
    :return:
    """
    def update_task_state(status_message):
        """Update the status message of the task, which is displayed in the watch view"""
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": status_message
        })

    update_task_state("Load Product Check...")

    # wait for 3 seconds to ensure that the database has the new Product Check (issue with very large product checks)
    time.sleep(3)

    try:
        product_check = ProductCheck.objects.get(id=product_check_id)
        product_check.task_id = self.request.id
        product_check.save()

    except Exception as ex:
        msg = "Cannot load product check, ID not found in database (%s)." % str(ex)
        logger.error(msg, exc_info=True)
        result = {
            "error_message": msg
        }
        return result

    update_task_state("Product Check in progress, please wait...")

    product_check.perform_product_check()
    result = {
        "status_message": "Product check successful finished."
    }
    product_check.task_id = None
    product_check.save()

    # if the task was executed eager, set state to SUCCESS (required for testing)
    if self.request.is_eager:
        self.update_state(state=TaskState.SUCCESS, meta=result)

    return result


@app.task(serializer='json', name="productdb.import_product_migrations", bind=True)
def import_product_migrations(self, job_file_id, user_for_revision=None):
    """
    import product migrations from the Excel file
    :param job_file_id: ID within the database that references the Excel file that should be imported
    :param user_for_revision: username that should be used for the revision tracking (only if started manually)
    :return:
    """
    def update_task_state(status_message):
        """Update the status message of the task, which is displayed in the watch view"""
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": status_message
        })

    update_task_state("Try to import uploaded file...")

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
        import_product_migrations_excel = ProductMigrationsExcelImporter(
            path_to_excel_file=import_excel_file.file,
            user_for_revision=User.objects.get(username=user_for_revision)
        )
        import_product_migrations_excel.verify_file()
        update_task_state("File valid, start updating the database...")

        import_product_migrations_excel.import_to_database(status_callback=update_task_state)
        update_task_state("Database import finished, processing results...")

        status_message = "<p style=\"text-align: left\">Product migrations successful updated</p>" \
                         "<ul style=\"text-align: left\">"
        for msg in import_product_migrations_excel.import_result_messages:
            status_message += "<li>%s</li>" % msg
        status_message += "</ul>"

        # drop the JobFile
        import_excel_file.delete()

        result = {
            "status_message": status_message
        }

    except (InvalidImportFormatException, InvalidExcelFileFormat) as ex:
        msg = "import failed, invalid file format (%s)" % ex
        logger.error(msg, ex)
        result = {
            "error_message": msg
        }

    except Exception as ex:  # catch any exception
        msg = "Unexpected exception occurred while importing product list (%s)" % ex
        logger.error(msg, ex)
        result = {
            "error_message": msg
        }

    # if the task was executed eager, set state to SUCCESS (required for testing)
    if self.request.is_eager:
        self.update_state(state=TaskState.SUCCESS, meta=result)

    return result


@app.task(serializer='json', name="productdb.import_price_list", bind=True)
def import_price_list(self, job_file_id, create_notification_on_server=True, update_only=False, user_for_revision=None):
    """
    import products from the given price list
    :param job_file_id: ID within the database that references the Excel file that should be imported
    :param create_notification_on_server: create a new Notification Message on the Server
    :param update_only: Don't create new products in the database, update only existing ones
    :param user_for_revision: username that should be used for the revision tracking (only if started manually)
    """
    def update_task_state(status_message):
        """Update the status message of the task, which is displayed in the watch view"""
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": status_message
        })

    update_task_state("Try to import uploaded file...")

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
        import_products_excel = ProductsExcelImporter(
            path_to_excel_file=import_excel_file.file,
            user_for_revision=User.objects.get(username=user_for_revision)
        )
        import_products_excel.verify_file()
        update_task_state("File valid, start updating the database...")

        import_products_excel.import_to_database(status_callback=update_task_state, update_only=update_only)
        update_task_state("Database import finished, processing results...")

        summary_msg = "User <strong>%s</strong> imported a Product list, %s Products " \
                      "changed." % (user_for_revision, import_products_excel.valid_imported_products)
        detail_msg = "<div style=\"text-align:left;\">%s " \
                     "Products successful updated. " % import_products_excel.valid_imported_products

        if import_products_excel.invalid_products != 0:
            detail_msg += "%s entries are invalid. Please check the following messages for " \
                          "more details." % import_products_excel.invalid_products

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

    except (InvalidImportFormatException, InvalidExcelFileFormat) as ex:
        msg = "import failed, invalid file format (%s)" % ex
        logger.error(msg, ex)
        result = {
            "error_message": msg
        }

    except Exception as ex:  # catch any exception
        msg = "Unexpected exception occurred while importing product list (%s)" % ex
        logger.error(msg, ex)
        result = {
            "error_message": msg
        }

    # if the task was executed eager, set state to SUCCESS (required for testing)
    if self.request.is_eager:
        self.update_state(state=TaskState.SUCCESS, meta=result)

    return result
