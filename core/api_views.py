from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from affiliates.models import Affiliate, Referral
from .models import Course
from .serializers import CourseSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from .models import Course, CoursePrice, Currency, UserCourse, CourseTier
from django.contrib.auth.decorators import login_required
import json

class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'description']

@require_GET
def get_course_data(request, course_id):
    currency_code = request.GET.get('currency', 'TZS')
    try:
        course = Course.objects.get(id=course_id)
        currency = Currency.objects.get(code=currency_code)
        price = CoursePrice.objects.get(tier=course.tier, currency=currency)
        return JsonResponse({'price': f"{currency.symbol}{price.amount}"})
    except (Course.DoesNotExist, Currency.DoesNotExist, CoursePrice.DoesNotExist):
        return JsonResponse({'error': 'Invalid course or currency'}, status=400)

@require_GET
def get_course_tiers(request, course_id):
    currency_code = request.GET.get('currency', 'TZS')
    try:
        course = Course.objects.get(id=course_id)
        tiers = course.available_tiers.all()
        currency = Currency.objects.get(code=currency_code)

        tier_data = []
        for tier in tiers:
            price = CoursePrice.objects.get(tier=tier, currency=currency)
            tier_data.append({
                'id': tier.id,
                'name': tier.get_name_display(),
                'description': tier.description,
                'price': f"{currency.symbol}{price.amount}",
            })

        return JsonResponse({'tiers': tier_data})
    except (Course.DoesNotExist, Currency.DoesNotExist, CoursePrice.DoesNotExist):
        return JsonResponse({'error': 'Invalid course or currency'}, status=400)


@csrf_exempt
@require_POST
@login_required
def buy_course(request, course_id):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        tier_id = data.get('tier_id')
        currency_code = data.get('currency', 'TZS')

        if not tier_id:
            return JsonResponse({'error': 'Tier ID is required'}, status=400)

        try:
            course = Course.objects.get(id=course_id)
            tier = CourseTier.objects.get(id=tier_id)
            currency = Currency.objects.get(code=currency_code)
            price = CoursePrice.objects.get(tier=tier, currency=currency)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Check for existing purchase
        if UserCourse.objects.filter(user=request.user, course=course).exists():
            return JsonResponse({
                'success': True,
                'message': 'You have already purchased this course.',
            })

        # Create the purchase record
        user_course = UserCourse.objects.create(
            user=request.user,
            course=course,
            tier=tier
        )

        # ===== AFFILIATE COMMISSION PROCESSING =====
        affiliate_code = request.session.get('affiliate_code')
        if affiliate_code:
            try:
                affiliate = Affiliate.objects.get(affiliate_code=affiliate_code)
                commission = float(price.amount) * 0.10  # 10% commission
                
                Referral.objects.create(
                    affiliate=affiliate,
                    referred_user=request.user,
                    commission_earned=commission,
                    user_course=user_course
                )
                
                affiliate.balance += commission
                affiliate.save()
            except Affiliate.DoesNotExist:
                pass
        # ===== END AFFILIATE PROCESSING =====

        return JsonResponse({
            'success': True,
            'message': 'Purchase successful!',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)