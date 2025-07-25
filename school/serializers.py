from rest_framework import serializers
from .models import Student, Attendance, Grade, Section, TeacherProfile, Subjects, Announcement, Routine, School

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'name', 'school', 'grade_number']

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name', 'school', 'grade']

class StudentSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'name', 'grade', 'grade_name', 'section', 'section_name', 'roll_number', 'father_name', 'mother_name', 'dob', 'address', 'parents_contact']


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = '__all__'



class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'date', 'status', 'notes']




class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subjects
        fields = '__all__'
        read_only_fields = ['school']  # so clients can't set it directly


# class RoutineSerializer(serializers.ModelSerializer):
#     class Meta:
#         fields = '__all__'


class AnnouncementSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id',
            'title',
            'description',
            'type',
            'created_at',
            'updated_at',
            'school',
            'school_name',
            'created_by',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'school_name', 'created_by_name']
