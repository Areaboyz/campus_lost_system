from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/administration/', views.administration_dashboard, name='administration_dashboard'),
    path('items/<int:pk>/toggle-resolution/', views.toggle_item_resolution, name='toggle_item_resolution'),
    path('items/', views.item_list, name='item_list'),
    path('items/report/', views.report_item, name='report_item'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('register/', views.register, name='register'), # <-- Add this line
]
