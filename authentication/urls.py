from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView

from . import profile_views
from .views import register, UserLoginView

app_name = 'authentication'
urlpatterns = [
    path('register/', register, name='register'),
    path('register/complete/', TemplateView.as_view(
        template_name='authentication/registration_complete.html'
    ), name='registration_complete'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('profil/', profile_views.profile_detail, name='profile'),
    path('profil/edit/', profile_views.profile_update, name='profile_update'),
    path('profil/hapus/', profile_views.profile_delete, name='profile_delete'),
    path('pengguna/', profile_views.user_list, name='user_list'),
    path('pengguna/<str:username>/', profile_views.user_detail, name='user_detail'),

    path('api/profil/', profile_views.profile_json, name='profile_json'),
    path('api/pengguna/', profile_views.user_list_json, name='user_list_json'),
    path('api/pengguna/<str:username>/', profile_views.user_detail_json, name='user_detail_json'),
]
