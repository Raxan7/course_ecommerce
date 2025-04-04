# affiliates/middleware.py
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Affiliate

class AffiliateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        affiliate_code = request.GET.get('ref')  # Get ?ref=CODE from URL
        
        if affiliate_code and not request.session.get('affiliate_code'):
            try:
                affiliate = Affiliate.objects.get(affiliate_code=affiliate_code)
                request.session['affiliate_code'] = affiliate_code
            except Affiliate.DoesNotExist:
                pass
        
        response = self.get_response(request)
        return response