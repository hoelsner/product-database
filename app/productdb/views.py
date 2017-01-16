import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.template.defaultfilters import safe
from django.utils.html import escape
from django.utils.timezone import timedelta, datetime, get_current_timezone
from django.contrib import messages
from rest_framework.authtoken.models import Token
from django_project.celery import is_worker_active
from app.config.models import NotificationMessage, TextBlock
from app.productdb.forms import ImportProductsFileUploadForm, ProductListForm, UserProfileForm, \
    ImportProductMigrationFileUploadForm, ProductCheckForm
from app.productdb.models import Product, JobFile, ProductGroup, ProductList, UserProfile, ProductMigrationSource, \
    ProductCheck
from app.productdb.models import Vendor
import app.productdb.tasks as tasks
from django_project.celery import set_meta_data_for_task
from app.productdb.utils import login_required_if_login_only_mode

HOMEPAGE_CONTEXT_CACHE_KEY = "PDB_HOMEPAGE_CONTEXT"
logger = logging.getLogger(__name__)


def home(request):
    """view for the homepage of the Product DB
    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    # if the user is a super user, send a message if no backend worker process is running
    if request.user.is_authenticated() and request.user.is_superuser:
        if not is_worker_active():
            messages.add_message(
                request,
                level=messages.ERROR,
                message="No backend worker process is running on the server. Please check the state of the application."
            )

    today_date = datetime.now().date()

    context = cache.get(HOMEPAGE_CONTEXT_CACHE_KEY)
    if not context:
        all_products_query = Product.objects.all()
        context = {
            "recent_events": NotificationMessage.objects.filter(
                created__gte=datetime.now(get_current_timezone()) - timedelta(days=30)
            ).order_by('-created')[:5],
            "vendors": [x.name for x in Vendor.objects.all() if x.name != "unassigned"],
            "product_count": all_products_query.count(),
            "product_lifecycle_count": all_products_query.filter(eox_update_time_stamp__isnull=False).count(),
            "product_no_eol_announcement_count": all_products_query.filter(
                eox_update_time_stamp__isnull=False,
                eol_ext_announcement_date__isnull=True
            ).count(),
            "product_eol_announcement_count": all_products_query.filter(
                eol_ext_announcement_date__isnull=False,
                end_of_sale_date__gt=today_date
            ).count(),
            "product_eos_count": all_products_query.filter(
                Q(end_of_sale_date__lte=today_date, end_of_support_date__gt=today_date)|
                Q(end_of_sale_date__lte=today_date, end_of_support_date__isnull=True)
            ).count(),
            "product_eol_count": all_products_query.filter(
                end_of_support_date__lte=today_date
            ).count(),
            "product_price_count": all_products_query.filter(list_price__isnull=False).count(),
        }
        cache.set(HOMEPAGE_CONTEXT_CACHE_KEY, context, timeout=60*10)

    context.update({
        "TB_HOMEPAGE_TEXT_BEFORE_FAVORITE_ACTIONS":
            TextBlock.objects.filter(name=TextBlock.TB_HOMEPAGE_TEXT_BEFORE_FAVORITE_ACTIONS).first(),
        "TB_HOMEPAGE_TEXT_AFTER_FAVORITE_ACTIONS":
            TextBlock.objects.filter(name=TextBlock.TB_HOMEPAGE_TEXT_AFTER_FAVORITE_ACTIONS).first(),
    })

    return render(request, "productdb/home.html", context=context)


def about_view(request):
    """about view
    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    return render(request, "productdb/about.html", context={})


def browse_vendor_products(request):
    """Browse vendor specific products in the database
    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    context = {
        "vendors": Vendor.objects.all()
    }
    selected_vendor = 1  # use ID 1 by default

    if request.method == "POST":
        vendor_id_str = [str(e) for e in context["vendors"].values_list("id", flat=True)]
        if request.POST['vendor_selection'] in vendor_id_str:
            selected_vendor = request.POST['vendor_selection']

    else:
        if request.user.is_authenticated():
            selected_vendor = request.user.profile.preferred_vendor.id

    context['vendor_selection'] = selected_vendor

    return render(request, "productdb/browse/view_products_by_vendor.html", context=context)


def browse_all_products(request):
    """Browse all products in the database
    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    return render(request, "productdb/browse/view_products.html", context={})


def list_product_groups(request):
    """browse all product groups in the database"""
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    return render(request, "productdb/product_group/list-product_groups.html", context={})


def list_product_lists(request):
    """browse all product lists in the database"""
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    context = {
        "product_lists": ProductList.objects.all()
    }

    return render(request, "productdb/product_list/list-product_list.html", context=context)


