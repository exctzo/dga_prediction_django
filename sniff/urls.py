from django.urls import path
from . import views as manual_views

urlpatterns = [
    path('', manual_views.sniff),
    path('statistic/', manual_views.statistic),
    path('get_task_info/', manual_views.get_task_info),
    path('revoke_task/', manual_views.revoke_task)
]