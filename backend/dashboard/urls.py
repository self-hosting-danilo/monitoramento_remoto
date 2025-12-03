from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/hospital-data/', views.hospital_data, name='hospital_data'),
]