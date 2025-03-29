from django.urls import path
from django.contrib.auth import views as auth_views  # Import auth views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('checkout/<int:course_id>/', views.CourseCheckoutView.as_view(), name='checkout'),

    path('course/<int:id>/', views.course_detail, name='course_detail'),

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),  # Use your custom logout view
]
