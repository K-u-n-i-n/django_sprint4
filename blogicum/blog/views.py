from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse_lazy

from .forms import CommentForm, PostForm, UserProfileForm
from .models import Post, Category, Comment


@login_required
def simple_view(request):
    """
    Функция для отображения страницы только залогиненным пользователям.

    Аргументы:
        request: объект запроса Django.

    Возвращает:
        - HttpResponse с текстом 'Страница для залогиненных пользователей!'.

    Логика работы:
        - Проверяет, что пользователь авторизован.
        - Возвращает HttpResponse с сообщением о том, что это страница только для залогиненных пользователей.    
    """
    return HttpResponse('Страница для залогиненных пользователей!')


class OnlyAuthorMixin(UserPassesTestMixin):
    """ Проверяет, является ли текущий пользователь автором объекта."""

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostListView(ListView):
    """
    Класс представления для списка постов.

    Атрибуты:
        model: модель данных, используемая для отображения списка постов (Post).
        queryset: запрос к базе данных для получения только опубликованных постов с информацией об авторе.
        ordering: порядок сортировки постов по дате создания (убывающий).
        paginate_by: количество постов на одной странице пагинации.
        template_name: имя шаблона для отображения списка постов ('blog/index.html').
    """
    model = Post
    queryset = Post.objects.filter(is_published=True).select_related('author')
    ordering = '-created_at'
    paginate_by = 10
    template_name = 'blog/index.html'


class PostCreateView(CreateView):
    """
    Класс представления для создания нового поста.

    Атрибуты:
        model: модель данных, используемая для создания постов (Post).
        form_class: класс формы, используемый для ввода данных при создании поста (PostForm).
        template_name: имя шаблона для отображения формы создания поста ('blog/create.html').
        success_url: URL, на который будет перенаправлен пользователь после успешного создания поста ('blog:index').

    Методы:
        form_valid(self, form): метод, вызываемый при валидации формы. Устанавливает текущего пользователя как автора поста.
    """
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя как автора поста перед сохранением.

        Аргументы:
            form: экземпляр формы с данными о новом посте.

        Возвращает:
            Результат вызова метода form_valid родительского класса с переданным аргументом form.
        """
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    """
    Класс представления для обновления существующего поста.

    Наследует от класса OnlyAuthorMixin и UpdateView.

    Атрибуты:
        model: модель данных, используемая для обновления постов (Post).
        form_class: класс формы, используемый для ввода данных при обновлении поста (PostForm).

    """
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """
    Класс представления для удаления существующего поста.

    Наследует от класса LoginRequiredMixin и DeleteView.

    Атрибуты:
        model: модель данных, используемая для удаления постов (Post).
        success_url: URL, на который происходит перенаправление после успешного удаления поста.
    """
    model = Post
    success_url = reverse_lazy('index')


class PostDetailView(DetailView):
    """
    Класс представления для отображения детальной информации о посте.

    Наследует от класса DetailView.

    Атрибуты:
        model: модель данных, используемая для отображения информации о посте (Post).
    """
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        return context


class ProfileView(ListView):
    """
    Класс представления для отображения профиля пользователя и его постов.

    Наследует от класса ListView.

    Атрибуты:
        model: модель данных, используемая для отображения постов (Post).
        template_name: имя шаблона для отображения профиля пользователя и его постов.
        context_object_name: имя объекта контекста, содержащего список постов.
        paginate_by: количество постов на одной странице пагинации.

    Методы:
        get_queryset(self): метод, возвращающий список постов пользователя.
        get_context_data(self, **kwargs): метод, добавляющий дополнительные данные в контекст шаблона для отображения.
    """
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        """
        Возвращает список постов пользователя для отображения.

        Аргументы:
            self: экземпляр класса ProfileView.

        Возвращает:
            QuerySet с постами пользователя, отсортированными по дате создания.
        """
        username = self.kwargs['username']
        profile = get_object_or_404(User, username=username)
        posts = Post.objects.filter(
            author=profile, is_published=True).select_related('author')

        return posts.order_by('-created_at')

    def get_context_data(self, **kwargs):
        """
        Добавляет дополнительные данные в контекст шаблона для отображения.

        Аргументы:
            self: экземпляр класса ProfileView.
            **kwargs: дополнительные аргументы.

        Возвращает:
            Словарь с дополнительными данными для передачи в шаблон.
        """
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username'])
        return context


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(Category, slug=category_slug)
        return Post.objects.filter(category=category, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(Category, slug=category_slug)
        context['category'] = category
        return context


def edit_profile(request):
    """
    Функция для редактирования профиля пользователя.

    Аргументы:
        request: объект запроса Django.

    Возвращает:
        Если пользователь аутентифицирован:
            - Форму для редактирования профиля пользователя, отображенную на странице 'blog/user.html'.
        Если пользователь не аутентифицирован:
            - Страницу с сообщением 'Для доступа к этой странице необходимо войти в систему.'

    При отправке формы методом POST:
        - Проверяет валидность формы и сохраняет изменения.
        - Перенаправляет пользователя на страницу своего профиля.

    Используемые формы:
        - UserProfileForm: форма для редактирования профиля пользователя.

    Исключения:
        Нет обработки конкретных исключений.
    """
    if request.user.is_authenticated:
        user = request.user

        if request.method == 'POST':
            form = UserProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                return redirect('blog:profile', username=user.username)
        else:
            form = UserProfileForm(instance=user)

        context = {
            'form': form
        }

        return render(request, 'blog/user.html', context)
    else:
        return HttpResponse('Для доступа к этой странице необходимо войти в систему.')


class AddCommentView(View):

    """
    Класс для добавления комментария к посту.

    Атрибуты:
        - login_required: декоратор, требующий аутентификацию пользователя для доступа к методу post.

    Методы:
        post(self, request, pk):
            Метод для обработки POST запроса на добавление комментария.

            Аргументы:
                request: объект запроса Django.
                pk: идентификатор поста, к которому добавляется комментарий.

            Возвращает:
                - Перенаправляет пользователя на страницу с деталями поста, к которому был добавлен комментарий.

            Логика работы:
                - Получает пост по его идентификатору.
                - Создает форму для комментария на основе данных из POST запроса.
                - Если форма валидна:
                    - Сохраняет комментарий, указывая текущего пользователя как автора и связывая с постом.
                    - Перенаправляет пользователя на страницу с деталями поста.
                - Если форма не валидна:
                    - Перенаправляет пользователя на страницу с деталями поста.

            Используемые формы:
                - CommentForm: форма для добавления комментария.

            Исключения:
                Нет обработки конкретных исключений.
    """

    form_class = CommentForm
    template_name = 'comments.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            post_id = kwargs['pk']
            post = Post.objects.get(id=post_id)
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return render(request, 'comments.html', {'form': form, 'post': post})
        else:
            return render(request, 'comments.html', {'form': form})


class EditCommentView(LoginRequiredMixin, View):
    def get(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user == comment.author:
            form = CommentForm(instance=comment)
            context = {
                'user': request.user,
                'post_id': post_id,
                'comment_id': comment_id,
                'form': form
            }
            return render(request, 'edit_comment.html', context)
        else:
            return redirect('blog:comment_list', post_id)

    def post(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user == comment.author:
            form = CommentForm(request.POST, instance=comment)
            if form.is_valid():
                form.save()
            return redirect('blog:comment_list', post_id)
        else:
            return redirect('blog:comment_list', post_id)


class DeleteCommentView(LoginRequiredMixin, View):
    def get(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user == comment.author:
            comment.delete()
        return redirect('blog:comment_list', post_id)
