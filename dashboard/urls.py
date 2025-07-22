from django.urls import path
from dashboard.views import *

urlpatterns = [

    path('', login_view, name='login'),
    path('logout_view/', logout_view, name='logout_view'),
    path('school/dashboard/', school_dashboard, name='school_admin_dashboard'),
    path('school/settings/', settings_view, name='settings'),
    path('update/password/', update_password, name='update_password'),
    path('students/', students_view, name="students"),
    path('subjects/', subjects, name='subjects'),
    path('subjects/add', add_subject, name='add_subject'),
    path('subject/edit/<int:pk>/', edit_subject, name='edit_subject'),
    path('subject/delete/<int:pk>/', delete_subject, name='delete_subject'),
    path('grades/', grades_view, name="grades"),
    path('grades/save/', create_edit_grade, name='create_grade'),
    path('grades/edit/<int:pk>/', create_edit_grade, name='update_grade'),
    path('grades/delete/<int:pk>/', delete_grade, name='delete_grade'),

    path('routine/setup/', routine_setup, name='routine_setup'),
    path('save_routine/', save_routine, name='save_routine'),
    path('load_routine/', load_routine, name='load_routine'),
    path('get_busy_teachers/', get_busy_teachers, name='get_busy_teachers'),


    path('detailed/student/attendance/', detailed_student_attendance, name='detailed_student_attendance'),



    path('sections/save/', create_edit_section, name='create_section'),
    path('sections/save/<int:pk>/', create_edit_section, name='update_section'),
    path('section/delete/<int:pk>/', delete_section, name='delete_section'),
    path('attendance/', overall_attendance, name='overall_attendance'),
    path('attendance/details/', attendance_details, name='attendance_details'),


    path('students/upload/', upload_students_csv, name='upload_students_csv'),
    path('get_teacher_assignments/',get_teacher_assignments, name='get_teacher_assignments'),


    path('create/students/', create_student, name='create_student'),
    path('students/update/', update_student, name='update_student'),
    path('students/delete/<int:pk>/', delete_student, name='delete_student'),

    path('teachers/', teachers_view, name='teachers'),
    path('teacher/create/', create_teacher, name='create_teacher'),
    path('teachers/update/<int:teacher_id>/', update_teacher, name='update_teacher'),
    path('teacher/delete/<int:id>/', delete_teacher, name='delete_teacher'),


    #Teacher dashboard
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('student/attendance/', attendance, name='attendance'),
    path('submit/attendance/', submit_attendance, name='submit_attendance'),
    path('routine/', teacher_routine_view, name='teacher_routine'),
    
    

    #path('assign_class_teacher/', assign_class_teacher, name='assign_class_teacher'),
    #path('get_class_teacher/', get_class_teacher, name='get_class_teacher'),
    path('import_students_csv/', import_students_csv, name='import_students_csv'),
    # path('core',code)


]
