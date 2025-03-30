from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from .models import Course, CourseTier, UserCourse, CoursePrice, Currency
from .forms import CheckoutForm, LoginForm, CustomUserCreationForm
import requests
from django.utils.decorators import method_decorator

# Utility function to get tier prices
def get_tier_prices(tier, currency_code='TZS'):
    try:
        currency = Currency.objects.get(code=currency_code)
        price = CoursePrice.objects.get(tier=tier, currency=currency)
        return price.amount
    except (Currency.DoesNotExist, CoursePrice.DoesNotExist):
        return None

# Home view
def home(request):
    # Get all active tiers
    tiers = CourseTier.objects.filter(courses__is_active=True).distinct().order_by('order')
    
    tier_data = []
    for tier in tiers:
        # Get the first active course for this tier (they should be the same content)
        course = tier.courses.filter(is_active=True).first()
        if course:
            tier_data.append({
                'tier': tier,
                'course': course,
                'price_tzs': get_tier_prices(tier, 'TZS'),
                'price_usd': get_tier_prices(tier, 'USD'),
                'price_kes': get_tier_prices(tier, 'KES'),
                'price_eur': get_tier_prices(tier, 'EUR'),
            })
    
    featured_tier = CourseTier.objects.filter(courses__featured=True).first()
    featured_course = featured_tier.courses.filter(featured=True).first() if featured_tier else None
    
    purchased = False
    if request.user.is_authenticated and featured_course:
        purchased = UserCourse.objects.filter(user=request.user, course=featured_course).exists()

    context = {
        'tiers': tier_data,
        'featured_course': {
            'id': featured_course.id if featured_course else None,
            'title': featured_course.title if featured_course else None,
            'image': featured_course.image if featured_course else None,
            'short_description': featured_course.short_description if featured_course else None,
            'rating': featured_course.rating if featured_course else None,
            'comment_count': featured_course.comments_count if featured_course else None,
            'purchased': purchased,
            'tier': featured_tier,
            'price_tzs': get_tier_prices(featured_tier, 'TZS') if featured_tier else None,
            'price_usd': get_tier_prices(featured_tier, 'USD') if featured_tier else None,
            'price_kes': get_tier_prices(featured_tier, 'KES') if featured_tier else None,
            'price_eur': get_tier_prices(featured_tier, 'EUR') if featured_tier else None,
        } if featured_course else None
    }
    return render(request, 'core/index.html', context)

# Course checkout view
class CourseCheckoutView(View):
    def post(self, request, course_id):
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                course = Course.objects.get(id=course_id)
                tier = course.tier
                currency = form.cleaned_data.get('currency', 'TZS')
                price = get_tier_prices(tier, currency)
                
                # Pesapal payment integration
                pesapal_url = "https://www.pesapal.com/API/PostPesapalDirectOrderV4"
                payload = {
                    'Amount': price,
                    'Description': f'Payment for {course.title} ({tier.get_name_display()})',
                    'Type': 'MERCHANT',
                    'Reference': f'course-{course.id}-{request.user.id}',
                    'FirstName': request.user.first_name,
                    'LastName': request.user.last_name,
                    'Email': request.user.email,
                    'Currency': currency,
                }
                headers = {
                    'Authorization': f'Bearer {settings.PESAPAL_API_KEY}',
                    'Content-Type': 'application/json',
                }
                response = requests.post(pesapal_url, json=payload, headers=headers)
                if response.status_code == 200:
                    UserCourse.objects.create(
                        user=request.user, 
                        course=course,
                        tier=tier
                    )
                    messages.success(request, 'Payment successful. You are now enrolled.')
                    return redirect('course_detail', id=course.id)
                else:
                    messages.error(request, 'Payment failed. Please try again.')
            except requests.RequestException:
                messages.error(request, 'Payment failed. Please try again.')
        return redirect('checkout', course_id=course_id)

# Logout view
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

# User registration view
class UserRegistrationView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'core/register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            verification_link = f"{request.build_absolute_uri('/verify-email/')}?email={user.email}"
            send_mail(
                'Verify your email',
                f'Click the link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            messages.success(request, 'Verification email sent.')
            return redirect('login')
        return render(request, 'core/register.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.username = form.cleaned_data['username']  # Save username
            user.save()
            
            # Save phone number to profile
            profile = user.profile
            profile.phone = form.cleaned_data['phone']
            profile.country_code = form.cleaned_data['country_code']
            profile.save()
            
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

# User login view
class UserLoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'core/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        return render(request, 'core/login.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class CourseListView(ListView):
    model = Course
    template_name = 'core/course_list.html'
    context_object_name = 'courses'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        sort = self.request.GET.get('sort')
        if category:
            queryset = queryset.filter(category=category)
        if sort:
            queryset = queryset.order_by(sort)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add prices and purchase status to each course
        courses_with_prices = []
        for course in context['courses']:
            purchased = UserCourse.objects.filter(user=self.request.user, course=course).exists()
            course_data = {
                'course': course,
                'purchased': purchased,
                'price_tzs': get_tier_prices(course.tier, 'TZS'),
                'price_usd': get_tier_prices(course.tier, 'USD'),
                'price_kes': get_tier_prices(course.tier, 'KES'),
                'price_eur': get_tier_prices(course.tier, 'EUR'),
            }
            courses_with_prices.append(course_data)
        
        context['courses_with_prices'] = courses_with_prices
        
        # Same for featured courses
        featured_courses = Course.objects.filter(featured=True)[:5]
        featured_with_prices = []
        for course in featured_courses:
            purchased = UserCourse.objects.filter(user=self.request.user, course=course).exists()
            featured_with_prices.append({
                'course': course,
                'purchased': purchased,
                'price_tzs': get_tier_prices(course.tier, 'TZS'),
                'price_usd': get_tier_prices(course.tier, 'USD'),
            })
        
        context['featured_courses'] = featured_with_prices
        
        return context