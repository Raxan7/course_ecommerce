# affiliates/models.py
from django.db import models
from django.contrib.auth.models import User
from core.models import UserCourse

class Affiliate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    affiliate_code = models.CharField(max_length=10, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.affiliate_code}"

class Referral(models.Model):
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE)
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_course = models.ForeignKey(UserCourse, on_delete=models.SET_NULL, null=True, blank=True)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Referral by {self.affiliate.user.username} for {self.referred_user.username}"