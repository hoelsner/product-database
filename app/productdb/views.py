import tempfile
import logging

from django.conf import settings
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.shortcuts import resolve_url
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from djcelery.models import WorkerState

import app.productdb.tasks as tasks
from app.config import AppSettings
from app.config.utils import update_periodic_cisco_eox_api_crawler_task, test_cisco_hello_api_access
from app.productdb import util as app_util
from app.productdb.models import Vendor
from app.productdb.models import Product
from app.productdb.forms import CiscoApiSettingsForm
from app.productdb.forms import CommonSettingsForm
from app.productdb.forms import ImportProductsFileUploadForm
from app.productdb.extapi import ciscoapiconsole
from app.productdb.extapi.exception import InvalidClientCredentialsException
from app.productdb.extapi.exception import CiscoApiCallFailed
from app.productdb.extapi.exception import ConnectionFailedException
from app.productdb.crawler.cisco_eox_api_crawler import update_cisco_eox_database
from app.productdb.excel_import import ImportProductsExcelFile

logger = logging.getLogger(__name__)


def home(request):
    """view for the homepage of the Product DB

    :param request:
    :return:
    """
    return render_to_response("productdb/home.html", context={}, context_instance=RequestContext(request))


def about_view(request):
    """about view

    :param request:
    :return:
    """
    return render_to_response("productdb/about.html", context={}, context_instance=RequestContext(request))


def browse_vendor_products(request):
    """View to browse the product by vendor

    :param request:
    :return:
    """
    context = {
        "vendors": Vendor.objects.all()
    }
    selected_vendor = ""

    if request.method == "POST":
        selected_vendor = request.POST['vendor_selection']
    else:
        default_vendor = "Cisco Systems"
        for vendor in context['vendors']:
            if vendor.name == default_vendor:
                selected_vendor = vendor.id
                break

    context['vendor_selection'] = selected_vendor

    return render_to_response("productdb/browse/vendor_products.html",
                              context=context,
                              context_instance=RequestContext(request))


def browse_product_lifecycle_information(request):
    """View to browse the lifecycle information for products by vendor

    :param request:
    :return:
    """
    context = {
        "vendors": Vendor.objects.all()
    }
    selected_vendor = ""

    if request.method == "POST":
        selected_vendor = request.POST['vendor_selection']

    context['vendor_selection'] = selected_vendor

    return render_to_response("productdb/lifecycle/lifecycle_information_by_vendor_products.html",
                              context=context,
                              context_instance=RequestContext(request))


def bulk_eol_check(request):
    """view that executes and handles the Bulk EoL check function

    :param request:
    :return:
    """
    context = {}

    if request.method == "POST":
        db_queries = request.POST['db_query'].splitlines()

        # clean POST db queries
        clean_db_queries = []
        for q in db_queries:
            clean_db_queries.append(q.strip())
        db_queries = filter(None, clean_db_queries)

        # detailed product results
        query_result = []
        # result statistics
        result_stats = dict()
        # queries, that are not found in the database or that are not affected by an EoL announcement
        skipped_queries = dict()

        for query in db_queries:
            q_result_counter = 0
            found_but_no_eol_announcement = False
            db_result = Product.objects.filter(product_id=query.strip())

            for element in db_result:
                q_result_counter += 1

                # check if the product is affected by an EoL announcement
                if element.eol_ext_announcement_date is None:
                    found_but_no_eol_announcement = True

                # don't add duplicates to query result, create statistical element
                if element.product_id not in result_stats.keys():
                    query_result.append(app_util.normalize_date(element))
                    result_stats[element.product_id] = dict()
                    result_stats[element.product_id]['count'] = 1
                    result_stats[element.product_id]['product'] = element
                    if element.eol_ext_announcement_date:
                        result_stats[element.product_id]['state'] = "EoS/EoL"
                    else:
                        result_stats[element.product_id]['state'] = "Not EoL"

                # increment statistics
                else:
                    result_stats[element.product_id]['count'] += 1

            if (q_result_counter == 0) or found_but_no_eol_announcement:
                if found_but_no_eol_announcement:
                    q_res_str = "no EoL announcement found"
                else:
                    # add queries without result to the stats and the counter
                    q_res_str = "Not found in database"
                    if query not in result_stats.keys():
                        print("Q " + query)
                        result_stats[query] = dict()
                        result_stats[query]['state'] = "Not found"
                        result_stats[query]['product'] = dict()
                        result_stats[query]['product']['product_id'] = query
                        result_stats[query]['count'] = 1
                    else:
                        result_stats[query]['count'] += 1

                # ignore duplicates
                if query not in skipped_queries.keys():
                    skipped_queries[query] = {
                        "query": query.strip(),
                        "result": q_res_str
                    }

        context['query_result'] = query_result
        context['result_stats'] = result_stats
        context['skipped_queries'] = skipped_queries

        # simply display an error message if no result is found
        if len(query_result) == 0:
            context['query_no_result'] = True

    return render_to_response("productdb/lifecycle/bulk_eol_check.html",
                              context=context,
                              context_instance=RequestContext(request))


