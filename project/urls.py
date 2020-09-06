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
    path('', views.Dashboard.as_view(), name='dashboard'),
    path('login/', views.login_handler, name='login'),
    path('logout/', views.logout_handler, name='logout'),
    path('giftexchange/create/', views.CreateGiftExchange.as_view(), name='giftexchange_create_new'),
    path('giftexchange/<int:giftexchange_id>/editdetails/', views.GiftExchangeDetailEdit.as_view(), name='giftexchange_detail_edit'),
    path('giftexchange/<int:giftexchange_id>/manage/', views.GiftExchangeAdminDetail.as_view(), name='giftexchange_manage_dashboard'),
    path('giftexchange/<int:giftexchange_id>/manage/editdetails/', views.GiftExchangeEdit.as_view(), name='giftexchange_manage_edit_details'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/', views.ParticipantsList.as_view(), name='giftexchange_manage_participants'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/upload/', views.ParticipantUpload.as_view(), name='giftexchange_upload_participants'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/<int:participant_id>/remove/', views.RemoveParticipant.as_view(), name='giftexchange_remove_participant'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/<int:participant_id>/addadmin/', views.SetParticipantAdmin.as_view(), name='giftexchange_add_participant_admin'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/<int:participant_id>/removeadmin/', views.UnsetParticipantAdmin.as_view(), name='giftexchange_remove_participant_admin'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/', views.ViewAssignments.as_view(), name='giftexchange_manage_assignments'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/set/', views.SetAssigments.as_view(), name='giftexchange_set_assignments'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/toggle-lock/', views.ToggleAssignmentLock.as_view(), name='giftexchange_toggle_assignment_lock'),
    path('giftexchange/<int:giftexchange_id>/', views.GiftExchangeDetail.as_view(), name='giftexchange_detail'),
    path('giftexchange/<int:giftexchange_id>/userdetails/<int:appuser_id>/', views.GiftExchangeDetail.as_view(), name='giftexchange_detail_appuser'),
    path('admin/', admin.site.urls),
]
