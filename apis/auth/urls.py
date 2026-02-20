# apis/auth/urls.py
from django.urls import path
from .views import LoginView, LogoutView, CheckAuthView, UserInfoView

app_name = 'auth'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('check/', CheckAuthView.as_view(), name='check-auth'),
    path('me/', UserInfoView.as_view(), name='user-info'),
]