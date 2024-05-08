from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post, Category
from .forms import ProfileForm, PostForm


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


def index(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)  # Передаем request.FILES в аргумент files
        if form.is_valid():
            # Обработка валидной формы
            form.save()
            return redirect('success_url')  # Перенаправление на страницу успешного сохранения
    else:
        form = PostForm()  # Инициализация формы без данных

    posts = get_published_posts().order_by('-pub_date')
    paginator = Paginator(posts, 10)  # Показывать по 10 постов на странице
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    return render(request, 'blog/index.html', {'form': form, 'page_obj': page_obj})


def post_detail(request, id):
    post = get_object_or_404(get_published_posts(), id=id)
    return render(request, 'blog/detail.html', {'post': post})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    post_list = get_published_posts().filter(category=category)

    paginator = Paginator(post_list, 10)  # Показывать по 10 постов на странице
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    return render(request, 'blog/category.html', {'category': category, 'page_obj': page_obj})


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=profile, is_published=True)

    # Показывать по 10 публикаций на странице
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'profile': profile,
        'page_obj': page_obj,
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


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # Установка текущего пользователя как автора
            post.pub_date = timezone.now()  # Установка текущей даты и времени
            post.save()            
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})
