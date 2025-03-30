from django.contrib import admin
from .models import Profile, Currency, CourseTier, Course, CoursePrice, UserCourse, Review

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'country_code', 'email_verified')
    search_fields = ('user__username', 'phone')

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol')
    search_fields = ('code', 'name')

@admin.register(CourseTier)
class CourseTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'order')
    ordering = ('order',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'tier', 'featured', 'is_active', 'created_at')
    list_filter = ('tier', 'featured', 'is_active')
    search_fields = ('title',)

@admin.register(CoursePrice)
class CoursePriceAdmin(admin.ModelAdmin):
    list_display = ('tier', 'currency', 'amount')
    list_filter = ('tier', 'currency')

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'tier', 'purchased_at', 'completed')
    list_filter = ('tier', 'completed')
    search_fields = ('user__username', 'course__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'tier', 'rating', 'created_at')
    list_filter = ('rating', 'tier')
    search_fields = ('user__username', 'course__title')
