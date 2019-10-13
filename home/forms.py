from django import forms
from django.contrib.auth.forms import AuthenticationForm
from . import models

class RegisterForm(forms.ModelForm) :
	username = forms.CharField(max_length=250, label="User Name")
	email = forms.EmailField(max_length=250, label="User Email", widget=forms.TextInput(attrs={'type':'email'}))
	first_name = forms.GenericIPAddressField(label="Local DNS IP", widget=forms.TextInput(), required=True) # its local dns ip
	password = forms.CharField(max_length=250, min_length=8, label="Password", widget=forms.TextInput(attrs={'type':'password'}))

	class Meta :
		model = models.Users
		fields = ["username","email","first_name"]

class LoginForm(AuthenticationForm) :
	username = forms.CharField(max_length=50, label="User Name")
	password = forms.CharField(max_length=250, min_length=8, label="Password", widget=forms.TextInput(attrs={'type':'password'}))