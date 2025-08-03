from django.urls import path
from .views import *

urlpatterns = [
    path('superadmin/dashboard/', superadmin_dashboard, name='superadmin_dashboard'),
    path('school/list/', school_list, name='school_list'),
    path('add/school/', add_school, name='add_school'),
    path('school/student_list/', school_wise_student, name='school_wise_student'),
]
