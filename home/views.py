from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login , update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from . import forms
from . import models

def home(request):
	return render(request, 'home.html')

def redirect(request):
	return HttpResponseRedirect("login/")

def register(request):
	if request.user.is_authenticated :
		return HttpResponseRedirect("/")

	if request.method == 'POST' :
		form = forms.RegisterForm(request.POST)
		if form.is_valid() :
			form.save()
			username = form.cleaned_data.get("username")
			email = form.cleaned_data.get("email")
			first_name = form.cleaned_data.get("first_name") # its local_dns_ip
			password = form.cleaned_data.get("password")
			try :
				user = User.objects.get(username=uservalue)
				error = {'form':form, 'error':'User name already taken'}
				return render(request, 'registration/register.html', error)
			except :
				# need to change user model to set rigth attribute (local dns ip)
				user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name) 
				user.save()
				login(request, user)
				return HttpResponseRedirect('/')
	else :
		form = forms.RegisterForm()
	return render(request, 'registration/register.html', {'form':form})

@login_required(login_url='/login/')
def profile(request) :
	return render(request, 'profile/profile.html')

@login_required(login_url='/login/')
def update_password(request) :
	if request.method == 'POST' :
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid() :
			user = form.save()
			update_session_auth_hash(request, user)
			messages.success(request, 'Your password was successfully updated!')
			#return HttpResponseRedirect("/")
		else :
			messages.error(request, 'Please correct the error below.')
	else :
		form = PasswordChangeForm(request.user)
	return render(request, 'profile/change-password.html',{'form':form})