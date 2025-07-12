from django.contrib import admin
from .models import Student, Attendance, Grade, Section, TeacherProfile, Subjects


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'grade_number', 'name', 'school')
    list_filter = ('school',)
    search_fields = ('name', 'school__name')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school', 'grade')
    list_filter = ('school',)
    search_fields = ('name', 'school__name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school', 'grade', 'section', 'roll_number')
    list_filter = ('school',)

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'school', 'grade', 'section', 'subjects']

    # def get_grades(self, obj):
    #     return ", ".join([str(grade.grade_number) for grade in obj.grades.all()])
    # get_grades.short_description = "Grades"

    # def get_sections(self, obj):
    #     return ", ".join([section.name for section in obj.sections.all()])
    # get_sections.short_description = "Sections"
    

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'date', 'status', 'notes')
    list_filter = ('student__school', 'date', 'status')


@admin.register(Subjects)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'grade', 'school')

