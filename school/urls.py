from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, AttendanceViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='students')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('api/', include(router.urls)),
]
