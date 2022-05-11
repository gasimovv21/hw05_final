from django.core.paginator import Paginator
from django.conf import settings


def page_obj_func(request, post_list):
    paginator = Paginator(post_list, settings.MAX_POSTS)
    page_number = request.GET.get('page')
    paginator.get_page(page_number)

    return paginator.get_page(page_number)
