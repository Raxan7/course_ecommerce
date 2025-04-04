from django.contrib.auth.decorators import login_required
from .models import Affiliate, Referral
from django.shortcuts import render
from django.http import HttpResponse


@login_required
def affiliate_dashboard(request):
    try:
        affiliate = Affiliate.objects.get(user=request.user)
    except Affiliate.DoesNotExist:
        return render(request, 'affiliates/not_affiliate.html')
    
    referrals = Referral.objects.filter(affiliate=affiliate).select_related('user_course', 'user_course__course')
    
    context = {
        'affiliate': affiliate,
        'referrals': referrals,
        'total_earnings': sum([r.commission_earned for r in referrals]),
        'unpaid_balance': sum([r.commission_earned for r in referrals if not r.is_paid]),
    }
    return render(request, 'affiliates/dashboard.html', context)




@login_required
def request_payout(request):
    affiliate = Affiliate.objects.get(user=request.user)
    
    if affiliate.balance > 0:
        # Integrate with Stripe/PayPal here
        print(f"Paying out ${affiliate.balance} to {affiliate.user.email}")
        affiliate.balance = 0
        affiliate.save()
        return HttpResponse("Payout request submitted!")
    return HttpResponse("No balance available for payout.")