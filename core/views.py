from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Course, UserCourse, CoursePrice, Currency
from .forms import CheckoutForm, LoginForm, CustomUserCreationForm
import requests

# Utility function to get course price in different currencies
def get_course_price(course, currency_code='TZS'):
    try:
        currency = Currency.objects.get(code=currency_code)
        price = CoursePrice.objects.get(course=course, currency=currency)
        return price.amount
    except (Currency.DoesNotExist, CoursePrice.DoesNotExist):
        return course.base_price  # Fallback to base price

# Home view
def home(request):
    featured_course = Course.objects.filter(featured=True).first()
    if not featured_course:
        return render(request, 'core/index.html', {'course': None})

    purchased = False
    if request.user.is_authenticated:
        purchased = UserCourse.objects.filter(user=request.user, course=featured_course).exists()

    # Get prices for different currencies
    price_tzs = get_course_price(featured_course, 'TZS')
    price_usd = get_course_price(featured_course, 'USD')
    price_kes = get_course_price(featured_course, 'KES')
    price_eur = get_course_price(featured_course, 'EUR')

    context = {
        'course': {
            'id': featured_course.id,
            'title': featured_course.title,
            'image': featured_course.image,
            'short_description': featured_course.short_description,
            'rating': featured_course.rating,
            'comment_count': featured_course.comments_count,
            'base_price': featured_course.base_price,
            'price_tzs': price_tzs,
            'price_usd': price_usd,
            'price_kes': price_kes,
            'price_eur': price_eur,
            'purchased': purchased,
        }
    }
    return render(request, 'core/index.html', context)

# Course detail view
@login_required
def course_detail(request, id):
    course = get_object_or_404(Course, pk=id)
    purchased = UserCourse.objects.filter(user=request.user, course=course).exists()
    
    # Get prices for different currencies
    price_tzs = get_course_price(course, 'TZS')
    price_usd = get_course_price(course, 'USD')
    price_kes = get_course_price(course, 'KES')
    price_eur = get_course_price(course, 'EUR')

    context = {
        'course': {
            'title': course.title,
            'image': course.image,
            'description': course.description,
            'likes_count': course.likes_count,
            'comments_count': course.comments_count,
            'base_price': course.base_price,
            'price_tzs': price_tzs,
            'price_usd': price_usd,
            'price_kes': price_kes,
            'price_eur': price_eur,
            'purchased': purchased,
        }
    }
    return render(request, 'core/course_detail.html', context)

# Course checkout view
class CourseCheckoutView(View):
    def post(self, request, course_id):
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                course = Course.objects.get(id=course_id)
                currency = form.cleaned_data.get('currency', 'TZS')
                price = get_course_price(course, currency)
                
                # Pesapal payment integration
                pesapal_url = "https://www.pesapal.com/API/PostPesapalDirectOrderV4"
                payload = {
                    'Amount': price,
                    'Description': f'Payment for {course.title}',
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
                    UserCourse.objects.create(user=request.user, course=course)
                    messages.success(request, 'Payment successful. You are now enrolled.')
                    return redirect('course_detail', id=course.id)
                else:
                    messages.error(request, 'Payment failed. Please try again.')
            except requests.RequestException:
                messages.error(request, 'Payment failed. Please try again.')
        return redirect('checkout', course_id=course_id)

# Logout view
@require_http_methods(["GET"])  # Restrict to GET requests
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')  # Redirect to home page after logout

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
        
        # Add prices to each course
        courses_with_prices = []
        for course in context['courses']:
            course_data = {
                'course': course,
                'price_tzs': get_course_price(course, 'TZS'),
                'price_usd': get_course_price(course, 'USD'),
                'price_kes': get_course_price(course, 'KES'),
                'price_eur': get_course_price(course, 'EUR'),
            }
            courses_with_prices.append(course_data)
        
        context['courses_with_prices'] = courses_with_prices
        
        # Same for featured courses
        featured_courses = Course.objects.filter(featured=True)[:5]
        featured_with_prices = []
        for course in featured_courses:
            featured_with_prices.append({
                'course': course,
                'price_tzs': get_course_price(course, 'TZS'),
                'price_usd': get_course_price(course, 'USD'),
            })
        
        context['featured_courses'] = featured_with_prices
        
        return context

class UserRegistrationView(View):
    def get(self, request):
        form = CustomUserCreationForm()  # Use CustomUserCreationForm
        return render(request, 'core/register.html', {'form': form})  # Template for user registration

    def post(self, request):
        form = CustomUserCreationForm(request.POST)  # Use CustomUserCreationForm
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
            return redirect('login')  # Ensure 'login' matches the URL pattern name
        return render(request, 'core/register.html', {'form': form})  # Template for user registration

class UserLoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'core/login.html', {'form': form})  # Template for user login

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful.')
                return redirect('home')  # Redirect to home or another page
            else:
                messages.error(request, 'Invalid username or password.')
        return render(request, 'core/login.html', {'form': form})  # Re-render login template with errors


from django.views.decorators.http import require_POST

@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')