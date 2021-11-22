from django.urls import path
from . import views
from django.contrib.auth import views as auth_view

urlpatterns = [
	path('', views.home, name='home'),
	path('upload', views.upload, name='upload'),
	path('indexsets', views.index_sets, name='indexsets'),
	path('indexsets/<str:index_set_name>/', views.index_detail, name='indexdetail'),
	path('worksheets/<slug:service_slug>', views.view_worksheets, name='view_worksheets'),
	path('worksheets/<slug:service_slug>/<slug:worksheet_id>/', views.view_worksheet_samples, name='view_worksheet_samples'
    ),
    path('ajax/load-indexes/', views.load_indexes, name='ajax_load_indexes'),
]