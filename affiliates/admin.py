# affiliates/admin.py
from django.contrib import admin
from .models import Affiliate, Referral

admin.site.register(Affiliate)
admin.site.register(Referral)