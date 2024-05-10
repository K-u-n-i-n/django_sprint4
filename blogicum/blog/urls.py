from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:category_slug>/',
         views.CategoryPostsView.as_view(), name='category_posts'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('create_post/', views.PostCreateView.as_view(), name='create_post'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('accounts/profile/', views.edit_profile, name='edit_profile'),
    path('posts/<int:pk>/comment/',
         views.AddCommentView.as_view(), name='add_comment'),
]
