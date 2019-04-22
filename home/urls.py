from django.urls import path, include
from . import views as manual_views
from django.contrib.auth import views
from . import forms
from django.contrib.auth.forms import PasswordChangeForm

urlpatterns = [
	path('', manual_views.home),
	path('login/', views.LoginView.as_view(), {'template_name':'registration/login.html','authentication_form':forms.LoginForm}),
	path('logout/', views.LogoutView.as_view(), name="logout"),
	path('register/', manual_views.register, name="register"),
	path('profile/', manual_views.profile, name="profile"),
	path('profile/changepassword/', manual_views.update_password, name="update_password")
]