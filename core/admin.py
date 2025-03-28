from django.contrib import admin
from .models import Course, UserCourse, Review

# Register your models here.
admin.site.register(Course)
admin.site.register(UserCourse)
admin.site.register(Review)
