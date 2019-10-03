from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('run_analysis/<int:pk>/', views.view_run_analysis, name='view_run_analysis'),
]