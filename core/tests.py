import pytest
from django.contrib.auth.models import User
from .models import Course, Enrollment
from django.test import TestCase

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='password')

@pytest.fixture
def course():
    return Course.objects.create(
        title='Test Course',
        description='Test Description',
        price=100.00,
        duration='2:00:00',
        instructor='Test Instructor',
    )

def test_course_purchase(user, course, client):
    client.login(username='testuser', password='password')
    response = client.post(f'/checkout/{course.id}/', {'stripe_token': 'test_token'})
    assert response.status_code == 302
    assert Enrollment.objects.filter(user=user, course=course).exists()
