"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from giftexchange import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('giftexchange/<int:giftexchange_id>/editdetails/', views.giftexchange_detail_edit, name='giftexchange_detail_edit'),
    path('giftexchange/<int:giftexchange_id>/manage/', views.giftexchange_manage_dashboard, name='giftexchange_manage_dashboard'),
    path('giftexchange/<int:giftexchange_id>/manage/editdetails/', views.giftexchange_manage_edit_details, name='giftexchange_manage_edit_details'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/', views.giftexchange_manage_assignments, name='giftexchange_manage_assignments'),
    path('giftexchange/<int:giftexchange_id>/manage/setassignments/', views.giftexchange_set_assignments, name='giftexchange_set_assignments'),
    path('giftexchange/<int:giftexchange_id>/manage/lockassignments/', views.giftexchange_toggle_assignment_lock, name='giftexchange_toggle_assignment_lock'),
    path('giftexchange/<int:giftexchange_id>/', views.giftexchange_detail, name='giftexchange_detail'),
    path('admin/', admin.site.urls),
]
