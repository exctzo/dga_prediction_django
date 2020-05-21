from django.contrib.auth.models import AbstractBaseUser, UserManager, BaseUserManager
from django.db import models
# from django.contrib.auth import get_user_model

class User(AbstractBaseUser,BaseUserManager) :

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = ('password','email','local_dns_ip')

	username = models.CharField(max_length=250, primary_key=True)
	password = models.CharField(max_length=50)
	email = models.EmailField(max_length=250, unique=True)
	local_dns_ip = models.CharField(max_length=30, default = '0.0.0.0')
	
	objects = UserManager()

# user_model = get_user_model()
# user_model.add_to_class("local_dns_ip", models.GenericIPAddressField(default = '0.0.0.0'))