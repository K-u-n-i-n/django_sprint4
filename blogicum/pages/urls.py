from django.conf.urls import handler404
from django.urls import path
from . import views

app_name = 'pages'
handler404 = 'pages.views.handler404'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('rules/', views.rules, name='rules'),
]
