from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, School

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'school', 'is_teacher', 'is_student', 'is_school_admin', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('School Info', {
            'fields': ('school', 'is_teacher', 'is_student', 'is_school_admin'),
        }),
    )
