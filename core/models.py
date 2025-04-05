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
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class CourseTier(models.Model):
    TIER_CHOICES = [
        ('basic', 'Warrior\'s Path'),
        ('standard', 'Champion\'s Edge'),
        ('premium', 'King\'s Throne'),
    ]
    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    courses = models.ManyToManyField('Course', related_name='available_tiers')
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.get_name_display()

class Course(models.Model):
    # Common fields for all tiers
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    image = models.ImageField(upload_to='course_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    liked_users = models.ManyToManyField(User, related_name='liked_courses', blank=True)
    
    # Tier relationship
    tier = models.ForeignKey(CourseTier, on_delete=models.PROTECT, related_name='default_courses')
    
    class Meta:
        ordering = ['-featured', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.tier.get_name_display()})"

class CoursePrice(models.Model):
    tier = models.ForeignKey(CourseTier, on_delete=models.CASCADE, related_name='prices')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('tier', 'currency')

    def __str__(self):
        return f"{self.tier.get_name_display()} - {self.currency.code} {self.amount}"

class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    tier = models.ForeignKey(CourseTier, on_delete=models.PROTECT)
    purchased_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.tier.get_name_display()})"

class Review(models.Model):
    course = models.ForeignKey(Course, related_name='reviews', on_delete=models.CASCADE)
    tier = models.ForeignKey(CourseTier, on_delete=models.PROTECT)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('course', 'user')

    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star review for {self.course.title} ({self.tier.get_name_display()})"
    

class PaymentStatus(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    tier = models.ForeignKey(CourseTier, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)