from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Category


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


def index(request):
    post_list = get_published_posts()[:5]
    return render(request, 'blog/index.html', {'post_list': post_list})


def post_detail(request, id):
    post = get_object_or_404(get_published_posts(), id=id)
    return render(request, 'blog/detail.html', {'post': post})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    post_list = get_published_posts().filter(category=category)
    return render(request, 'blog/category.html',
                  {'post_list': post_list, 'category': category})


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    context = {
        'profile': profile,
    }
    return render(request, 'profile.html', context)
