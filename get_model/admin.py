from django.contrib import admin
from . import models

admin.site.register(models.PreparedDatasets)
admin.site.register(models.PreparedModel)
admin.site.register(models.ModelsLearningStat)