from django.core.paginator import Paginator


ITEMS_PER_PAGE = 10


def pagination(request, posts):
    paginator = Paginator(posts, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
