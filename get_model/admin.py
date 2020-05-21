from django.contrib import admin
from . import models

admin.site.register(models.PreparedDataset)
admin.site.register(models.PreparedModel)
admin.site.register(models.ModelLearningStat)