from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
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
        # Check if user is authenticated (redundant but safe)
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Parse the request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        # Get required fields
        tier_id = data.get('tier_id')
        currency_code = data.get('currency', 'TZS')

        if not tier_id:
            return JsonResponse({'error': 'Tier ID is required'}, status=400)

        # Get objects
        try:
            course = Course.objects.get(id=course_id)
            tier = CourseTier.objects.get(id=tier_id)
            currency = Currency.objects.get(code=currency_code)
            price = CoursePrice.objects.get(tier=tier, currency=currency)
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)
        except CourseTier.DoesNotExist:
            return JsonResponse({'error': 'Tier not found'}, status=404)
        except Currency.DoesNotExist:
            return JsonResponse({'error': 'Currency not supported'}, status=400)
        except CoursePrice.DoesNotExist:
            return JsonResponse({'error': 'Price not available for this tier/currency'}, status=400)

        # Check if user already purchased this course
        if UserCourse.objects.filter(user=request.user, course=course).exists():
            return JsonResponse({
                'success': True,
                'message': 'You have already purchased this course.',
            })

        # Create the purchase record
        UserCourse.objects.create(
            user=request.user,
            course=course,
            tier=tier
        )

        return JsonResponse({
            'success': True,
            'message': 'Purchase successful!',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)