@login_required()
@permission_required('is_superuser')
def settings_view(request):
    """View for common Product Database settings

    :param request:
    :return:
    """
    app_config = AppSettings()
    app_config.read_file()

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = CommonSettingsForm(request.POST)
        if form.is_valid():
            # process the data in form.cleaned_data as required
            app_config.set_cisco_api_enabled(form.cleaned_data['cisco_api_enabled'])

            if not app_config.is_cisco_api_enabled():
                # reset values from API configuration
                base_api = ciscoapiconsole.BaseCiscoApiConsole()
                base_api.client_id = "PlsChgMe"
                base_api.client_secret = "PlsChgMe"
                base_api.save_client_credentials()

                app_config.set_cisco_api_client_id("")
                app_config.set_cisco_api_client_secret("")
                app_config.set_product_blacklist_regex("")
                app_config.set_cisco_eox_api_queries("")
                app_config.set_cisco_eox_api_auto_sync_last_execution_result(False)
                app_config.set_cisco_api_credentials_successful_tested(False)
                app_config.set_periodic_sync_enabled(False)
                update_periodic_cisco_eox_api_crawler_task(False)       # disable periodic sync

                app_config.set(
                    value="not tested",
                    key="cisco_api_credentials_last_message",
                    section=AppSettings.CISCO_API_SECTION
                )
                app_config.set(
                    value=False,
                    key="cisco_api_credentials_successful_tested",
                    section=AppSettings.CISCO_API_SECTION
                )

            app_config.write_file()

            return redirect(resolve_url("productdb:settings"))

    else:
        form = CommonSettingsForm()
        form.fields['cisco_api_enabled'].initial = app_config.is_cisco_api_enabled()

    context = {
        "form": form,
        "cisco_api_enabled": app_config.is_cisco_api_enabled()
    }

    return render_to_response("productdb/settings/settings.html",
                              context=context,
                              context_instance=RequestContext(request))


