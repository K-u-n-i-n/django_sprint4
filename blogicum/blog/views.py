from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy

from .forms import CommentForm, PostForm, ProfileForm
from .models import Post, Profile


@login_required
def simple_view(request):
    return HttpResponse('Страница для залогиненных пользователей!')


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostListView(ListView):
    model = Post
    queryset = Post.objects.filter(is_published=True).select_related('author')
    ordering = '-created_at'
    paginate_by = 10
    template_name = 'blog/index.html'


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('index')


class PostDetailView(DetailView):
    model = Post


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs['username']
        profile = get_object_or_404(User, username=username)
        return Post.objects.filter(author=profile, is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username'])
        return context


def category_posts(request, category):
    posts = Post.objects.filter(category=category, is_published=True)
    return render(request, 'blog/category_posts.html', {'posts': posts, 'category': category})


def edit_profile(request):
    if request.user.is_authenticated:
        user_profile, created = Profile.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            form = ProfileForm(request.POST, instance=user_profile)
            if form.is_valid():
                form.save()
                return redirect('blog:profile', username=request.user.username)  # Передаем имя пользователя при перенаправлении
        else:
            form = ProfileForm(instance=user_profile)

        return render(request, 'blog/user.html', {'form': form})
    else:
        return redirect('login')  # Перенаправляем на страницу входа, если пользователь не авторизован


class AddCommentView(View):
    @login_required
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)

        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()

            return redirect('post_detail', pk=pk)

        return redirect('post_detail', pk=pk)
