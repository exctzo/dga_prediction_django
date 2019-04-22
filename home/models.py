from django.db import models

class Users(models.Model) :
	username = models.CharField(max_length=250, primary_key=True)
	email = models.EmailField(max_length=250, unique=True)