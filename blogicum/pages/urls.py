from django.urls import path
from . import views

app_name = 'pages'
handler404 = 'pages.views.page_not_found'

urlpatterns = [
    path('about/', views.AboutView.as_view(), name='about'),
    path('rules/', views.RulesView.as_view(), name='rules'),
]
