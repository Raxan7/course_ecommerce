from django.core.management.base import BaseCommand
from core.models import CoursePrice, CourseTier, Currency, Course, UserCourse, Review, Profile


class Command(BaseCommand):
    help = 'Export data from the database for use in another database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Exporting data..."))

        # Export Course Prices
        self.stdout.write(self.style.SUCCESS("Exporting Course Prices"))
        for price in CoursePrice.objects.all():
            # Accessing fields directly
            self.stdout.write(f"CourseTier: {price.tier.name}, Currency: {price.currency.code}, Amount: {price.amount}")

        # Export Course Tiers
        self.stdout.write(self.style.SUCCESS("Exporting Course Tiers"))
        for tier in CourseTier.objects.all():
            # Accessing fields directly
            self.stdout.write(f"ID: {tier.id}, Name: {tier.name}, Description: {tier.description}, Order: {tier.order}")

        # Export Currencies
        self.stdout.write(self.style.SUCCESS("Exporting Currencies"))
        for currency in Currency.objects.all():
            # Accessing fields directly
            self.stdout.write(f"ID: {currency.id}, Code: {currency.code}, Name: {currency.name}, Symbol: {currency.symbol}")

        # Export Courses
        self.stdout.write(self.style.SUCCESS("Exporting Courses"))
        for course in Course.objects.all():
            # Accessing fields directly
            self.stdout.write(f"ID: {course.id}, Title: {course.title}, Short Description: {course.short_description}, Tier ID: {course.tier_id}")

        # Export UserCourses
        self.stdout.write(self.style.SUCCESS("Exporting User Courses"))
        for user_course in UserCourse.objects.all():
            # Accessing fields directly
            self.stdout.write(f"User: {user_course.user.username}, Course: {user_course.course.title}, Tier: {user_course.tier.name}, Purchased At: {user_course.purchased_at}")

        # Export Reviews
        self.stdout.write(self.style.SUCCESS("Exporting Reviews"))
        for review in Review.objects.all():
            # Accessing fields directly
            self.stdout.write(f"Course: {review.course.title}, User: {review.user.username}, Rating: {review.rating}, Comment: {review.comment}, Created At: {review.created_at}")

        # Export Profiles
        self.stdout.write(self.style.SUCCESS("Exporting Profiles"))
        for profile in Profile.objects.all():
            # Accessing fields directly
            self.stdout.write(f"User: {profile.user.username}, Phone: {profile.phone}, Email Verified: {profile.email_verified}, Country Code: {profile.country_code}")

        self.stdout.write(self.style.SUCCESS("Export complete!"))
