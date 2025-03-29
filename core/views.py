from django.shortcuts import render, redirect
from django.views.generic import ListView, View
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout  # Import logout function
from .models import Course
from .forms import CheckoutForm, LoginForm  # Ensure LoginForm is created
import requests  # For Pesapal API integration

from django.shortcuts import render, get_object_or_404
from .models import Course, UserCourse
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import CustomUserCreationForm  # We'll create this next

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
    template_name = 'core/course_list.html'  # Template for listing courses
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
        context['featured_courses'] = Course.objects.filter(is_featured=True)[:5]
        return context

class UserRegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'core/register.html', {'form': form})  # Template for user registration

    def post(self, request):
        form = RegistrationForm(request.POST)
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

class CourseCheckoutView(View):
    def post(self, request, course_id):
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                course = Course.objects.get(id=course_id)
                # Pesapal payment integration
                pesapal_url = "https://www.pesapal.com/API/PostPesapalDirectOrderV4"
                payload = {
                    'Amount': course.price,
                    'Description': f'Payment for {course.title}',
                    'Type': 'MERCHANT',
                    'Reference': f'course-{course.id}-{request.user.id}',
                    'FirstName': request.user.first_name,
                    'LastName': request.user.last_name,
                    'Email': request.user.email,
                }
                headers = {
                    'Authorization': f'Bearer {settings.PESAPAL_API_KEY}',
                    'Content-Type': 'application/json',
                }
                response = requests.post(pesapal_url, json=payload, headers=headers)
                if response.status_code == 200:
                    course.enrollments.create(user=request.user)
                    messages.success(request, 'Payment successful. You are now enrolled.')
                    return redirect('course_detail', course_id=course.id)
                else:
                    messages.error(request, 'Payment failed. Please try again.')
            except requests.RequestException:
                messages.error(request, 'Payment failed. Please try again.')
        return redirect('checkout', course_id=course_id)  # Redirect to checkout template if needed

def home(request):
    featured_course = Course.objects.first()  # Use the first course as the featured course
    if not featured_course:
        return render(request, 'core/index.html', {'course': None})  # Handle case where no course exists

    purchased = False
    if request.user.is_authenticated:
        purchased = UserCourse.objects.filter(user=request.user, course=featured_course).exists()

    context = {
        'course': {
            'id': featured_course.id,  # Ensure ID is passed
            'title': featured_course.title,
            'image': featured_course.image,
            'short_description': featured_course.short_description,
            'rating': featured_course.rating,
            'comment_count': featured_course.comments_count,
            'price': featured_course.price,
            'purchased': purchased,
        }
    }
    return render(request, 'core/index.html', context)


@login_required
def course_detail(request, id):  # Accept 'id' as a parameter
    course = get_object_or_404(Course, pk=id)  # Use 'id' to fetch the course
    purchased = UserCourse.objects.filter(user=request.user, course=course).exists()
    
    context = {
        'course': {
            'title': course.title,
            'image': course.image,
            'description': course.description,
            'likes_count': course.likes_count,
            'comments_count': course.comments_count,
            'price': course.price,
            'purchased': purchased,
        }
    }
    return render(request, 'core/course_detail.html', context)

def logout_view(request):
    if request.method == 'GET':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')  # Redirect to home page after logout
    return HttpResponse(status=405)  # Return 405 for unsupported methods