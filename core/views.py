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
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Course, CourseTier, UserCourse, CoursePrice, Currency
from .forms import CheckoutForm, LoginForm, CustomUserCreationForm
from .pesapal import PesaPal
from decimal import Decimal
import json
import uuid
from django.core.serializers.json import DjangoJSONEncoder
from affiliates.models import Affiliate, Referral

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

    courses_with_prices = [
        {
            'course': course,
        }
        for course in Course.objects.all()
    ]

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
        } if featured_course else None,
        'courses_with_prices': courses_with_prices,
    }
    return render(request, 'core/index.html', context)

import sys
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Course, CourseTier
from .pesapal import PesaPal
import uuid

def debug_print(message):
    """Print debug messages to terminal with timestamp"""
    from datetime import datetime
    print(f"[{datetime.now()}] DEBUG: {message}", file=sys.stderr)

class CourseCheckoutView(View):
    def post(self, request, course_id):
        try:
            debug_print(f"=== Starting checkout process for course_id: {course_id} ===")
            
            # Get course and validate input
            debug_print("1. Fetching course from database...")
            course = get_object_or_404(Course, id=course_id)
            debug_print(f"   Found course: {course.title} (ID: {course.id})")
            
            tier_id = request.POST.get('tier_id')
            currency = request.POST.get('currency', 'TZS')
            debug_print(f"2. Received parameters - tier_id: {tier_id}, currency: {currency}")
            
            if not tier_id:
                debug_print("   ERROR: No tier_id provided!")
                messages.error(request, 'Please select a tier')
                return redirect('course_list')
            
            debug_print("3. Fetching tier from database...")
            tier = get_object_or_404(CourseTier, id=tier_id)
            debug_print(f"   Found tier: {tier.get_name_display()} (ID: {tier.id})")
            
            debug_print("4. Getting price for selected currency...")
            price = get_tier_prices(tier, currency)
            debug_print(f"   Price retrieved: {price}")
            
            if not price:
                debug_print(f"   ERROR: No price available for currency: {currency}")
                messages.error(request, 'Price not available for selected currency')
                return redirect('course_list')
            
            # ===== AFFILIATE TRACKING =====
            affiliate_code = request.session.get('affiliate_code')
            if affiliate_code:
                try:
                    affiliate = Affiliate.objects.get(affiliate_code=affiliate_code)
                    # Store affiliate info in session for after payment completion
                    request.session['pending_affiliate'] = {
                        'affiliate_id': affiliate.id,
                        'commission': float(price) * 0.10  # 10% commission
                    }
                except Affiliate.DoesNotExist:
                    pass
            # ===== END AFFILIATE TRACKING =====
            
            # Initialize PesaPal (RESTORED)
            debug_print("5. Initializing PesaPal service...")
            pesapal = PesaPal()
            
            # Register IPN (RESTORED)
            debug_print("6. Registering IPN URL with PesaPal...")
            ipn_id = pesapal.register_ipn_url()
            debug_print(f"   Received IPN ID: {ipn_id}")
            
            if not ipn_id:
                debug_print("   ERROR: Failed to register IPN URL!")
                messages.error(request, 'Payment service unavailable. Please try again later.')
                return redirect('course_list')
            
            # Generate unique order ID
            order_id = f"COURSE-{course.id}-{uuid.uuid4().hex[:8]}"
            debug_print(f"7. Generated order ID: {order_id}")
            
            # Prepare order details
            callback_url = request.build_absolute_uri(reverse('pesapal_callback'))
            cancellation_url = request.build_absolute_uri(reverse('course_list'))
            
            debug_print("8. Building order details:")
            debug_print(f"   - Callback URL: {callback_url}")
            debug_print(f"   - Cancellation URL: {cancellation_url}")
            
            order_details = {
                'id': order_id[:50],
                'currency': currency,
                'amount': str(price),
                'description': f"Payment for {course.title} ({tier.get_name_display()})"[:100],
                'callback_url': callback_url,
                'cancellation_url': cancellation_url,
                'notification_id': ipn_id,  # RESTORED
                'billing_address': {
                    'email_address': request.user.email,
                    'phone_number': request.user.profile.phone or '',
                    'country_code': (request.user.profile.country_code)[1:] or 'TZ',
                    'first_name': request.user.first_name or '',
                    'last_name': request.user.last_name or '',
                }
            }
            
            debug_print("9. Complete order details:")
            for key, value in order_details.items():
                if key != 'billing_address':
                    debug_print(f"   {key}: {value}")
                else:
                    debug_print("   billing_address:")
                    for subkey, subvalue in value.items():
                        debug_print(f"     {subkey}: {subvalue}")
            
            # Submit order to PesaPal (RESTORED)
            debug_print("10. Submitting order to PesaPal...")
            response = pesapal.submit_order_request(order_details)
            debug_print(f"   PesaPal response: {response}")
            
            if response and 'redirect_url' in response:
                debug_print("11. Order submitted successfully!")
                debug_print(f"   Redirect URL: {response['redirect_url']}")
                
                # Store minimal data in session
                session_data = {
                    'order_id': order_id,
                    'course_id': course.id,
                    'tier_id': tier.id,
                }
                debug_print("12. Storing in session:")
                for key, value in session_data.items():
                    debug_print(f"   {key}: {value}")
                
                request.session['pesapal_order'] = session_data
                request.session.modified = True
                debug_print("13. Session updated successfully")
                
                # Redirect to PesaPal payment page (RESTORED)
                debug_print(f"14. Redirecting to PesaPal payment page")
                return redirect(response['redirect_url'])
            else:
                error_msg = response.get('error', {}).get('message', 'Payment initialization failed') if response else 'Payment service unavailable'
                debug_print(f"   ERROR: Payment submission failed - {error_msg}")
                messages.error(request, error_msg)
                return redirect('course_list')
                
        except Exception as e:
            debug_print(f"!!! EXCEPTION !!!")
            debug_print(f"Type: {type(e).__name__}")
            debug_print(f"Message: {str(e)}")
            debug_print("Stack trace:")
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('course_list')
        

