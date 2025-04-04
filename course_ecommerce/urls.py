"""
URL configuration for course_ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from core.views import logout_view  # Import the logout view
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),   
    path('', include('core.urls')),  # Include core app URLs  
    path('logout/', logout_view, name='logout'),  # Add logout URL

    path('affiliate/', include('affiliates.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files in development]
