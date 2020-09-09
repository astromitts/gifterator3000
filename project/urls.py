"""project URL Configuration
"""
from django.contrib import admin
from django.urls import path
from giftexchange.views import app_views
from giftexchange.views import session_views
from giftexchange.views import admin_views

urlpatterns = [
    path('', app_views.Dashboard.as_view(), name='dashboard'),
    path('login/', session_views.LoginHandler.as_view(), name='login'),
    path('register/', session_views.RegistrationHandler.as_view(), name='register'),
    path('logout/', session_views.logout_handler, name='logout'),
    path('profile/', app_views.ManageProfile.as_view(), name='profile'),
    path('profile/reset-password/', session_views.ResetPassword.as_view(), name='reset_password'),  # Forced password update
    path('profile/change-password/', session_views.ChangePassword.as_view(), name='change_password'),  # logged in user optional password update
    path('giftexchange/create/', app_views.CreateGiftExchange.as_view(), name='giftexchange_create_new'),
    path('giftexchange/<int:giftexchange_id>/editdetails/', app_views.GiftExchangePersonalDetailEdit.as_view(), name='giftexchange_detail_edit'),
    path('giftexchange/<int:giftexchange_id>/manage/', admin_views.GiftExchangeAdminDetail.as_view(), name='giftexchange_manage_dashboard'),
    path('giftexchange/<int:giftexchange_id>/manage/editdetails/', admin_views.GiftExchangeEdit.as_view(), name='giftexchange_manage_edit_details'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/', admin_views.ParticipantsList.as_view(), name='giftexchange_manage_participants'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/upload/', admin_views.ParticipantUpload.as_view(), name='giftexchange_upload_participants'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/search/', admin_views.ParticipantsSearch.as_view(), name='giftexchange_search_participants'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/search/invite/', admin_views.ParticipantsAddFromSearch.as_view(), name='giftexchange_invite_from_search'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/invite/', admin_views.InviteNewUser.as_view(), name='giftexchange_invite_new_user'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/<int:participant_id>/remove/', admin_views.RemoveParticipant.as_view(), name='giftexchange_remove_participant'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/<int:participant_id>/addadmin/', admin_views.SetParticipantAdmin.as_view(), name='giftexchange_add_participant_admin'),
    path('giftexchange/<int:giftexchange_id>/manage/participants/<int:participant_id>/removeadmin/', admin_views.UnsetParticipantAdmin.as_view(), name='giftexchange_remove_participant_admin'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/', admin_views.ViewAssignments.as_view(), name='giftexchange_manage_assignments'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/set/', admin_views.SetAssigments.as_view(), name='giftexchange_set_assignments'),
    path('giftexchange/<int:giftexchange_id>/manage/assignments/toggle-lock/', admin_views.ToggleAssignmentLock.as_view(), name='giftexchange_toggle_assignment_lock'),
    path('giftexchange/<int:giftexchange_id>/', app_views.GiftExchangePersonalDetail.as_view(), name='giftexchange_detail'),
    path('giftexchange/<int:giftexchange_id>/setgift/', app_views.GiftExchangeSetGift.as_view(), name='giftexchange_set_gift'),
    path('giftexchange/<int:giftexchange_id>/setgift/<int:appuser_id>/', app_views.GiftExchangeSetGift.as_view(), name='giftexchange_set_gift_for_user'),
    path('giftexchange/<int:giftexchange_id>/review/', app_views.GiftExchangeDetailResult.as_view(), name='giftexchange_detail_review'),
    path('giftexchange/<int:giftexchange_id>/accept/', app_views.AcceptGiftExchangeInvitation.as_view(), name='giftexchange_invitation_accept'),
    path('giftexchange/<int:giftexchange_id>/decline/', app_views.DeclineGiftExchangeInvitation.as_view(), name='giftexchange_invitation_decline'),
    path('giftexchange/<int:giftexchange_id>/userdetails/<int:appuser_id>/', app_views.GiftExchangePersonalDetail.as_view(), name='giftexchange_detail_appuser'),
    path('admin/', admin.site.urls),
]
