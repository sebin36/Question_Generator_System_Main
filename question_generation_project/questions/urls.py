from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),  # Welcome page
    path('register/', views.register, name='register'),  # Register page
    path('login/', views.user_login, name='login'),  # Login page
    path('generate-questions/', views.generate_questions, name='generate_questions'),  # Question generation page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('view-history/', views.view_history, name='view_history'),
    path('history/<int:history_id>/', views.history_detail, name='history_detail'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile-details/', views.profile_details, name='profile_details'),
    path('update-profile/', views.update_profile, name='update_profile'),
]
