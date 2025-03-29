from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=5, default='+255')
    email_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # USD, TZS, KES, EUR
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    image = models.ImageField(upload_to='course_images/')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in TZS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-featured', '-created_at']

    def __str__(self):
        return self.title

class CoursePrice(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='prices')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('course', 'currency')

    def __str__(self):
        return f"{self.course.title} - {self.currency.code} {self.amount}"

class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    purchased_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class Review(models.Model):
    course = models.ForeignKey(Course, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('course', 'user')

    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star review for {self.course.title}"