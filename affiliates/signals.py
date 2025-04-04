# affiliates/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
import secrets
from .models import Affiliate

@receiver(post_save, sender=User)
def create_affiliate(sender, instance, created, **kwargs):
    if created:
        Affiliate.objects.create(
            user=instance,
            affiliate_code=secrets.token_hex(3).upper()  # 6-char random code
        )