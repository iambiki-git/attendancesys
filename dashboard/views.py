from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from school.models import Student, Attendance, Grade, Section
from django.contrib import messages
import requests
from django.contrib.auth import login, authenticate
from django.http import JsonResponse

# Create your views here.

def login_view(request):
    # ✅ If already logged in, redirect to dashboard
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_school_admin:
            return redirect('school_admin_dashboard')
        elif request.user.is_teacher:
            return redirect('teacher_dashboard')
        elif request.user.is_student:
            return redirect('student_dashboard')
        else:
            return redirect('default_dashboard')  # optional fallback
    
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
                request.session['refresh_token'] = tokens['refresh']
                
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


from django.contrib.auth import logout as django_logout
import logging
logger = logging.getLogger(__name__)
def logout_view(request):
    
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')

    # print(access_token)
    # print(refresh_token)

    #Step 1: Logout from JWT (blacklist refresh token)
    if access_token and refresh_token:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            requests.post(
                "http://127.0.0.1:8000/api/logout/",
                headers=headers,
                json={"refresh": refresh_token},
                timeout=5
            )
        except Exception as e:
            logger.error(f"Failed to call logout API: {e}")


    # Step 2: Django logout and session clear
    django_logout(request)
    request.session.flush()

    # Step 3: Redirect to login
    return redirect('/')  # Make sure 'login' name matches your login path


@login_required(login_url='/')
def school_dashboard(request):
    school = request.user.school
    students = Student.objects.filter(school=school)
    grades = Grade.objects.filter(school=school)
    today = datetime.today()

    total_students = students.count()
    total_grades = grades.count
    today_attendance = Attendance.objects.filter(student__school=school, date=today)

    # present_count = today_attendance.filter(status='Present').count()
    # absent_count = today_attendance.filter(status='Absent').count()

    context = {
        'school': school,
        'total_students': total_students,
        # 'present_count': present_count,
        # 'absent_count': absent_count,
        'total_grades': total_grades,
        'today': today,

    }

    return render(request, 'dashboard/school_admin_dashboard.html', context)


def students_view(request):
    return render(request, 'dashboard/student_page.html')

def grades_view(request):
    school = request.user.school
    grades = Grade.objects.filter(school=school)

    context = {
        'grades':grades,
    }
    return render(request, 'dashboard/grades.html', context)


# from django.conf import settings
# def save_grade(request):
#     print("Reached save_grade view")
#     if request.method == 'POST':
#         level = request.POST.get('level')
#         name = request.POST.get('name', '').strip()
#         school = request.user.school
#         # print(level)
#         # print(name)

#         # Basic validation
#         try:
#             level = int(level)
#             if level < 1 or level > 12:
#                 messages.error(request, 'Grade level must be between 1 and 12')
#                 return redirect('grades')
#         except (ValueError, TypeError):
#             messages.error(request, 'Invalid grade level')
#             return redirect('grades')

#         # Option 1: Save to Database directly (if you have a Grade model)
#         # from .models import Grade
#         # Grade.objects.create(level=level, name=name if name else None)
#         # messages.success(request, 'Grade saved successfully!')
#         # return redirect('grades')

#         #Check if grades already exists
#         if Grade.objects.filter(grade_number=level, school=school).exists():
#             messages.error(request, f'Grades {level} already exists.')
#             return redirect('grades')

#         # Option 2: Save via API (uncomment and fix this)
#         access_token = request.session.get('access_token')
#         #print(access_token)

#         if not access_token:
#             messages.error(request, 'Not authenticated with API')
#             return redirect('grades')
        
#         try:
#             response = requests.post(
#                 f'{settings.API_BASE_URL}grades/',
#                 json={
#                     'school': school.id,
#                     'grade_number': level,
#                     'name': name if name else None
#                 },
#                 headers={
#                     'Authorization': f'Bearer {access_token}',
#                     'Content-Type': 'application/json'
#                 }
#             )
            
#             if response.status_code == 201:
#                 messages.success(request, 'Grade saved successfully via API!')
#             else:
#                 error_msg = response.json().get('detail', 'Unknown API error')
#                 messages.error(request, f'API Error: {error_msg}')
                
#         except requests.exceptions.RequestException as e:
#             messages.error(request, f'Failed to connect to API: {str(e)}')
    
#     return redirect('grades')

from attendancesys.utils import get_valid_access_token
from django.conf import settings
@login_required
def save_edit_grade(request, pk=None):
    # print("Reached save_grade view")
    # print('pk', pk)

    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('grades')

    level = request.POST.get('level')
    name = request.POST.get('name', '').strip()
    school = request.user.school

    # Basic validation
    try:
        level = int(level)
        if level < 1 or level > 12:
            messages.error(request, 'Grade level must be between 1 and 12')
            return redirect('grades')
    except (ValueError, TypeError):
        messages.error(request, 'Invalid grade level')
        return redirect('grades')
    
    

    # Check for duplicate grade level (only for create)
    # if pk is None:
    if Grade.objects.filter(grade_number=level, school=school).exists():
        messages.error(request, f'Grade {level} already exists.')
        return redirect('grades')

    # Use access token for API
    #access_token = request.session.get('access_token')
    access_token = get_valid_access_token(request)

    print(access_token)
    if not access_token:
        messages.error(request, 'Not authenticated with API')
        return redirect('grades')

    # Prepare payload
    payload = {
        'school': school.id,
        'grade_number': level,
        'name': name if name else None
    }

    # Send request to API
    api_url = f"{settings.API_BASE_URL}grades/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        if pk is None:
            # CREATE: POST
            response = requests.post(api_url, json=payload, headers=headers)
        else:
            # UPDATE: PATCH
            api_url = f"{settings.API_BASE_URL}grades/{pk}/"
            response = requests.patch(api_url, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            if pk is None:
                messages.success(request, 'Grade created successfully via API!')
            else:
                messages.success(request, 'Grade updated successfully via API!')
        else:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            messages.error(request, f"API Error: {error_detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Failed to connect to API: {str(e)}')

    return redirect('grades')



def save_section(request):
    grade_id = request.POST.get('grade_id')
    name = request.POST.get('name')
    school = request.user.school

    if not grade_id or not name:
        messages.error(request, "All fields are required.")
        return redirect('grades')  # replace with your page name
    
    #Check if sections already exists
    if Section.objects.filter(name=name, grade=grade_id, school=school).exists():
        messages.error(request, f'Section {name} already exists.')
        return redirect('grades')
    
    access_token = get_valid_access_token(request)
    print(access_token)
    
    try:
        response = requests.post(
            f'{settings.API_BASE_URL}sections/',
            json={
                'school': school.id,
                'grade': grade_id,
                'name': name if name else None
            },
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 201:
            messages.success(request, 'Section saved successfully via API!')
        else:
            error_msg = response.json().get('detail', 'Unknown API error')
            messages.error(request, f'API Error: {error_msg}')
            
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Failed to connect to API: {str(e)}')

    return redirect('grades')

def delete_grade(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('grades')

    access_token = get_valid_access_token(request)
    if not access_token:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    api_url = f"{settings.API_BASE_URL}grades/{pk}/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.delete(api_url, headers=headers)

        if response.status_code == 204:
            messages.success(request, 'Grade deleted successfully.')
        else:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            messages.error(request, f"API Error: {detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")

    return redirect('grades')
