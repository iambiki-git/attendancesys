from django.urls import path
from dashboard.views import *

urlpatterns = [
    path('', login_view, name='login'),
    path('logout_view/', logout_view, name='logout_view'),
    path('school/dashboard/', school_dashboard, name='school_admin_dashboard'),
    path('students/', students_view, name="students"),
    path('grades/', grades_view, name="grades"),
    path('grades/save/', save_edit_grade, name='save_grade'),
    path('grades/edit/<int:pk>/', save_edit_grade, name='save_grade'),
    path('grades/delete/<int:pk>/', delete_grade, name='delete_grade'),
    path('sections/save/', save_section, name='save_section'),
]
