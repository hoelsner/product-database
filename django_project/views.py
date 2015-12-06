from django.shortcuts import render_to_response
from django.template import RequestContext


def custom_page_not_found_view(request):
    response = render_to_response('django_project/custom_404_page.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def custom_error_view(request):
    response = render_to_response('django_project/custom_500_page.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


def custom_bad_request_view(request):
    response = render_to_response('django_project/custom_400_page.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 400
    return response


def custom_permission_denied_view(request):
    response = render_to_response('django_project/custom_400_page.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 403
    return response