# Add these new views for PesaPal callbacks
def pesapal_callback(request):
    """Handle PesaPal callback after payment"""
    order_tracking_id = request.GET.get('OrderTrackingId')
    if not order_tracking_id:
        messages.error(request, 'Invalid payment callback')
        return redirect('course_list')
    
    # RESTORED: Actual PesaPal status check
    pesapal = PesaPal()
    status_response = pesapal.get_transaction_status(order_tracking_id)
    
    if status_response and status_response.get('payment_status') == 'COMPLETED':
        try:
            order_details = request.session.get('pesapal_order', {})
            if not order_details:
                messages.error(request, 'Session expired. Please contact support.')
                return redirect('course_list')
            
            course = get_object_or_404(Course, id=order_details['course_id'])
            tier = get_object_or_404(CourseTier, id=order_details['tier_id'])
            
            # Create enrollment
            user_course, created = UserCourse.objects.get_or_create(
                user=request.user,
                course=course,
                tier=tier,
                defaults={'purchased_at': timezone.now()}
            )
            
            # ===== AFFILIATE COMMISSION PROCESSING =====
            pending_affiliate = request.session.get('pending_affiliate')
            if pending_affiliate and created:  # Only if new purchase
                try:
                    affiliate = Affiliate.objects.get(id=pending_affiliate['affiliate_id'])
                    Referral.objects.create(
                        affiliate=affiliate,
                        referred_user=request.user,
                        commission_earned=pending_affiliate['commission'],
                        user_course=user_course
                    )
                    affiliate.balance += pending_affiliate['commission']
                    affiliate.save()
                    debug_print(f"Affiliate commission processed: {affiliate.user.username} earned {pending_affiliate['commission']}")
                except Affiliate.DoesNotExist:
                    debug_print("Affiliate not found - commission not processed")
                
                # Clear the pending affiliate
                if 'pending_affiliate' in request.session:
                    del request.session['pending_affiliate']
            # ===== END AFFILIATE PROCESSING =====
            
            # Clear session
            if 'pesapal_order' in request.session:
                del request.session['pesapal_order']
            
            messages.success(request, 'Payment successful! You are now enrolled in the course.')
            return redirect('course_content')
            
        except Exception as e:
            messages.error(request, f'Error processing your enrollment: {str(e)}')
            return redirect('course_list')
    else:
        status = status_response.get('payment_status', 'UNKNOWN') if status_response else 'UNKNOWN'
        messages.error(request, f'Payment not completed. Status: {status}')
        return redirect('course_list')
    

@csrf_exempt
def pesapal_ipn(request):
    """Handle Instant Payment Notification from PesaPal"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_tracking_id = data.get('OrderNotification', {}).get('OrderTrackingId')
            
            if order_tracking_id:
                # Verify payment status (RESTORED)
                pesapal = PesaPal()
                status_response = pesapal.get_transaction_status(order_tracking_id)
                
                if status_response and status_response.get('payment_status') == 'COMPLETED':
                    # Here you would typically update your database
                    # You might want to store the IPN notification for auditing
                    pass
                    
        except Exception as e:
            print(f"Error processing IPN: {str(e)}")
    
    return JsonResponse({'status': 'ok'})


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

def course_content(request):
    return render(request, 'core/course_content.html')