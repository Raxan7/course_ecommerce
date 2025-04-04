from django.urls import path
from .views import affiliate_dashboard, request_payout

urlpatterns = [
    path('dashboard/', affiliate_dashboard, name='affiliate_dashboard'),
    path('request-payout/', request_payout, name='request_payout'),
]