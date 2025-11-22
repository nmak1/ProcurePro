from django.urls import path
from apps.users import views  # ← ИЗМЕНИТЕ ИМПОРТ

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.user_login, name='user-login'),
    path('logout/', views.user_logout, name='user-logout'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', views.UserUpdateView.as_view(), name='user-update'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('me/', views.user_info, name='user-info'),
]
