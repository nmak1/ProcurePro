from django.urls import path
from .views import UserRegistrationView, UserProfileView, login_view

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('login/', login_view, name='login'),
]