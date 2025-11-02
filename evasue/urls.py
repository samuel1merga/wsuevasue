from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/manage-leaders/', views.manage_leaders, name='manage_leaders'),
    path('admin/create-team/', views.create_team, name='create_team'),
    path('admin/register-leader/', views.register_leader, name='register_leader'),
    path('admin/team/<int:team_id>/members/', views.admin_view_team_members, name='admin_view_team_members'),
   path('admin/manage-leaderss/', views.manage_leaders_to_remove, name='list_of_leaders'),
path('admin/remove-leader/<int:team_id>/<int:leader_id>/', views.remove_leaders, name='remove_leader'),

    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
   # path('register/team/<int:team_id>/', views.register_team, name='register_team'),
    path('create-admin/', views.create_admin, name='create_admin'),
    path('admin/create-team/', views.create_team, name='create_team'),

    path('member/dashboard/', views.member_dashboard, name='member_dashboard'),
    path('register/member/', views.register_member, name='register_member'),


    path('team/<int:team_id>/members/', views.view_team_members, name='view_team_members'),
    path('team/<int:team_id>/ajax-members/', views.ajax_search_team_members, name='ajax_search_team_members'),
    path('leader/member/<int:user_id>/', views.member_detail, name='member_detail'),

    path('leader/dashboard/', views.leader_dashboard, name='leader_dashboard'),
    #path('leader/approve/<int:request_id>/', views.approve_request, name='approve_request'),



path('leader/download/members/pdf/<int:team_id>/', views.download_team_members_by_batch_zip, name='download_team_members_pdf'),


    path('change-password/', views.custom_password_change, name='custom_password_change')

]