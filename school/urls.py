from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, AttendanceViewSet, GradeViewSet, SectionViewSet, TeacherProfileViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='students')
router.register(r'teachers', TeacherProfileViewSet, basename='teacherprofile')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'sections', SectionViewSet, basename='section')

urlpatterns = [
    path('api/', include(router.urls)),
]
