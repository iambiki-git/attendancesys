from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from school.models import Student, Attendance, Grade, Section
from django.contrib import messages
import requests
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.core.paginator import Paginator

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

import json
from django.core.serializers.json import DjangoJSONEncoder
# def students_view(request):
#     school = request.user.school
#     grades = Grade.objects.filter(school=school)
#     sections = Section.objects.filter(school=school)
#     students = Student.objects.filter(school=school).order_by('name')

#     sections_by_grade = {}
#     for grade in grades:
#         sections_list = sections.filter(grade=grade).values_list('name', flat=True)
#         sections_by_grade[grade.grade_number] = list(sections_list)

#     context = {
#         'students': students,
#         'grades': grades,
#         'sections_by_grade': json.dumps(sections_by_grade, cls=DjangoJSONEncoder),
#     }
#     return render(request, 'dashboard/student_page.html', context)


# def students_view(request):
#     school = request.user.school
#     grades = Grade.objects.filter(school=school).order_by('grade_number')
#     sections = Section.objects.filter(school=school).order_by('name')

#     # Sections grouped by Grade
#     sections_by_grade = {}
#     for grade in grades:
#         sections_list = sections.filter(grade=grade).values_list('id', 'name')
#         sections_by_grade[grade.id] = list(sections_list)

#     grade_id = request.GET.get('grade_id')
#     section_id = request.GET.get('section_id')

#     students = Student.objects.filter(school=school)
#     if grade_id:
#         students = students.filter(grade_id=grade_id)
#     if section_id:
#         students = students.filter(section_id=section_id)
#     students = students.order_by('name')

#     return render(request, 'dashboard/student_page.html', {
#         'grades': grades,
#         'sections_by_grade': json.dumps(sections_by_grade, cls=DjangoJSONEncoder),
#         'students': students,
#         'selected_grade': grade_id,
#         'selected_section': section_id,
#     })

from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json

