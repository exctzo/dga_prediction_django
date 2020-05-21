from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login , update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from . import forms
from . import models

def home(iv_request):
	return render(iv_request, 'home.html')

def redirect(iv_request):
	return HttpResponseRedirect("login/")

def register(iv_request):
	if iv_request.user.is_authenticated :
		return HttpResponseRedirect("/")

	if iv_request.method == 'POST' :
		lv_form = forms.RegisterForm(iv_request.POST)
		if lv_form.is_valid() :
			lv_form.save()
			lv_username = lv_form.cleaned_data.get("username")
			lv_email = lv_form.cleaned_data.get("email")
			lv_local_dns_ip = lv_form.cleaned_data.get("local_dns_ip")
			lv_password = lv_form.cleaned_data.get("password")
			try :
				lv_user = models.User.objects.get(username=uservalue)
				lv_error = {'form':lv_form, 'error':'User name already taken'}
				return render(iv_request, 'registration/register.html', lv_error)
			except :
				lv_user = models.User.objects.create_user(username=lv_username, password=lv_password, email=lv_email, first_name=lv_local_dns_ip) 
				lv_user.save()
				login(iv_request, lv_user)
				return HttpResponseRedirect('/')
	else :
		lv_form = forms.RegisterForm()
	return render(iv_request, 'registration/register.html', {'form':lv_form})

@login_required(login_url='/login/')
def profile(iv_request) :
	return render(iv_request, 'profile/profile.html')

@login_required(login_url='/login/')
def update_password(iv_request) :
	if iv_request.method == 'POST' :
		lv_form = PasswordChangeForm(iv_request.user, iv_request.POST)
		if form.is_valid() :
			lv_user = form.save()
			update_session_auth_hash(iv_request, lv_user)
			messages.success(iv_request, 'Your password was successfully updated!')
		else :
			messages.error(iv_request, 'Please correct the error below.')
	else :
		lv_form = PasswordChangeForm(iv_request.user)
	return render(iv_request, 'profile/change-password.html',{'form':lv_form})