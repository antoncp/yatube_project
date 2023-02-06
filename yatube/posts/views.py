from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post

User = get_user_model()
NUM_POSTS_PER_PAGE = 10


def index(request):
    post_list = Post.objects.all()
    page_obj = make_pages(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = make_pages(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all().select_related('group')
    page_obj = make_pages(request, post_list)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def search(request):
    keyword = request.GET.get("q", None)
    if keyword:
        post_list = Post.objects.filter(text__iregex=keyword).select_related(
            'author', 'group')
        page_obj = make_pages(request, post_list)
    else:
        page_obj = None
    return render(request, "posts/search.html", {"page_obj": page_obj,
                                                 "keyword": keyword})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related(
            'author', 'group'), id=post_id)
    author = request.user.id == post.author.id
    context = {
        'post': post,
        'author': author,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


def make_pages(request, post_list, per_page=NUM_POSTS_PER_PAGE):
    """Split the QuerySet result to a pages with the specified number of posts
    per page. The number of posts per page could be provided during a function
    call. As a default the number of posts is taken from a constant
    NUM_POSTS_PER_PAGE. Returns page with a specified number of posts.
    """
    paginator = Paginator(post_list, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
