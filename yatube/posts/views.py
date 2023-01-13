from django.http import HttpResponse


def index(request):
    return HttpResponse('First main page')


def group_posts(request, slug):
    return HttpResponse(f'A post, written by {slug}')