def students_view(request):
    school = request.user.school
    grades = Grade.objects.filter(school=school).order_by('grade_number')
    sections = Section.objects.filter(school=school).order_by('name')

    # Sections grouped by Grade
    sections_by_grade = {}
    for grade in grades:
        sections_list = sections.filter(grade=grade).values_list('id', 'name')
        sections_by_grade[grade.id] = list(sections_list)

    grade_id = request.GET.get('grade_id')
    section_id = request.GET.get('section_id')

    # Get the selected grade and section objects
    selected_grade_obj = None
    selected_section_obj = None
    
    if grade_id:
        selected_grade_obj = Grade.objects.filter(id=grade_id).first()
    if section_id:
        selected_section_obj = Section.objects.filter(id=section_id).first()

    students = Student.objects.filter(school=school)
    if grade_id:
        students = students.filter(grade_id=grade_id)
    if section_id:
        students = students.filter(section_id=section_id)
    students = students.order_by('name')

    context = {
        'grades': grades,
        'sections_by_grade': json.dumps(sections_by_grade, cls=DjangoJSONEncoder),
        'students': students,
        'selected_grade': grade_id,
        'selected_section': section_id,
        'selected_grade_obj': selected_grade_obj,  # Add this
        'selected_section_obj': selected_section_obj,  # Add this
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Handle AJAX requests differently if needed
        return JsonResponse(context)
    
    return render(request, 'dashboard/student_page.html', context)


# def create_student(request):
#     if request.method == "POST":
#         full_name = request.POST.get('full_name')
#         roll_no = int(request.POST.get('roll_no'))
#         grade_id = request.POST.get('grade_id')
#         section_id = request.POST.get('section_id')

#         # Call DRF API
#         api_url = f"{settings.API_BASE_URL}students/"
#         access_token = get_valid_access_token(request)
#         print(access_token)

#         payload = {
#             "name": full_name,
#             'roll_number': roll_no,
#             "grade": grade_id,
#             "section": section_id,
#         }

#         headers = {
#             'Authorization': f'Bearer {access_token}',
#             'Content-Type': 'application/json'
#         }

#         response = requests.post(api_url, json=payload, headers=headers)
#         if response.status_code == 201:
#             messages.success(request, "Student created successfully.")
#         else:
#             messages.error(request, f"Error: {response.status_code} {response.text}")
        

#         # Redirect back to student list page
#         return redirect(f"/students/?grade_id={grade_id}&section_id={section_id}")
    
from django.http import JsonResponse
import json

def create_student(request):
    if request.method == "POST":
        try:
            full_name = request.POST.get('full_name')
            roll_no = int(request.POST.get('roll_no'))
            grade_id = request.POST.get('grade_id')
            section_id = request.POST.get('section_id')

            if not all([full_name, roll_no, grade_id, section_id]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})

            # Call DRF API
            api_url = f"{settings.API_BASE_URL}students/"
            access_token = get_valid_access_token(request)

            payload = {
                "name": full_name,
                'roll_number': roll_no,
                "grade": grade_id,
                "section": section_id,
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 201:
                return JsonResponse({'success': True})
            else:
                error_msg = response.json().get('detail', response.text)
                return JsonResponse({'success': False, 'error': error_msg})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        

# def delete_student(request, pk):
#     if request.method != 'POST':
#         messages.error(request, 'Invalid request method.')
#         return redirect('students')

#     access_token = get_valid_access_token(request)
#     if not access_token:
#         messages.error(request, 'Session expired. Please log in again.')
#         return redirect('login')

#     api_url = f"{settings.API_BASE_URL}students/{pk}/"
#     headers = {
#         'Authorization': f'Bearer {access_token}',
#         'Content-Type': 'application/json',
#     }

#     try:
#         response = requests.delete(api_url, headers=headers)

#         if response.status_code == 204:
#             messages.success(request, 'Student deleted successfully.')
#         else:
#             try:
#                 detail = response.json()
#             except Exception:
#                 detail = response.text
#             messages.error(request, f"API Error: {detail}")

#     except requests.exceptions.RequestException as e:
#         messages.error(request, f"Failed to connect to API: {str(e)}")

#     return redirect(f"/students/?grade_id={grade_id}&section_id={section_id}")


def delete_student(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('students')

    access_token = get_valid_access_token(request)
    if not access_token:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    # Get grade and section from POST data
    grade_id = request.POST.get('grade_id')
    section_id = request.POST.get('section_id')

    # API call to delete student
    api_url = f"{settings.API_BASE_URL}students/{pk}/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.delete(api_url, headers=headers)

        if response.status_code == 204:
            messages.success(request, 'Student deleted successfully.')
        else:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            messages.error(request, f"API Error: {detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")

    # Redirect back with original filters
    redirect_url = '/students/'
    if grade_id and section_id:
        redirect_url += f'?grade_id={grade_id}&section_id={section_id}'
    return redirect(redirect_url)        



def grades_view(request):
    school = request.user.school
    grades = Grade.objects.filter(school=school).order_by('grade_number')

    # Create Paginator: 6 items per page
    paginator = Paginator(grades, 6)

    # Get current page number from GET parameter ?page=
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)



    context = {
        'page_obj':page_obj,
    }
    return render(request, 'dashboard/grades.html', context)



from attendancesys.utils import get_valid_access_token
from django.conf import settings
@login_required
def create_edit_grade(request, pk=None):
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
                messages.success(request, 'Grade created successfully!')
            else:
                messages.success(request, 'Grade updated successfully!')
        else:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            messages.error(request, f"API Error: {error_detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Failed to connect to API: {str(e)}')

    return redirect('grades')


import re
def create_edit_section(request, pk=None):
    grade_id = request.POST.get('grade_id')
    name = request.POST.get('name', '').strip()
    school = request.user.school

    if not re.search(r'[A-Za-z]', name):
        messages.error(request, 'Section must contain at least one letter.')
        return redirect('grades')
    
    if not grade_id or not name:
        messages.error(request, "All fields are required.")
        return redirect('grades')  # replace with your page name
    
    #Check if sections already exists
    if Section.objects.filter(name=name, grade=grade_id, school=school).exists():
        messages.error(request, f'Section {name} already exists.')
        return redirect('grades')

    
    access_token = get_valid_access_token(request)
    #print(access_token)

    payload = {
        'school': school.id,
        'grade': grade_id,
        'name': name
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        if pk:
            # update
            response = requests.put(
                f'{settings.API_BASE_URL}sections/{pk}/',
                json=payload,
                headers=headers
            )
            if response.status_code == 200:
                messages.success(request, 'Section updated successfully!')
            else:
                error_msg = response.json().get('detail', 'Unknown API error')
                messages.error(request, f'API Error: {error_msg}')

        else:
            # Create 
            response = requests.post(
                f'{settings.API_BASE_URL}sections/',
                json=payload,
                headers=headers
            )
            if response.status_code == 201:
                messages.success(request, 'Section created successfully!')
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

def delete_section(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('grades')

    access_token = get_valid_access_token(request)
    if not access_token:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    api_url = f"{settings.API_BASE_URL}sections/{pk}/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.delete(api_url, headers=headers)

        if response.status_code == 204:
            messages.success(request, 'Section deleted successfully.')
        else:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            messages.error(request, f"API Error: {detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")

    return redirect('grades')


def teachers_view(request):
    return render(request, 'dashboard/teachers_page.html')