def detail_product_group(request, product_group_id=None):
    """detail view for a product group"""
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    if not product_group_id:
        # if product_group_id is set to none, redirect to the all products groups view
        return redirect(reverse("productdb:list-product_groups"))

    else:
        try:
            pg = ProductGroup.objects.get(id=product_group_id)
        except:
            raise Http404("Product Group with ID %s not found in database" % product_group_id)

    context = {
        "product_group": pg,
        "back_to": request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:list-product_groups")
    }

    return render(request, "productdb/product_group/detail-product_group.html", context=context)


def share_product_list(request, product_list_id):
    """public share link that doesn't require an authentication to view the Product List
    :param request:
    :param product_list_id:
    :return:
    """
    return detail_product_list(request, product_list_id, share_link=True)


def detail_product_list(request, product_list_id=None, share_link=False):
    """detail view for a product list
    :param request:
    :param product_list_id:
    :param share_link: will use a template that only shows the login link in the header
    :return:
    """
    if login_required_if_login_only_mode(request) and not share_link:
        # redirect to the share link
        return redirect(reverse("productdb:share-product_list", kwargs={"product_list_id": product_list_id}))

    if not product_list_id:
        # if product_id is set to none, redirect to the all products view
        return redirect(reverse("productdb:list-product_lists"))

    else:
        try:
            pl = ProductList.objects.get(id=product_list_id)

        except:
            raise Http404("Product List with ID %s not found in database" % product_list_id)

    share_link_username = ""
    if request.user.is_authenticated():
        share_link_username = request.user.first_name

    # build share by email link content
    share_link_url = request.get_raw_uri().split("/productdb/")[0] + \
                     reverse("productdb:share-product_list", kwargs={"product_list_id": product_list_id})
    share_link_content = "?Subject=" + \
                         escape(pl.name + " - Product List") + \
                         "&body=" + \
                         escape("Hi,%%0D%%0Dplease take a look on the %s Product List:%%0D%%0D"
                                "%s%%0D%%0DThank you.%%0D%%0DKind regards,%%0D%s" % (pl.name,
                                                                                     share_link_url,
                                                                                     share_link_username))

    context = {
        "product_list": pl,
        "share_link_content": share_link_content,
        "share_link": False if request.user.is_authenticated() else share_link,
        "share_link_url": share_link_url,
        "back_to": request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:list-product_lists")
    }

    if pl.description:
        context["export_description"] = pl.description.splitlines()[0] if len(pl.description.splitlines()) != 0 else ""

    return render(request, "productdb/product_list/detail-product_list.html", context=context)


def view_product_details(request, product_id=None):
    """view product details"""
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    if not product_id:
        # if product_id is set to none, redirect to the all products view
        return redirect(reverse("productdb:all_products"))

    else:
        try:
            view_product = Product.objects.prefetch_related("productmigrationoption_set", "vendor").get(id=product_id)
        except:
            raise Http404("Product with ID %s not found in database" % product_id)

    # identify migration options and render to dictionary for template
    dict_preferred_replacement_option = None
    dict_migration_paths = {}

    if view_product.has_migration_options():
        db_preferred_replacement_option = view_product.get_preferred_replacement_option()
        valid_replacement_product = db_preferred_replacement_option.get_valid_replacement_product()
        dict_preferred_replacement_option = {
            "migration_source": db_preferred_replacement_option.migration_source.name,
            "migration_product_info_url": db_preferred_replacement_option.migration_product_info_url,
            "comment": db_preferred_replacement_option.comment,
            "replacement_product_id": db_preferred_replacement_option.replacement_product_id,
            "is_valid_replacement": db_preferred_replacement_option.is_valid_replacement(),
            "is_replacement_in_db": db_preferred_replacement_option.is_replacement_in_db(),
            "get_valid_replacement_product": valid_replacement_product.id if valid_replacement_product else None,
            "link_to_preferred_option": None,
        }
        if dict_preferred_replacement_option["is_valid_replacement"] and \
                dict_preferred_replacement_option["is_replacement_in_db"]:
            dict_preferred_replacement_option["link_to_preferred_option"] = reverse("productdb:product-detail", kwargs={
                "product_id": dict_preferred_replacement_option["get_valid_replacement_product"]
            })

    for migration_source_name in view_product.get_product_migration_source_names_set():
        db_migration_path = view_product.get_migration_path(migration_source_name)
        dict_migration_paths[migration_source_name] = []
        for pmo in db_migration_path:
            dict_migration_paths[migration_source_name].append({
                "replacement_product_id": pmo.replacement_product_id,
                "is_replacement_in_db": pmo.is_replacement_in_db(),
                "get_product_replacement_id": pmo.get_product_replacement_id(),
                "comment": pmo.comment,
                "migration_product_info_url": pmo.migration_product_info_url,
                "is_valid_replacement": pmo.is_valid_replacement(),
            })

    dict_migration_source_details = {}
    for e in ProductMigrationSource.objects.all():
        dict_migration_source_details[e.name] = {
            "description": e.description,
            "preference": e.preference
        }

    # process migration paths for the template
    context = {
        "product": view_product,
        "preferred_replacement_option": dict_preferred_replacement_option,
        "migration_paths": dict_migration_paths,
        "migration_source_details": dict_migration_source_details,
        "back_to": request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:all_products")
    }

    return render(request, "productdb/browse/product_detail.html", context=context)


