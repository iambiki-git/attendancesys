from django.contrib import admin
from .models import Student, Attendance, Grade, Section


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)
    search_fields = ('name', 'school__name')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'grade')
    list_filter = ('school',)
    search_fields = ('name', 'school__name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school', 'grade', 'section')
    list_filter = ('school',)
    

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'date', 'status')
    list_filter = ('student__school', 'date', 'status')


