import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.template.defaultfilters import safe
from django.utils.html import escape
from django.utils.timezone import timedelta, datetime, get_current_timezone
from django.contrib import messages

from app.config.models import NotificationMessage, TextBlock
from app.productdb import utils as app_util
from app.productdb.forms import ImportProductsFileUploadForm, ProductListForm
from app.productdb.models import Product, JobFile, ProductGroup, ProductList
from app.productdb.models import Vendor
import app.productdb.tasks as tasks
from django_project.celery import set_meta_data_for_task

from django_project.utils import login_required_if_login_only_mode

logger = logging.getLogger(__name__)


def home(request):
    """view for the homepage of the Product DB

    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    today_date = datetime.now().date()

    context = {
        "recent_events": NotificationMessage.objects.filter(
            created__gte=datetime.now(get_current_timezone()) - timedelta(days=30)
        ).order_by('-created')[:5],
        "TB_HOMEPAGE_TEXT_BEFORE_FAVORITE_ACTIONS":
            TextBlock.objects.filter(name=TextBlock.TB_HOMEPAGE_TEXT_BEFORE_FAVORITE_ACTIONS).first(),
        "TB_HOMEPAGE_TEXT_AFTER_FAVORITE_ACTIONS":
            TextBlock.objects.filter(name=TextBlock.TB_HOMEPAGE_TEXT_AFTER_FAVORITE_ACTIONS).first(),
        "vendors": [x.name for x in Vendor.objects.all() if x.name != "unassigned"],
        "product_count": Product.objects.all().count(),
        "product_lifecycle_count": Product.objects.filter(eox_update_time_stamp__isnull=False).count(),
        "product_no_eol_announcement_count": Product.objects.filter(
            eox_update_time_stamp__isnull=False,
            eol_ext_announcement_date__isnull=True
        ).count(),
        "product_eol_announcement_count": Product.objects.filter(
            eol_ext_announcement_date__isnull=False,
            end_of_sale_date__gt=today_date
        ).count(),
        "product_eos_count": Product.objects.filter(
            Q(end_of_sale_date__lte=today_date, end_of_support_date__gt=today_date)|
            Q(end_of_sale_date__lte=today_date, end_of_support_date__isnull=True)
        ).count(),
        "product_eol_count": Product.objects.filter(
            end_of_support_date__lte=today_date
        ).count(),
        "product_price_count": Product.objects.filter(list_price__isnull=False).count(),
    }

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
    """
    browse all product groups in the database
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    return render(request, "productdb/product_group/list-product_groups.html", context={})


def list_product_lists(request):
    """
    browse all product lists in the database
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    context = {
        "product_lists": ProductList.objects.all()
    }

    return render(request, "productdb/product_list/list-product_list.html", context=context)


def detail_product_group(request, product_group_id=None):
    """
    detail view for a product group
    """
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
        "product_group": pg
    }

    return render(request, "productdb/product_group/detail-product_group.html", context=context)


def share_product_list(request, product_list_id):
    """
    public share link that doesn't require an authentication to view the Product List
    :param request:
    :param product_list_id:
    :return:
    """
    return detail_product_list(request, product_list_id, share_link=True)


def detail_product_list(request, product_list_id=None, share_link=False):
    """
    detail view for a product list
    :param request:
    :param product_list_id:
    :param share_link: will use a template that only shows the login link in the header
    :return:
    """
    if login_required_if_login_only_mode(request) and not share_link:
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    if not product_list_id:
        # view 404 if a share_link page should be rendered
        if share_link:
            raise Http404("Product List not found")

        # if product_id is set to none, redirect to the all products view
        return redirect(reverse("productdb:list-product_lists"))

    else:
        try:
            pl = ProductList.objects.get(id=product_list_id)

        except:
            raise Http404("Product List with ID %s not found in database" % product_list_id)

    # build share by email link content
    share_link_url = request.get_raw_uri().split("/productdb/")[0] + \
                     reverse("productdb:share-product_list", kwargs={"product_list_id": product_list_id})
    share_link_content = "?Subject=" + \
                         escape(pl.name + " - Product List") + \
                         "&body=" + \
                         escape("Hi,%%0D%%0Dplease take a look on the %s Product List:%%0D%%0D"
                                "%s%%0D%%0DThank you.%%0D%%0DKind Regards,%%0D%s" % (pl.name,
                                                                                     share_link_url,
                                                                                     "Henry"))

    context = {
        "product_list": pl,
        "export_description": pl.description.splitlines()[0] if len(pl.description.splitlines()) != 0 else "",
        "share_link_content": share_link_content,
        "share_link": False if request.user.is_authenticated() else share_link
    }

    return render(request, "productdb/product_list/detail-product_list.html", context=context)


def view_product_details(request, product_id=None):
    """
    view product details
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    if not product_id:
        # if product_id is set to none, redirect to the all products view
        return redirect(reverse("productdb:all_products"))

    else:
        try:
            p = Product.objects.get(id=product_id)
        except:
            raise Http404("Product with ID %s not found in database" % product_id)

    context = {
        "product": p
    }

    return render(request, "productdb/browse/product_detail.html", context=context)


def bulk_eol_check(request):
    """view that executes and handles the Bulk EoL check function

    :param request:
    :return:
    """
    if login_required_if_login_only_mode(request):
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

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

            # go through the database results
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
                    result_stats[element.product_id]['state'] = element.current_lifecycle_states

                # increment statistics
                else:
                    result_stats[element.product_id]['count'] += 1

            # classify the query results
            if (q_result_counter == 0) or found_but_no_eol_announcement:
                if (q_result_counter == 0) and not found_but_no_eol_announcement:
                    q_res_str = "Not found in database"

                if found_but_no_eol_announcement:
                    q_res_str = "no EoL announcement found"

                else:
                    # add queries without result to the stats and the counter
                    if query not in result_stats.keys():
                        result_stats[query] = dict()
                        result_stats[query]['state'] = ["Not found in database"]
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

    return render(request, "productdb/do/bulk_eol_check.html", context=context)


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
        "form": form
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

    context = {
        "product_list": pl,
        "form": form
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
    }

    return render(request, "productdb/product_list/delete-product_list.html", context=context)


@login_required()
@permission_required('productdb.change_product', raise_exception=True)
def import_products(request):
    """
    import of products using Excel
    :param request:
    :return:
    """
    context = {}
    if request.method == "POST":
        form = ImportProductsFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # file is valid, save and execute the import job
            job_file = JobFile(file=request.FILES['excel_file'])
            job_file.save()

            if request.user.is_superuser:
                # only the superuser is allowed to add a server notification message
                create_notification = not form.cleaned_data["suppress_notification"]

            else:
                # all other users are not allowed to add a server notification
                create_notification = False

            task = tasks.import_price_list.delay(
                job_file_id=job_file.id,
                create_notification_on_server=create_notification,
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
        form = ImportProductsFileUploadForm(initial={"suppress_notification": True})
        if not request.user.is_superuser:
            form.fields["suppress_notification"].disabled = True

    context['form'] = form

    return render(request, "productdb/import/import_products.html", context=context)
