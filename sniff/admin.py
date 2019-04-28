from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Requests)
admin.site.register(models.Hosts)