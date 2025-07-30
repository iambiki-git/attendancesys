from django.contrib import admin
from .models import Student, Attendance, Grade, Section, TeacherProfile, Subjects, Routine, Announcement


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
    #list_display = ('id', 'name', 'school', 'grade', 'section', 'roll_number')
    list_display = ('id', 'name', 'school', 'grade', 'section', 'roll_number', 'father_name', 'mother_name', 'dob', 'address', 'parents_contact')
    list_filter = ('school',)

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'school', 'grade', 'section', 'phone', 'dob', 'address', 'edu_qualification', 'specialization', 'year_of_experience']

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

@admin.register(Routine)
class RoutineEntryAdmin(admin.ModelAdmin):
    list_display = ('grade', 'section', 'day', 'period_number', 'subject', 'teacher')
    list_filter = ('grade', 'section', 'day', 'teacher')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'school', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('type', 'school')

from school.models import Assignment
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'subject', 'description', 'due_date', 'assignment_file', 'created_by', 'grade', 'section', 'school', 'created_at', 'remark')