@login_required()
@permission_required('is_superuser')
def cisco_api_settings(request):
    """View for the settings of the Cisco API console

    :param request:
    :return: :raise:
    """
    app_config = AppSettings()
    app_config.read_file()

    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = CiscoApiSettingsForm(request.POST)
        if form.is_valid():
            old_credentials = app_config.get_cisco_api_client_id() + app_config.get_cisco_api_client_secret()
            new_credentials = form.cleaned_data['cisco_api_client_id'] + form.cleaned_data['cisco_api_client_secret']

            if not new_credentials == old_credentials:
                # test credentials (if not in demo mode)
                if settings.DEMO_MODE:
                    logger.warn("skipped verification of the Hello API call to test the credentials, "
                                "DEMO MODE enabled")
                    app_config.set_cisco_api_credentials_last_message("Demo Mode")
                    app_config.set_cisco_api_credentials_successful_tested(True)

                else:
                    try:
                        test_cisco_hello_api_access(
                            form.cleaned_data['cisco_api_client_id'],
                            form.cleaned_data['cisco_api_client_secret']
                        )
                        app_config.set_cisco_api_credentials_last_message("successful connected")
                        app_config.set_cisco_api_credentials_successful_tested(True)

                    except InvalidClientCredentialsException as ex:
                        logger.warn("verification of client credentials failed", exc_info=True)
                        app_config.set_cisco_api_credentials_last_message(str(ex))
                        app_config.set_cisco_api_credentials_successful_tested(False)

            # process the data in form.cleaned_data as required
            app_config.set_periodic_sync_enabled(form.cleaned_data['eox_api_auto_sync_enabled'])
            update_periodic_cisco_eox_api_crawler_task(form.cleaned_data['eox_api_auto_sync_enabled'])

            app_config.set_cisco_eox_api_queries(form.cleaned_data['eox_api_queries'])
            app_config.set_product_blacklist_regex(form.cleaned_data['eox_api_blacklist'])
            app_config.set_auto_create_new_products(form.cleaned_data['eox_auto_sync_auto_create_elements'])

            app_config.set_cisco_api_client_id(form.cleaned_data['cisco_api_client_id'])
            app_config.set_cisco_api_client_secret(form.cleaned_data['cisco_api_client_secret'])

            app_config.write_file()
            return redirect(resolve_url("productdb:cisco_api_settings"))

    else:
        form = CiscoApiSettingsForm()
        form.fields['eox_auto_sync_auto_create_elements'].initial = app_config.is_auto_create_new_products()
        form.fields['eox_api_auto_sync_enabled'].initial = app_config.is_periodic_sync_enabled()
        form.fields['eox_api_queries'].initial = app_config.get_cisco_eox_api_queries()
        form.fields['eox_api_blacklist'].initial = app_config.get_product_blacklist_regex()

        if app_config.is_cisco_api_enabled():
            try:
                base_api = ciscoapiconsole.CiscoHelloApi()
                base_api.load_client_credentials()
                # load the client credentials if exist
                cisco_api_credentials = base_api.get_client_credentials()

                form.fields['cisco_api_client_id'].initial = cisco_api_credentials['client_id']
                form.fields['cisco_api_client_secret'].initial = cisco_api_credentials['client_secret']

            except Exception:
                logger.fatal("unexpected exception occurred", exc_info=True)
                raise
        else:
            form.cisco_api_client_id = False
            form.fields['cisco_api_client_secret'].required = False

    context = {
        "settings_form": form,
        "settings": app_config.to_dictionary()
    }
    print(app_config.to_dictionary())

    return render_to_response("productdb/settings/cisco_api_settings.html",
                              context=context,
                              context_instance=RequestContext(request))


@login_required()
@permission_required('is_superuser')
def crawler_overview(request):
    """Overview of the tasks

    :param request:
    :return:
    """
    app_config = AppSettings()
    app_config.read_file()

    context = {
        "settings": app_config.to_dictionary()
    }

    # determine worker status
    ws = WorkerState.objects.all()
    if ws.count() == 0:
        worker_status = """
        <div class="alert alert-danger" role="alert">
            <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
            <span class="sr-only">Error:</span>
            No worker found, periodic and scheduled tasks will not run
        </div>"""
    else:
        alive_worker = False
        for w in ws:
            if w.is_alive():
                alive_worker = True
                break
        if alive_worker:
            worker_status = """
            <div class="alert alert-success" role="alert">
                <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
                <span class="sr-only">Error:</span>
                Online Worker found, task backend running.
            </div>"""

        else:
            worker_status = """
            <div class="alert alert-warning" role="alert">
                <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
                <span class="sr-only">Error:</span>
                Only offline Worker found, task backend not running. Please verify the state in the
                <a href="/admin">Django Admin</a> frontend.
            </div>"""

    context['worker_status'] = mark_safe(worker_status)

    return render_to_response("productdb/settings/crawler_overview.html",
                              context=context,
                              context_instance=RequestContext(request))


