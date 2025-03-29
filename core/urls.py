from django.urls import path
from django.contrib.auth import views as auth_views  # Import auth views
from . import views

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

    path('course/<int:id>/', views.course_detail, name='course_detail'),

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),  # Use your custom logout view

    path(".well-known/acme-challenge/<str:challenge>", acme_challenge),
]
