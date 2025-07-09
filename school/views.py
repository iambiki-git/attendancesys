from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Student, Attendance, Grade, Section
from .serializers import StudentSerializer, AttendanceSerializer, GradeSerializer, SectionSerializer

class IsAuthenticatedSchoolUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.school is not None
    
class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticatedSchoolUser]

    def get_queryset(self):
        return Grade.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)  

class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticatedSchoolUser]

    def get_queryset(self):
        return Section.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticatedSchoolUser]

    def get_queryset(self):
        return Student.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticatedSchoolUser]

    def get_queryset(self):
        return Attendance.objects.filter(student__school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save()

