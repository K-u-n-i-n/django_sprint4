from django.urls import path
from . import views


app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:id>/', views.post_detail, name='post_detail'),
    path('category/<slug:category_slug>/',
         views.category_posts, name='category_posts'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('create_post/', views.create_post, name='create_post'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('accounts/profile/', views.edit_profile, name='edit_profile'),

]
