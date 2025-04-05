from django.urls import path
from django.contrib.auth import views as auth_views  # Import auth views
from . import views
from . import api_views

from django.http import HttpResponse
import os

def acme_challenge(request, challenge):
    challenge_path = os.path.join('/home/useuulkn/repositories/course_ecommerce/.well-known/acme-challenge/', challenge)
    if os.path.exists(challenge_path):
        with open(challenge_path, 'r') as f:
            return HttpResponse(f.read(), content_type="text/plain")
    return HttpResponse("Not Found", status=404)


urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('checkout/<int:course_id>/', views.CourseCheckoutView.as_view(), name='checkout'),

    # Removed course_detail URL

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),  # Use your custom logout view

    path(".well-known/acme-challenge/<str:challenge>", acme_challenge),

    # API endpoints
    path('api/get_course_data/<int:course_id>/', api_views.get_course_data, name='get_course_data'),
    path('api/buy_course/<int:course_id>/', api_views.buy_course, name='buy_course'),
    path('api/get_course_tiers/<int:course_id>/', api_views.get_course_tiers, name='get_course_tiers'),
    path('api/toggle_like/<int:course_id>/', views.toggle_like, name='toggle_like'),

    path('course/content/', views.course_content, name='course_content'),

    # PesaPal URLs
    path('pesapal/callback/', views.pesapal_callback, name='pesapal_callback'),
    path('pesapal/ipn/', views.pesapal_ipn, name='pesapal_ipn'),
]
