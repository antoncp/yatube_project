from django.shortcuts import render, get_object_or_404
from .models import Post, Group

NUM_POSTS_PER_PAGE = 10


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()[:NUM_POSTS_PER_PAGE]
    context = {
        'posts': posts,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:NUM_POSTS_PER_PAGE]
    context = {
        'group': group,
        'posts': posts,
    }
    return render(request, template, context)


def search(request):
    keyword = request.GET.get("q", None)
    if keyword:
        posts = Post.objects.filter(text__iregex=keyword).select_related(
            'author', 'group')
    else:
        posts = None
    return render(request, "posts/search.html", {"posts": posts,
                                                 "keyword": keyword})
