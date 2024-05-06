from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import Post, Category
from .forms import ProfileForm, PostForm


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
    return render(request, 'blog/profile.html', context)


def edit_profile(request):
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        profile = None

    # Создание формы с данными профиля пользователя
    form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile
    }
    return render(request, 'blog/user.html', context)


def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.pub_date = timezone.now()  # Установка текущей даты и времени
            post.save()
            return redirect('post_detail', id=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})