@login_required()
@permission_required('is_superuser')
def test_tools(request):
    """test tools for the application (mainly about the crawler functions)

    :param request:
    :return:
    """
    app_config = AppSettings()
    app_config.read_file()

    context = {
        "settings": app_config.to_dictionary()
    }

    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        if "sync_cisco_eox_states_now" in request.POST.keys():
            if "sync_cisco_eox_states_query" in request.POST.keys():
                query = request.POST['sync_cisco_eox_states_query']

                if query != "":
                    if len(query.split(" ")) == 1:
                        context['query_executed'] = query
                        try:
                            eox_api_update_records = update_cisco_eox_database(api_query=query)

                        except ConnectionFailedException as ex:
                            eox_api_update_records = ["Cannot contact Cisco API, error message:\n%s" % ex]

                        except CiscoApiCallFailed as ex:
                            eox_api_update_records = [ex]

                        except Exception as ex:
                            logger.debug("execution failed due to unexpected exception", exc_info=True)
                            eox_api_update_records = ["execution failed: %s" % ex]

                        context['eox_api_update_records'] = eox_api_update_records

                    else:
                        context['eox_api_update_records'] = ["Invalid query '%s': not executed" %
                                                             request.POST['sync_cisco_eox_states_query']]
                else:
                    context['eox_api_update_records'] = ["Please specify a valid query"]

    # determine worker status
    ws = WorkerState.objects.all()
    if ws.count() == 0:
        worker_status = """
        <div class="alert alert-danger" role="alert">
            <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
            <span class="sr-only">Error:</span>
            No worker found, periodic and scheduled tasks will not run
        </div>"""
    else:
        alive_worker = False
        for w in ws:
            if w.is_alive():
                alive_worker = True
                break
        if alive_worker:
            worker_status = """
            <div class="alert alert-success" role="alert">
                <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
                <span class="sr-only">Error:</span>
                Online Worker found, task backend running.
            </div>"""

        else:
            worker_status = """
            <div class="alert alert-warning" role="alert">
                <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
                <span class="sr-only">Error:</span>
                Only offline Worker found, task backend not running. Please verify the state in the
                <a href="/admin">Django Admin</a> frontend.
            </div>"""

    context['worker_status'] = mark_safe(worker_status)

    return render_to_response("productdb/settings/task_testing_tools.html",
                              context=context,
                              context_instance=RequestContext(request))


@login_required()
@permission_required('is_superuser')
def schedule_cisco_eox_api_sync_now(request):
    """View which manually schedules an Cisco EoX synchronization and redirects to the given URL
    or the main settings page.

    :param request:
    :return:
    """
    app_config = AppSettings()
    app_config.read_file()

    task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()
    app_config.set(
        section=AppSettings.CISCO_EOX_CRAWLER_SECTION,
        key="eox_api_sync_task_id",
        value= task.id
    )
    app_config.write_file()

    return redirect(request.GET.get('redirect_url', "/productdb/settings/"))


@login_required()
@permission_required('is_superuser')
def import_products(request):
    """view for the import of products using Excel

    :param request:
    :return:
    """
    context = {}
    if request.method == "POST":
        form = ImportProductsFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # file is valid, execute the import
            uploaded_file = request.FILES['excel_file']

            tmp = tempfile.NamedTemporaryFile(suffix="." + uploaded_file.name.split(".")[-1])

            uploaded_file.open()
            tmp.write(uploaded_file.read())

            try:
                import_products_excel = ImportProductsExcelFile(tmp.name)
                import_products_excel.verify_file()
                import_products_excel.import_products_to_database()

                context['import_valid_imported_products'] = import_products_excel.valid_imported_products
                context['import_invalid_products'] = import_products_excel.invalid_products
                context['import_messages'] = import_products_excel.import_result_messages
                context['import_result'] = "success"

            except Exception as ex:
                msg = "unexpected error occurred during import (%s)" % ex
                logger.error(msg, ex)
                context['import_messages'] = msg
                context['import_result'] = "error"

            finally:
                tmp.close()

    else:
        form = ImportProductsFileUploadForm()

    context['form'] = form

    return render_to_response("productdb/settings/import_products.html",
                              context=context,
                              context_instance=RequestContext(request))
