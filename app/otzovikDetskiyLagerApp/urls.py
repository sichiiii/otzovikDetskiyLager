from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/expert/', views.register_expert, name='register_expert'),
    path('register/participant/', views.register_participant, name='register_participant'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cabinet/participant/', views.participant_cabinet, name='participant_cabinet'),
    path('cabinet/expert/', views.expert_cabinet, name='expert_cabinet'),
    path('cabinet/organizer/', views.organizer_cabinet, name='organizer_cabinet'),
    path('cabinet/organizer/download/all/', views.download_all_zip, name='download_all_zip'),
    path('cabinet/organizer/download/<str:game_type>/<str:game_name>/', views.download_game_zip, name='download_game_zip'),
    path('cabinet/participant/delete_file/', views.delete_participant_file, name='delete_participant_file'),
    path('cabinet/expert/delete_file/', views.delete_expert_file, name='delete_expert_file'),
]