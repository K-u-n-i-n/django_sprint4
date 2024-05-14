from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied

from .forms import CommentForm, PostForm, UserProfileForm
from .models import Post, Category, Comment


# @login_required
# def simple_view(request):
#     """
#     Функция для отображения страницы только залогиненным пользователям.
#     """
#     return HttpResponse('Страница для залогиненных пользователей!')


# class OnlyAuthorMixin(UserPassesTestMixin):
#     """ Проверяет, является ли текущий пользователь автором объекта."""

#     def test_func(self):
#         object = self.get_object()
#         return object.author == self.request.user


class PostListView(ListView):
    """
    Класс представления для списка постов.

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

    """
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    login_url = '/login/'

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя как автора поста перед сохранением.

        """
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # Получаем username из объекта пользователя, связанного с созданным постом
        username = self.object.author.username
        # Возвращаем URL для перехода на страницу профиля пользователя
        return reverse('blog:profile', args=[username])


class PostUpdateView(UpdateView):
    """
    Класс для редактирования поста.
    """
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def test_func(self):
        self.object = self.get_object()
        return self.request.user.is_authenticated and self.object.author == self.request.user

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            return redirect(reverse('blog:post_detail', kwargs={'post_id': self.kwargs['pk']}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)


class PostDetailView(DetailView):
    """
    Класс представления для отображения детальной информации о посте.
    """
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        # Получаем ID поста из параметров URL
        post_id = self.kwargs.get('post_id')
        # Ищем пост по ID с дополнительным условием для времени публикации
        post = get_object_or_404(Post, id=post_id)

        # Проверяем, является ли текущий пользователь автором поста или
        # пост опубликован и категория опубликована, и дата публикации меньше или равна текущему времени
        if (post.author == self.request.user
                or (post.is_published and post.category.is_published and post.pub_date <= timezone.now())):
            return post

        # Если условия не выполняются, выбрасываем ошибку 404
        raise Http404("You do not have permission to view this post.")

    # # данный код позволяет получить объект поста на основе переданного идентификатора
    # def get_object(self, queryset=None):
    #     post_id = self.kwargs.get('post_id')
    #     return get_object_or_404(Post, id=post_id)

    # def dispatch(self, request, *args, **kwargs):
    #     post = self.get_object()
    #     category = post.category

    #     if (post.is_published and category.is_published) or post.author == self.request.user:
    #         self.queryset = Post.objects
    #         return super().dispatch(request, *args, **kwargs)

    #     raise Http404

    def get_context_data(self, **kwargs):
        '''данный метод добавляет в контекст данные о посте,
          форму для добавления комментариев и список комментариев,
            которые будут использоваться при отображении страницы.'''
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        comments = post.comments.all().order_by('created_at')
        context['form'] = CommentForm()
        context['comments'] = comments

        return context


class ProfileView(ListView):
    """
    Класс представления для отображения профиля пользователя и его постов.

    """
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        """
        Возвращает список постов пользователя для отображения.

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


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'comments.html'
   
    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'post_id': post_id})

    def form_valid(self, form):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)





    # def get_object(self):
    #     if not hasattr(self, '_post'):
    #         post_id = self.kwargs.get('post_id')
    #         self._post = get_object_or_404(Post, id=post_id)
    #     return self._post

    # def get(self, request, *args, **kwargs):
    #     post = self.get_object()
    #     form = self.form_class()
    #     comments = post.comments.all()
    #     return render(request, self.template_name, {'form': form, 'post': post, 'comments': comments})

    # def post(self, request, *args, **kwargs):
    #     form = self.form_class(request.POST)
    #     if form.is_valid():
    #         post = self.get_object()
    #         comment = form.save(commit=False)
    #         comment.author = request.user
    #         comment.post = post
    #         comment.save()
    #         return redirect('blog:post_detail', pk=post.id)
    #     else:
    #         return render(request, self.template_name, {'form': form})


class EditCommentView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        # Вы можете добавить здесь любую предварительную логику
        self.object = self.get_object()
        if self.object.author != request.user:
            raise Http404("Вы не авторизованы для удаления этого комментария.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        comment_id = self.kwargs.get('comment_id')
        # Используем get_object_or_404 для корректной обработки отсутствующих объектов
        return get_object_or_404(Comment, id=comment_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_id'] = self.kwargs.get('post_id')
        return context


class DeleteCommentView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'  # Используем ваш общий шаблон
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        # Вы можете добавить здесь любую предварительную логику
        self.object = self.get_object()
        if self.object.author != request.user:
            raise Http404("Вы не авторизованы для удаления этого комментария.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def get_object(self, queryset=None):
        """ Переопределяем метод для проверки прав пользователя. """
        obj = super().get_object(queryset)
        return obj

    def post(self, request, *args, **kwargs):
        # Обработка POST запроса, который подтверждает удаление
        return self.delete(request, *args, **kwargs)
