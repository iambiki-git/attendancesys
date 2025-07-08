from django.urls import path
from dashboard.views import *

urlpatterns = [
    path('', login_view, name='login'),
    path('logout_view/', logout_view, name='logout_view'),
    path('school/dashboard/', school_dashboard, name='school_admin_dashboard'),
    path('students/', students_view, name="students"),
    path('grades/', grades_view, name="grades"),
    path('grades/save/', create_edit_grade, name='create_grade'),
    path('grades/edit/<int:pk>/', create_edit_grade, name='update_grade'),
    path('grades/delete/<int:pk>/', delete_grade, name='delete_grade'),
    path('sections/save/', create_edit_section, name='create_section'),
    path('sections/save/<int:pk>/', create_edit_section, name='update_section'),

    path('section/delete/<int:pk>/', delete_section, name='delete_section'),
]
