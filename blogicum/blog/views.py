from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse_lazy, reverse

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
    queryset = Post.objects.filter(is_published=True, pub_date__lte=timezone.now(
    )).select_related('author').prefetch_related('category', 'location')
    ordering = '-pub_date'
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        posts = super().get_queryset().annotate(comment_count=Count('comments'))
        posts = posts.filter(category__is_published=True)
        return posts


class PostCreateView(LoginRequiredMixin, CreateView):
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

    login_url = '/login/'

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

    def get_success_url(self):
        # Получаем username из объекта пользователя, связанного с созданным постом
        username = self.object.author.username
        # Возвращаем URL для перехода на страницу профиля пользователя
        return reverse('blog:profile', args=[username])


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
    model = Post
    template_name = 'blog/create.html'  # Указываем шаблон для использования
    # Убедитесь, что это правильный путь
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'  # Указываем, что pk это 'post_id' из URL

    def get_queryset(self):
        """
        Этот метод уточняет, что пользователь может удалять только свои посты.
        """
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)


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
        post = self.get_object()
        # Сортировка комментариев по времени публикации
        comments = post.comments.all().order_by('created_at')
        context['form'] = CommentForm()
        context['comments'] = comments

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
        posts = Post.objects.filter(author=profile).select_related(
            'author').prefetch_related('comments', 'category', 'location')

        posts_annotated = posts.annotate(comment_count=Count('comments'))

        return posts_annotated.order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'profile' not in context:
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
        category = get_object_or_404(
            Category, slug=category_slug, is_published=True)

        if not category.is_published:
            raise Http404("Категория не найдена")

        posts = Post.objects.filter(
            category=category, is_published=True, pub_date__lte=timezone.now()).annotate(
            comment_count=Count('comments')).order_by('-pub_date')
        return posts

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


class AddCommentView(OnlyAuthorMixin, View):
    form_class = CommentForm
    template_name = 'comments.html'

    def get_object(self):
        if not hasattr(self, '_post'):
            post_id = self.kwargs.get('post_id')
            self._post = get_object_or_404(Post, id=post_id)
        return self._post

    def get(self, request, *args, **kwargs):
        post = self.get_object()
        form = self.form_class()
        comments = post.comments.all()
        return render(request, self.template_name, {'form': form, 'post': post, 'comments': comments})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            post = self.get_object()
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', pk=post.id)
        else:
            return render(request, self.template_name, {'form': form})


class EditCommentView(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        comment_id = self.kwargs.get('comment_id')
        return Comment.objects.get(id=comment_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_id'] = self.kwargs.get('post_id')
        return context


class DeleteCommentView(LoginRequiredMixin, View):
    def get(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user == comment.author:
            comment.delete()
        return redirect('blog:post_detail', pk=post_id)
