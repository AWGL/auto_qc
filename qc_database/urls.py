from django.urls import path
from . import views
from .views import RunAnalysisList, SampleAnalysisList
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='auto_qc/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='auto_qc/logout.html'), name='logout'),
    path('', views.home_auto_qc, name='home_auto_qc'),
    path('run_analysis/<int:pk>/', views.view_run_analysis, name='view_run_analysis'),
    path('archived/', views.view_archived_run_analysis, name='view_archived_run_analysis'),
    path('ngs_kpis/', views.ngs_kpis, name='ngs_kpis'),
    path('search/', views.search, name='search'),
    path('api/sample-analyses/', SampleAnalysisList.as_view(), name='all-sample-analyses'),
    path('api/sample-analyses/pipelines/<str:pipeline>/', SampleAnalysisList.as_view(), name='sample-analysis-by-pipeline'),
    path('api/sample-analyses/pipelines/<str:pipeline>/runs/<str:run>/', SampleAnalysisList.as_view(), name='sample-analysis-by-run'),
    path('api/sample-analyses/pipelines/<str:pipeline>/runs/<str:run>/samples/<str:sample>/', SampleAnalysisList.as_view(), name='sample-analysis-by-sample'),
    path('api/run-analyses/', RunAnalysisList.as_view(), name='run-analysis-list'),
    path('api/run-analyses/runs/<str:run>/', RunAnalysisList.as_view(), name='run-analysis-by-run'),
    path('get-available-data-models/', views.get_available_data_models, name='get_available_data_models'),
    path('downloader/', views.downloader, name='downloader'),
]
