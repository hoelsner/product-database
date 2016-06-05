from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import resolve_url, redirect, render
from django.utils.safestring import mark_safe
from djcelery.models import WorkerState

from app.config import AppSettings
from app.config.forms import SettingsForm, NotificationMessageForm
from app.config.models import NotificationMessage
from app.config.utils import test_cisco_eox_api_access
from django_project.utils import login_required_if_login_only_mode


@login_required()
@permission_required('is_superuser', raise_exception=True)
def add_notification(request):
    """
    add a notification
    """
    if request.method == "POST":
        form = NotificationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse("productdb:home"))

    else:
        form = NotificationMessageForm()

    context = {
        "form": form
    }

    return render(request, "config/notification-add.html", context=context)


@login_required()
@permission_required('is_superuser', raise_exception=True)
def status(request):
    """
    Status page for the Product Database
    """
    app_config = AppSettings()
    app_config.read_file()

    is_cisco_api_enabled = app_config.is_cisco_api_enabled()
    context = {
        "is_cisco_api_enabled": is_cisco_api_enabled
    }

    if is_cisco_api_enabled:
        # test access (once every 30 minutes)
        cisco_eox_api_test_successful = cache.get("CISCO_EOC_API_TEST", False)

        # defaults, overwritten if an exception is thrown
        cisco_eox_api_available = True
        cisco_eox_api_message = "successful connected to the Cisco EoX API"

        if not cisco_eox_api_test_successful:
            try:
                test_cisco_eox_api_access(client_id=app_config.get_cisco_api_client_id(),
                                          client_secret=app_config.get_cisco_api_client_secret(),
                                          drop_credentials=False)
                cache.set("CISCO_EOC_API_TEST", True, 60 * 30)

            except Exception as ex:
                cisco_eox_api_available = True
                cisco_eox_api_message = str(ex)

        context["cisco_eox_api_available"] = cisco_eox_api_available
        context["cisco_eox_api_message"] = cisco_eox_api_message

    # determine worker status
    ws = WorkerState.objects.all()
    if ws.count() == 0:
        worker_status = """
            <div class="alert alert-danger" role="alert">
                <span class="fa fa-exclamation-circle"></span>
                <span class="sr-only">Error:</span>
                All backend worker offline, asynchronous and scheduled tasks are not executed.
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
                    <span class="fa fa-info-circle"></span>
                    <span class="sr-only">Error:</span>
                    Backend worker found.
                </div>"""

        else:
            worker_status = """
                <div class="alert alert-warning" role="alert">
                    <span class="fa fa-exclamation-circle"></span>
                    <span class="sr-only">Error:</span>
                    Only unregistered backend worker found, asynchronous and scheduled tasks are not executed.
                    Please verify the state in the <a href="/productdb/admin">Django Admin</a> page.
                </div>"""

    context['worker_status'] = mark_safe(worker_status)

    return render(request, "config/status.html", context=context)


@login_required()
@permission_required('is_superuser', raise_exception=True)
def change_configuration(request):
    """
    change configuration of the Product Database
    """
    app_config = AppSettings()
    app_config.read_file()

    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = SettingsForm(request.POST)
        if form.is_valid():
            # set common settings
            app_config.set_login_only_mode(form.cleaned_data["login_only_mode"])

            # set the Cisco API configuration options
            api_enabled = form.cleaned_data["cisco_api_enabled"]

            if not api_enabled:
                # api is disabled, reset values to default
                app_config.set_cisco_api_enabled(api_enabled)
                app_config.set_cisco_api_client_id("PlsChgMe")
                app_config.set_cisco_api_client_secret("PlsChgMe")
                app_config.set_cisco_eox_api_auto_sync_enabled(False)
                app_config.set_auto_create_new_products(False)
                app_config.set_cisco_eox_api_queries("")
                app_config.set_product_blacklist_regex("")

            else:
                app_config.set_cisco_api_enabled(api_enabled)

                client_id = form.cleaned_data["cisco_api_client_id"] \
                    if form.cleaned_data["cisco_api_client_id"] != "" else "PlsChgMe"
                app_config.set_cisco_api_client_id(client_id)
                client_secret = form.cleaned_data["cisco_api_client_secret"] \
                    if form.cleaned_data["cisco_api_client_secret"] != "" else "PlsChgMe"
                app_config.set_cisco_api_client_secret(client_secret)

                if client_id != "PlsChgMe":
                    if settings.DEMO_MODE:
                        messages.success(request, "Successfully connected to the Cisco EoX API (Demo Mode)")
                    else:
                        result, message = test_cisco_eox_api_access(
                            form.cleaned_data["cisco_api_client_id"],
                            form.cleaned_data["cisco_api_client_secret"]
                        )

                        if result:
                            messages.success(request, "Successfully connected to the Cisco EoX API")

                        else:
                            messages.error(request, "Cannot contact the Cisco EoX API: %s" % message)

                else:
                    messages.info(
                        request,
                        "Please configure your Cisco API credentials within the Cisco API settings tab."
                    )

                app_config.set_cisco_eox_api_auto_sync_enabled(form.cleaned_data["eox_api_auto_sync_enabled"])
                app_config.set_auto_create_new_products(form.cleaned_data["eox_auto_sync_auto_create_elements"])
                app_config.set_cisco_eox_api_queries(form.cleaned_data["eox_api_queries"])
                app_config.set_product_blacklist_regex(form.cleaned_data["eox_api_blacklist"])

            app_config.write_file()

            # expire cached settings
            cache.delete("LOGIN_ONLY_MODE_SETTING")

            messages.success(request, "Settings saved successfully")
            return redirect(resolve_url("productdb_config:change_settings"))

    else:
        form = SettingsForm()
        form.fields['cisco_api_enabled'].initial = app_config.is_cisco_api_enabled()
        form.fields['login_only_mode'].initial = app_config.is_login_only_mode()
        form.fields['cisco_api_client_id'].initial = app_config.get_cisco_api_client_id()
        form.fields['cisco_api_client_secret'].initial = app_config.get_cisco_api_client_secret()
        form.fields['eox_api_auto_sync_enabled'].initial = app_config.is_cisco_eox_api_auto_sync_enabled()
        form.fields['eox_auto_sync_auto_create_elements'].initial = app_config.is_auto_create_new_products()
        form.fields['eox_api_queries'].initial = app_config.get_cisco_eox_api_queries()
        form.fields['eox_api_blacklist'].initial = app_config.get_product_blacklist_regex()

    context = {
        "form": form,
        "is_cisco_api_enabled": app_config.is_cisco_api_enabled(),
        "is_cisco_eox_api_auto_sync_enabled": app_config.is_cisco_eox_api_auto_sync_enabled()
    }
    return render(request, "config/change_configuration.html", context=context)


def server_messages_list(request):
    """
    show the server message log
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    context = {
        "recent_events": NotificationMessage.objects.all()
    }

    return render(request, "config/notification-list.html", context=context)


def server_message_detail(request, message_id):
    """
    show a detailed server message
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    try:
        context = {
            "message": NotificationMessage.objects.get(id=message_id)
        }

        return render(request, "config/notification-detail.html", context=context)

    except:
        raise Http404()
