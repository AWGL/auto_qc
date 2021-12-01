from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='auto_qc/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='auto_qc/logout.html'), name='logout'),
    path('', views.home_auto_qc, name='home_auto_qc'),
    path('run_analysis/<int:pk>/', views.view_run_analysis, name='view_run_analysis'),
    path('archived/', views.view_archived_run_analysis, name='view_archived_run_analysis'),
    path('ngs_kpis/', views.ngs_kpis, name='ngs_kpis'),
    path('search/', views.search, name='search')
]