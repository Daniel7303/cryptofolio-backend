from django.urls import path
from .views import AlertListCreateView
from .alert import check_alerts

urlpatterns = [
    path('', AlertListCreateView.as_view(), name='alert_list_create'),
    path('check/', check_alerts, name='check_alerts'),
]
