from django.urls import path
from . import views as manual_views

urlpatterns = [
    path('', manual_views.get_model),
    path('get_data/', manual_views.get_data),
    path('train_model/', manual_views.train_model),
    path('get_task_info/', manual_views.get_task_info),
    path('revoke_task/', manual_views.revoke_task)
]