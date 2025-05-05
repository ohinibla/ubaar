from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("check/", views.check_user_phonenumber, name="check"),
    path("login/", views.login_user, name="login_user"),
    path("register/<str:phonenumber>/", views.register_otp, name="register"),
    path("register_info/", views.register_info, name="register_info"),
    path("register_password/", views.register_password, name="register_password"),
]
