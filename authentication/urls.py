from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView

from .views import register, UserLoginView

app_name = 'authentication'
urlpatterns = [
    path('register/', register, name='register'),
    path('register/complete/', TemplateView.as_view(
        template_name='authentication/registration_complete.html'
    ), name='registration_complete'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
