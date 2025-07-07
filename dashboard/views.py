from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from school.models import Student, Attendance
from django.contrib import messages
import requests




# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User  # or your custom User model
import requests
from django.contrib import messages
from django.shortcuts import render, redirect

# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         if not username or not password:
#             messages.error(request, 'Both username and password are required')
#             return render(request, 'dashboard/login_page.html')
        
#         try:
#             # 1. First authenticate with DRF to get tokens
#             token_response = requests.post(
#                 'http://127.0.0.1:8000/api/token/',
#                 data={'username': username, 'password': password},
#                 timeout=5
#             )
            
#             if token_response.status_code == 200:
#                 tokens = token_response.json()
#                 print(tokens)  # Debugging line to see the tokens
                
#                 # 2. Store the access token in session
#                 request.session['access_token'] = tokens['access']
                
#                 # 3. ALSO authenticate the Django session
#                 user = authenticate(request, username=username, password=password)
#                 print(user)
#                 if user is not None:
#                     login(request, user)  # This sets request.user
#                     return redirect('school_dashboard')
#                 else:
#                     messages.error(request, 'Failed to authenticate Django session')
#             else:
#                 error_msg = token_response.json().get('detail', 'Invalid credentials')
#                 messages.error(request, error_msg)
                
#         except requests.exceptions.RequestException as e:
#             messages.error(request, f'Connection error: {str(e)}')
    
#     return render(request, 'dashboard/login_page.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Both username and password are required')
            return render(request, 'dashboard/login_page.html')
        
        try:
            # 1. First authenticate with DRF to get tokens
            token_response = requests.post(
                'http://127.0.0.1:8000/api/token/',
                data={'username': username, 'password': password},
                timeout=5
            )
            
            if token_response.status_code == 200:
                tokens = token_response.json()
                request.session['access_token'] = tokens['access']
                
                # 2. Authenticate the Django session
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    
                    # 3. Check user role and redirect accordingly
                    if hasattr(user, 'is_superuser') and user.is_superuser:
                        return redirect('admin_dashboard')
                    elif hasattr(user, 'is_school_admin') and user.is_school_admin:
                        return redirect('school_admin_dashboard')
                    elif hasattr(user, 'is_teacher') and user.is_teacher:
                        return redirect('teacher_dashboard')
                    elif hasattr(user, 'is_student') and user.is_student:
                        return redirect('student_dashboard')
                    else:
                        messages.warning(request, 'User has no assigned role')
                        return redirect('default_dashboard')
                else:
                    messages.error(request, 'Failed to authenticate Django session')
            else:
                error_msg = token_response.json().get('detail', 'Invalid credentials')
                messages.error(request, error_msg)
                
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Connection error: {str(e)}')
    
    return render(request, 'dashboard/login_page.html')  



def school_dashboard(request):
    school = request.user.school
    students = Student.objects.filter(school=school)
    today = datetime.today()

    total_students = students.count()
    today_attendance = Attendance.objects.filter(student__school=school, date=today)

    present_count = today_attendance.filter(status='Present').count()
    absent_count = today_attendance.filter(status='Absent').count()

    context = {
        'school': school,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count,
        'today': today,

    }

    return render(request, 'dashboard/school_admin_dashboard.html', context)