def list_product_checks(request):
    """
    list all Product Checks that are available for the current user
    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    product_checks = ProductCheck.objects.filter(
        Q(create_user__isnull=True)|
        Q(create_user__username=request.user.username)
    ).prefetch_related("productcheckentry_set", "productcheckentry_set__product_in_database")

    return render(request, "productdb/product_check/list-product_check.html", context={
        "product_checks": product_checks
    })


def detail_product_check(request, product_check_id):
    """
    detail view of a Product Check
    :param request:
    :param product_check_id:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    product_check = ProductCheck.objects.filter(id=product_check_id).prefetch_related(
        "productcheckentry_set",
        "productcheckentry_set__product_in_database",
        "productcheckentry_set__migration_product",
    ).first()

    if product_check is None:
        raise Http404("Product check with ID %s not found in database" % product_check_id)

    # if the product check is in progress, redirect to task-watch page
    if product_check.in_progress:
        return redirect(reverse("task_in_progress", kwargs={"task_id": product_check.task_id}))

    return render(request, "productdb/product_check/detail-product_check.html", context={
        "product_check": product_check,
        "back_to": request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:list-product_checks")
    })


def create_product_check(request):
    """
    create a Product Check and schedule task
    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    if request.method == "POST":
        form = ProductCheckForm(request.POST)

        if form.is_valid():
            if form.cleaned_data["public_product_check"]:
                form.instance.create_user = None

            form.save()

            # dispatch task
            task = tasks.perform_product_check.delay(form.instance.id)
            set_meta_data_for_task(
                task_id=task.id,
                title="Product check",
                auto_redirect=True,
                redirect_to=reverse("productdb:detail-product_check", kwargs={
                    "product_check_id": form.instance.id
                })
            )
            logger.info("create product check with ID %d on task %s" % (form.instance.id, task.id))

            return redirect(reverse("task_in_progress", kwargs={"task_id": task.id}))

    else:
        form = ProductCheckForm(initial={
            "create_user": request.user.id,
            "public_product_check": False if request.user.id else True
        })

        # if user is not logged in, create always a public check
        if not request.user.id:
            form.fields["public_product_check"].widget.attrs['disabled'] = True

    choose_migration_source = request.user.profile.choose_migration_source if request.user.is_authenticated() else False

    worker_is_active = is_worker_active()

    if getattr(settings, "CELERY_ALWAYS_EAGER", False):
        # if celery always eager is enabled, it works without worker
        worker_is_active = True

    return render(request, "productdb/product_check/create-product_check.html", context={
        "form": form,
        "choose_migration_source": choose_migration_source,
        "worker_is_active": worker_is_active
    })


@login_required()
@permission_required("productdb.add_productlist", raise_exception=True)
def add_product_list(request):
    if request.method == "POST":
        form = ProductListForm(request.POST)
        if form.is_valid():
            pl = form.save(commit=False)
            pl.update_user = request.user
            pl.save()
            return redirect(reverse("productdb:list-product_lists"))

    else:
        form = ProductListForm()

    context = {
        "form": form,
        "back_to": request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:list-product_lists")
    }

    return render(request, "productdb/product_list/add-product_list.html", context=context)


@login_required()
@permission_required("productdb.change_productlist", raise_exception=True)
def edit_product_list(request, product_list_id=None):
    pl = get_object_or_404(ProductList, id=product_list_id)

    if pl.update_user != request.user:
        messages.add_message(
            request,
            level=messages.WARNING,
            message="You are not allowed to change this Product List. Only the "
                    "original Author is allowed to perform this action."
        )

    if request.method == "POST":
        form = ProductListForm(request.POST, instance=pl)
        if pl.update_user != request.user:
            messages.add_message(
                request,
                level=messages.ERROR,
                message="You are not allowed to change this Product List. Only the "
                        "original Author is allowed to perform this action."
            )

        elif form.is_valid():
            pl = form.save(commit=False)
            pl.update_user = request.user
            pl.save()
            return redirect(reverse("productdb:list-product_lists"))

    else:
        form = ProductListForm(instance=pl)

    default_back_to = reverse("productdb:detail-product_list", kwargs={"product_list_id": product_list_id})
    back_to = request.GET.get("back_to") if request.GET.get("back_to") else default_back_to
    context = {
        "product_list": pl,
        "form": form,
        "back_to": back_to
    }

    return render(request, "productdb/product_list/edit-product_list.html", context=context)


@login_required()
@permission_required("productdb.delete_productlist", raise_exception=True)
def delete_product_list(request, product_list_id=None):
    pl = get_object_or_404(ProductList, id=product_list_id)

    if request.method == "POST":
        if pl.update_user != request.user:
            messages.add_message(
                request,
                level=messages.ERROR,
                message="You are not allowed to change this Product List. Only the "
                        "original Author is allowed to perform this action."
            )

        elif request.POST.get("really_delete"):
            pl.delete()
            messages.add_message(
                request,
                level=messages.INFO,
                message=safe("Product List <strong>%s</strong> successfully deleted." % pl.name)
            )
            return redirect(reverse("productdb:list-product_lists"))

    if pl.update_user != request.user:
        messages.add_message(
            request,
            level=messages.WARNING,
            message="You are not allowed to change this Product List. Only the "
                    "original Author is allowed to perform this action."
        )
    else:
        messages.add_message(request, level=messages.ERROR, message="Be careful, this action cannot be undone!")

    context = {
        "product_list": pl,
        "back_to": request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:list-product_lists")
    }

    return render(request, "productdb/product_list/delete-product_list.html", context=context)


@login_required()
@permission_required('productdb.change_product', raise_exception=True)
def import_products(request):
    """import of products using Excel
    :param request:
    :return:
    """
    context = {}
    if request.method == "POST":
        form = ImportProductsFileUploadForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            # file is valid, save and execute the import job
            job_file = JobFile(file=request.FILES['excel_file'])
            job_file.save()

            task = tasks.import_price_list.delay(
                job_file_id=job_file.id,
                create_notification_on_server=not form.cleaned_data["suppress_notification"],
                update_only=form.cleaned_data["update_existing_products_only"],
                user_for_revision=request.user.username
            )
            set_meta_data_for_task(
                task_id=task.id,
                title="Import products from Excel sheet",
                auto_redirect=False,
                redirect_to=reverse("productdb:import_products")
            )

            return redirect(reverse("task_in_progress", kwargs={"task_id": task.id}))

    else:
        form = ImportProductsFileUploadForm(request.user)

    context['form'] = form

    return render(request, "productdb/import/import_products.html", context=context)


@login_required()
@permission_required('productdb.change_productmigrationoption', raise_exception=True)
def import_product_migrations(request):
    context = {}
    if request.method == "POST":
        form = ImportProductMigrationFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # file is valid, save and execute the import job
            job_file = JobFile(file=request.FILES['excel_file'])
            job_file.save()

            task = tasks.import_product_migrations.delay(
                job_file_id=job_file.id,
                user_for_revision=request.user.username
            )
            set_meta_data_for_task(
                task_id=task.id,
                title="Import product migrations from Excel sheet",
                auto_redirect=False,
                redirect_to=reverse("productdb:import_product_migrations")
            )

            return redirect(reverse("task_in_progress", kwargs={"task_id": task.id}))

    else:
        form = ImportProductMigrationFileUploadForm()

    context["form"] = form

    return render(request, "productdb/import/import_product_migrations.html", context=context)


@login_required()
def edit_user_profile(request):
    up, _ = UserProfile.objects.get_or_create(user=request.user)
    back_to = request.GET.get("back_to") if request.GET.get("back_to") else reverse("productdb:home")

    if request.method == "POST":
        form = UserProfileForm(request.user, request.POST, instance=up)

        if form.is_valid():
            form.save()

            request.user.email = form.cleaned_data.get("email")
            request.user.save()

            messages.add_message(request, messages.INFO, "User Profile successful updated")

            return redirect(back_to)

    else:
        form = UserProfileForm(request.user, instance=up)

    token, _ = Token.objects.get_or_create(user=request.user)

    context = {
        "form": form,
        "back_to": back_to,
        "api_auth_token": token
    }

    return render(request, "productdb/user_profile/edit-user_profile.html", context=context)
