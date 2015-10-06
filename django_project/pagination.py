from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math


class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        used_page_size = int(self.request.GET.get('page_size', self.page_size))
        if self.page.paginator.count / used_page_size <= 1:
            last_page_index = 1
        else:
            last_page_index = math.ceil(self.page.paginator.count / used_page_size)

        result = {
            'pagination': {
                'total_records': self.page.paginator.count,
                'page_records': len(data),
                'page': int(self.request.GET.get('page', 1)),
                'last_page': last_page_index,
                'url': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                }
            },
            'data': data
        }

        return Response(result)
