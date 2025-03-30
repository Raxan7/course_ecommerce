from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course
from .serializers import CourseSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from .models import Course, CoursePrice, Currency, UserCourse
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
        course = Course.objects.get(id=course_id)
        data = json.loads(request.body)
        currency_code = data.get('currency', 'TZS')
        currency = Currency.objects.get(code=currency_code)
        price = CoursePrice.objects.get(tier=course.tier, currency=currency)

        # Simulate purchase logic
        UserCourse.objects.create(user=request.user, course=course, tier=course.tier)
        return JsonResponse({'message': 'Purchase successful!'})
    except (Course.DoesNotExist, Currency.DoesNotExist, CoursePrice.DoesNotExist):
        return JsonResponse({'error': 'Purchase failed. Invalid data.'}, status=400)
