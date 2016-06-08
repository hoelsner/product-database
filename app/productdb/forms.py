import tempfile
import logging
from django import forms
from app.productdb.excel_import import ImportProductsExcelFile, InvalidImportFormatException, InvalidExcelFileFormat

logger = logging.getLogger("app.productdb.forms")


class ImportProductsFileUploadForm(forms.Form):
    FILE_EXT_WHITELIST = [
        "xlsx",
    ]

    excel_file = forms.FileField(
        label="Upload Excel File:"
    )

    suppress_notification = forms.BooleanField(
        required=False,
        label="Suppress Server Notification Message"
    )

    def clean(self):
        # validation of the import products excel file
        uploaded_file = self.cleaned_data.get("excel_file")

        if uploaded_file is None:
            raise forms.ValidationError("invalid upload, file has no content.")

        if len(uploaded_file.name.split('.')) == 1:
            raise forms.ValidationError("file type is not supported.")

        if uploaded_file.name.split('.')[-1] not in self.FILE_EXT_WHITELIST:
            raise forms.ValidationError("only .xlsx files is allowed")

        # verify that content can be read
        try:
            tmp = tempfile.NamedTemporaryFile(suffix="." + uploaded_file.name.split(".")[-1])

            tmp.write(uploaded_file.read())

            import_product = ImportProductsExcelFile(tmp.name)
            import_product.verify_file()

            tmp.close()

        except InvalidImportFormatException as ex:
            msg = "Invalid structure in Excel file (%s)" % ex
            logger.info(msg)
            raise forms.ValidationError(msg)

        except InvalidExcelFileFormat:
            logger.debug("Invalid excel file format")
            raise forms.ValidationError("Invalid excel file format")

        except forms.ValidationError:
            raise

        except Exception as ex:
            logger.warn("Unexpected error while uploading file", ex)
            raise forms.ValidationError("Unexpected error occurred during upload (%s)" % ex)
