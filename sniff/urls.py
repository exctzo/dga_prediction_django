from django.urls import path
from . import views as manual_views

urlpatterns = [
    path('', manual_views.sniff),
    path('statistic/', manual_views.statistic)
]