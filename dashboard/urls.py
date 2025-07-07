from django.urls import path
from dashboard.views import *

urlpatterns = [
    path('', login_view, name='login'),
    path('school-admin/dashboard/', school_dashboard, name='school_admin_dashboard'),
]
