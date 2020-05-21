from django.contrib import admin
from . import models

admin.site.register(models.PreparedDatasets)
admin.site.register(models.PreparedModels)
admin.site.register(models.ModelsLearningStat)