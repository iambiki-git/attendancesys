from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime
from school.models import Student, Attendance, Grade, Section, TeacherProfile, Subjects
from users.models import School
from django.contrib import messages
import requests
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.http import JsonResponse
from django.core.paginator import Paginator

# Create your views here.

def login_view(request):
    # ✅ If already logged in, redirect to dashboard
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('superadmin_dashboard')
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
                        return redirect('superadmin_dashboard')
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


# from django.http import HttpResponseForbidden
# from datetime import datetime, timedelta
# @login_required(login_url='/')
# def school_dashboard(request):
#     if not request.user.is_staff and not request.user.is_school_admin:
#         return HttpResponseForbidden("You are not authorized to access this page.")
    
#     school = request.user.school
#     students = Student.objects.filter(school=school)
#     teachers = TeacherProfile.objects.filter(school=school)
#     grades = Grade.objects.filter(school=school)
#     today = datetime.today()

#     total_students = students.count()
#     total_teachers = teachers.count()
#     total_grades = grades.count

#     # Define the week range (Sunday to Friday)
#     start_of_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)

#     labels = []
#     present_data = []
#     absent_data = []
#     late_data = []

#     for i in range(6):  # Sunday to Friday
#         day = start_of_week + timedelta(days=i)
#         labels.append(day.strftime('%a'))  # "Sun", "Mon", etc.

#         daily_qs = Attendance.objects.filter(student__school=school, date=day)

#         present_data.append(daily_qs.filter(status='Present').count())
#         absent_data.append(daily_qs.filter(status='Absent').count())
#         late_data.append(daily_qs.filter(status='Late').count())


#     context = {
#         'school': school,
#         'total_students': total_students,
#         'total_teachers': total_teachers,
#         'total_grades': total_grades,
#         'today': today,

#         'attendance_labels': json.dumps(labels),
#         'present_data': json.dumps(present_data),
#         'absent_data': json.dumps(absent_data),
#         'late_data': json.dumps(late_data),

#     }

#     return render(request, 'dashboard/school_dashboard/school_admin_dashboard.html', context)


from datetime import datetime, timedelta
import json
from django.http import HttpResponseForbidden

@login_required(login_url='/')
def school_dashboard(request):
    if not request.user.is_staff and not request.user.is_school_admin:
        return HttpResponseForbidden("You are not authorized to access this page.")

    school = request.user.school
    today = datetime.today().date()
    today_bs = nepali_datetime.date.from_datetime_date(today)
    today_bs_str = today_bs.strftime('%K %B %d, %Y')  # e.g., 2081 Shrawan 04, 2081

    students = Student.objects.filter(school=school)
    teachers = TeacherProfile.objects.filter(school=school)
    grades = Grade.objects.filter(school=school)
    sections = Section.objects.filter(grade__in=grades).order_by('name')

    # Group sections by grade.id → ['A', 'B', ...]
    sections_by_grade = {
        grade.id: list(sections.filter(grade=grade).values_list('name', flat=True))
        for grade in grades
    }
        

    total_students = students.count()
    total_teachers = teachers.count()
    total_grades = grades.count()

    # Week Range (Sun to Fri)
    start_of_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    week_days = [start_of_week + timedelta(days=i) for i in range(6)]
    labels = [day.strftime('%a') for day in week_days]

    # === Overall attendance ===
    overall_present, overall_absent, overall_late = [], [], []
    for day in week_days:
        qs = Attendance.objects.filter(student__school=school, date=day)
        overall_present.append(qs.filter(status='Present').count())
        overall_absent.append(qs.filter(status='Absent').count())
        overall_late.append(qs.filter(status='Late').count())


    # === Handle GET params (if any) ===
    grade_id = request.GET.get('grade')
    section_name = request.GET.get('section')

    selected_grade = Grade.objects.filter(id=grade_id).first() if grade_id else None

    # Fetch the Section object by name and grade
    selected_section = None
    if section_name and selected_grade:
        selected_section = Section.objects.filter(name=section_name, grade=selected_grade, school=school).first()

    show_section_chart = selected_grade and section_name

    section_present, section_absent, section_late = [], [], []

    if show_section_chart:
        for day in week_days:
            qs = Attendance.objects.filter(
                student__school=school,
                student__grade=selected_grade,
                student__section=selected_section,
                date=day
            )
            section_present.append(qs.filter(status='Present').count())
            section_absent.append(qs.filter(status='Absent').count())
            section_late.append(qs.filter(status='Late').count())

    context = {
        'school': school,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_grades': total_grades,
        'today': today,
        'today_bs_str': today_bs_str,
        'grades': grades,
        'sections_by_grade': json.dumps(sections_by_grade, cls=DjangoJSONEncoder),

        'attendance_labels': json.dumps(labels),

        'overall_present_data': json.dumps(overall_present),
        'overall_absent_data': json.dumps(overall_absent),
        'overall_late_data': json.dumps(overall_late),

        'selected_grade_id': int(grade_id) if grade_id else None,
        'selected_section': selected_section.name if selected_section else None,
        'section_present_data': json.dumps(section_present),
        'section_absent_data': json.dumps(section_absent),
        'section_late_data': json.dumps(section_late),
        'show_section_chart': show_section_chart,
    }

    return render(request, 'dashboard/school_dashboard/school_admin_dashboard.html', context)



def settings_view(request):
    return render(request, 'dashboard/school_dashboard/settings.html')

def update_password(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Check if current password is correct
        if not user.check_password(current_password):
            messages.error(request, "Your current password is incorrect.")
            return redirect('settings') 
        
        # Check if new password and confirm match
        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('settings')
        
        # Set new password
        user.set_password(new_password)
        user.save()

        # Keep user logged in after password change
        update_session_auth_hash(request, user)

        messages.success(request, "Your password has been updated successfully.")
        return redirect('settings')
    else:
        return redirect('settings')
    

from django.core.serializers.json import DjangoJSONEncoder
import json

def students_view(request):
    if not request.user.is_staff and not request.user.is_school_admin:
        return HttpResponseForbidden("You are not authorized to access this page.")
    
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

    # Pagination
    # paginator = Paginator(students, 3)  # Show 10 students per page
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)

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
    
    return render(request, 'dashboard/school_dashboard/student_page.html', context)


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
            roll_no = request.POST.get('roll_no')
            grade_id = request.POST.get('grade_id')
            section_id = request.POST.get('section_id')

            if not all([full_name, roll_no, grade_id, section_id]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})

            # Validate duplicate roll number in same grade-section
            if Student.objects.filter(
                roll_number=roll_no,
                grade_id=grade_id,
                section_id=section_id
            ).exists():
                return JsonResponse({'success': False, 'error': f'Roll number {roll_no} already exists in this class section.'})

            # Prepare API call
            api_url = f"{settings.API_BASE_URL}students/"
            access_token = get_valid_access_token(request)

            payload = {
                "name": full_name,
                "roll_number": int(roll_no),
                "grade": int(grade_id),
                "section": int(section_id),
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


def update_student(request):
    try:
        student_id = request.POST.get('student_id')
        name = request.POST.get('name')
        roll_no = request.POST.get('roll_no')
        
        if not all([student_id, name, roll_no]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        student = Student.objects.get(id=student_id)
        student.name = name
        student.roll_number = roll_no
        student.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Student information updated successfully!',
            'updated_data': {
                'name': name,
                'roll_no': roll_no
            }
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


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
    if not request.user.is_staff and not request.user.is_school_admin:
        return HttpResponseForbidden("You are not authorized to access this page.")
    
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
    return render(request, 'dashboard/school_dashboard/grades.html', context)



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

    #print(access_token)
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
    if not request.user.is_staff and not request.user.is_school_admin:
        return HttpResponseForbidden("You are not authorized to access this page.")
    
    school = request.user.school
    grades = Grade.objects.filter(school=school).order_by('grade_number')
    sections = Section.objects.filter(school=school).order_by('name')
    subjects = Subjects.objects.filter(school=school).order_by('id')

    all_teachers = TeacherProfile.objects.filter(school=school).order_by('user__first_name')
    #print(teachers)

    # Prepare sections data grouped by grade
    sections_by_grade = {}
    for grade in grades:
        sections_by_grade[grade.id] = [
            {'id': section.id, 'name': section.name} 
            for section in sections.filter(grade=grade)
        ]

    # Pagination
    paginator = Paginator(all_teachers, 6)  # Show 10 teachers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'grades': grades,
        'sections': sections,  # All sections for initial load
        'sections_by_grade': json.dumps(sections_by_grade),
        'teachers': page_obj,
        'subjects': subjects,
        'all_teachers': all_teachers,
    }
    return render(request, 'dashboard/school_dashboard/teachers_page.html', context)


from django.contrib.auth import get_user_model
User = get_user_model()
def create_teacher(request):
    if request.method == "POST":
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        school=request.user.school

        # grade_id = request.POST.get('grade_level')
        # section_id = request.POST.get('section')
        # subjects = request.POST.get('subject')

        # Validate required fields
        if not all([username, email, password, first_name, last_name]):
            messages.error(request, "All required fields must be filled.")
            return redirect('teachers')
        
        # if not all([username, email, password, grade_id, section_id]):
        #     messages.error(request, "All required fields must be filled.")
        #     return redirect('teachers')

        # Check for duplicates
        if User.objects.filter(username=username, school=school).exists():
            messages.warning(request, "Username already taken.")
            return redirect('teachers')

        if User.objects.filter(email=email, school=school).exists():
            messages.warning(request, "Email already registered.")
            return redirect('teachers')

        try:
            school = request.user.school  # Logged-in admin को school

            # ✅ Create teacher user
            teacher_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                school=school,
                is_teacher=True
            )

            # ✅ Get Grade and Section
            # grade = Grade.objects.get(id=grade_id, school=school)
            # section = Section.objects.get(id=section_id, school=school)

            # ✅ Create TeacherProfile & link Grade, Section, Subject
            profile = TeacherProfile.objects.create(
                user=teacher_user,
                school=school,
                # grade=grade,
                # section=section,
                #subjects=subjects
            )

            messages.success(request, f"Teacher '{username}' created successfully!")
            return redirect('teachers')

        except Exception as e:
            if 'teacher_user' in locals():
                teacher_user.delete()
            messages.error(request, f"Error creating teacher: {str(e)}")
            return redirect('teachers')

    # GET: Render form with Grade & Section dropdown
    # grades = Grade.objects.filter(school=request.user.school)
    # sections = Section.objects.filter(school=request.user.school)

    # context = {
    #     'grades': grades,
    #     'sections': sections
    # }

    return render(request, 'teachers/create_teacher.html')


from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()

def update_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(TeacherProfile, user__id=teacher_id, school=request.user.school)
        
        try:
            user = teacher.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.username = request.POST.get('username', user.username)
            user.save()
            
            grade_id = request.POST.get('grade_level')
            teacher.grade = get_object_or_404(Grade, id=grade_id, school=request.user.school) if grade_id else None

            section_id = request.POST.get('section')
            teacher.section = get_object_or_404(Section, id=section_id, school=request.user.school) if section_id else None
            
            teacher.save()
            
            return JsonResponse({
                'success': True,
                'teacher': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'username': user.username,
                    'grade': teacher.grade.grade_number if teacher.grade else None,
                    'section': teacher.section.name if teacher.section else None,
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


from django.utils import timezone
import nepali_datetime
from collections import Counter

def teacher_dashboard(request):
    teacher = request.user.teacherprofile
    grade = teacher.grade
    section = teacher.section
    today_ad = timezone.now().date()
    today_bs = nepali_datetime.date.from_datetime_date(today_ad)
    first_day_of_month = today_ad.replace(day=1)


    nepali_weekday = today_bs.strftime("%A")
    nepali_date_str = today_bs.strftime("%B %d, %Y")

    start_of_week = today_ad - timedelta(days=(today_ad.weekday() + 1) % 7)  # Sunday
    week_dates = [start_of_week + timedelta(days=i) for i in range(6)]  # Sunday to Friday

    weekly_attendance_summary = []
    for date in week_dates:
        day_attendance = Attendance.objects.filter(
            student__grade=grade,
            student__section=section,
            student__school=teacher.school,
            date=date
        )
        counts = Counter([a.status for a in day_attendance])
        weekly_attendance_summary.append({
            'date': nepali_datetime.date.from_datetime_date(date).strftime('%A'),  # e.g., 'आइतबार'
            'present': counts.get('Present', 0) + counts.get('Late', 0),
            'absent': counts.get('Absent', 0),
            'late': counts.get('Late', 0),
        })

        #Todays classes
        today = datetime.today().strftime('%A')
        teacher_profile = TeacherProfile.objects.get(user=request.user)
        routines = Routine.objects.filter(
            teacher=teacher_profile,
            day=today
        ).order_by('period_number')


    # Step 1: Filter records for the month
    monthly_attendance = Attendance.objects.filter(
        student__grade=grade,
        student__section=section,
        student__school=teacher.school,
        date__range=(first_day_of_month, today_ad)
    )

    # Step 2: Total unique attendance days
    unique_dates = monthly_attendance.values_list('date', flat=True).distinct()
    school_days = unique_dates.count()

    # total students
    students = Student.objects.filter(
        grade=grade,
        section=section,
        school=teacher.school
    )
    students_count = students.count()

    # Step 4: Total expected attendance records
    total_possible_attendance = school_days * students_count

    # Step 5: Actual Present + Late records
    total_present = monthly_attendance.filter(status__in=['Present', 'Late']).count()

    # Step 6: Calculate percentage
    overall_attendance_percent = round((total_present / total_possible_attendance) * 100, 2) if total_possible_attendance > 0 else 0

    # Present = Present + Late
    present_count = Attendance.objects.filter(
        student__grade=grade,
        student__section=section,
        student__school=teacher.school,
        date=today_ad,
        status__in=['Present', 'Late']
    ).count()

    # Absent
    absent_count = Attendance.objects.filter(
        student__grade=grade,
        student__section=section,
        student__school=teacher.school,
        date=today_ad,
        status='Absent'
    ).count()

    # Late 
    late_count = Attendance.objects.filter(
        student__grade=grade,
        student__section=section,
        student__school=teacher.school,
        date=today_ad,
        status='Late'
    ).count()

    # Attendance percentage late lai ni present manne
    #attendance_percentage = round((present_count / students_count) * 100 if students_count > 0 else 0)
    # Calculate percentages
    present_percent = round((present_count / students_count) * 100, 2) if students_count > 0 else 0
    late_percent = round((late_count / students_count) * 100, 2) if students_count > 0 else 0
    absent_percent = round((absent_count / students_count) * 100, 2) if students_count > 0 else 0
    
    context = {
        'students_count': students_count,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'overall_attendance_percent': overall_attendance_percent,
        'present_percent': present_percent,
        'late_percent': late_percent,
        'absent_percent': absent_percent,
        'teacher': teacher,
        'grade': grade,
        'section': section,
        'current_date_ad': today_ad,
        'current_date_bs': today_bs,
        'nepali_weekday': nepali_weekday,
        'nepali_date_str': nepali_date_str,
        'weekly_attendance_summary': weekly_attendance_summary,
        'todays_classes': routines

    }
    return render(request, 'dashboard/teachers/teacher_dashboard.html', context)


from django.utils import timezone
from datetime import date
from django.views.decorators.http import require_POST
from django.conf import settings
def is_existing_record(student_id, date_str):
    return Attendance.objects.filter(student_id=student_id, date=date_str).exists()

def attendance(request):
    teacher = request.user.teacherprofile
    grade = teacher.grade
    section = teacher.section
    today = timezone.now().date()

    students = Student.objects.filter(
        grade=grade,
        section=section,
        school=teacher.school
    ).order_by('roll_number')

    for student in students:
        record = Attendance.objects.filter(student=student, date=today).first()
        student.attendance_status_today = record.status if record else "Not Marked"
        student.note_today = record.notes if record else ""

    attendance_submitted = Attendance.objects.filter(
        student__grade=grade,
        student__section=section,
        student__school=teacher.school,
        date=today
    ).exists()

    context = {
        'students': students,
        'current_date': date.today(),
        'attendance_submitted': attendance_submitted,
    }
    return render(request, 'dashboard/teachers/attendance_page.html', context)


@require_POST
def submit_attendance(request):
    access_token = get_valid_access_token(request)
    API_URL = f"{settings.API_BASE_URL}attendance/"
    HEADERS = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        attendance_date = request.POST.get("attendance_date", "").strip()
        if not attendance_date:
            attendance_date = timezone.now().date().strftime('%Y-%m-%d')

        for key, value in request.POST.items():
            if key.startswith('student_'):
                student_id = key.split('_')[1]
                payload = {
                    "student": str(student_id),
                    "date": attendance_date,
                    "status": value,
                    "notes": request.POST.get(f"note_{student_id}", "").strip()
                        if value in ["Absent", "Late"] else ""
                }

                attendance_id = get_existing_attendance_id(student_id, attendance_date)

                if attendance_id:
                    endpoint = f"{API_URL}{attendance_id}/"
                    response = requests.patch(
                        endpoint,
                        headers=HEADERS,
                        json=payload,
                        timeout=5
                    )
                else:
                    response = requests.post(
                        API_URL,
                        headers=HEADERS,
                        json=payload,
                        timeout=5
                    )

                if response.status_code not in [200, 201]:
                    try:
                        error_data = response.json()
                    except ValueError:
                        error_data = response.text or "Unknown error"
                    messages.error(request, f"Error for student {student_id}: {error_data}")
                    return redirect('attendance')

        messages.success(request, "Attendance saved successfully!")
        return redirect('attendance')

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Connection failed: {str(e)}")
        return redirect('attendance')



def get_existing_attendance_id(student_id, date_str):
    record = Attendance.objects.filter(student_id=student_id, date=date_str).first()
    return record.id if record else None


from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
def delete_teacher(request, id):
    teacher = User.objects.get(id=id, is_teacher=True)
    teacher.delete()
    messages.success(request, 'Teacher deleted successfully.')
    return redirect('teachers')
    

def subjects(request):
    grade_id = request.GET.get('grade_id')
    section_id = request.GET.get('section_id')
    school = request.user.school

    grades = Grade.objects.filter(school=school)
    sections = Section.objects.filter(grade_id=grade_id) if grade_id else Section.objects.none()

    subjects = Subjects.objects.filter(grade_id=grade_id) if grade_id else []

    context = {
        'grades': grades,
        'sections': sections,
        'subjects': subjects,
        'selected_grade': Grade.objects.filter(id=grade_id).first() if grade_id else None,
        'selected_section': Section.objects.filter(id=section_id).first() if section_id else None,
    }
    return render(request, 'dashboard/school_dashboard/subjects.html', context)


def add_subject(request):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('subjects')  # adjust this to your subjects list URL name

    subject_name = request.POST.get('name')
    grade_id = request.POST.get('grade_id')  # 👈 get grade
    school = request.user.school
    if not subject_name:
        messages.error(request, 'Subject name cannot be empty.')
        return redirect('subjects')
    
    if Subjects.objects.filter(name=subject_name, school=school).exists():
        messages.error(request, 'This subject is already exists.')
        return redirect('subjects')

    access_token = get_valid_access_token(request)
    if not access_token:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    api_url = f"{settings.API_BASE_URL}subjects/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'name': subject_name,
        'grade': grade_id,
        'school': school.id
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 201:
            messages.success(request, f'Subject "{subject_name}" added successfully.')
        else:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            messages.error(request, f"API Error: {detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")

    return redirect(f"{reverse('subjects')}?grade_id={grade_id}")



def delete_subject(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('subjects')  # adjust to your subjects list URL name

    grade_id = request.POST.get('grade_id')  # 👈 get grade

    # Example: get access token (replace with your logic)
    access_token = get_valid_access_token(request)
    if not access_token:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    # Build API URL for the DRF endpoint
    api_url = f"{settings.API_BASE_URL}subjects/{pk}/"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.delete(api_url, headers=headers)

        if response.status_code == 204:
            messages.success(request, 'Subject deleted successfully.')
        else:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            messages.error(request, f"API Error: {detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")

    return redirect(f"{reverse('subjects')}?grade_id={grade_id}")


def edit_subject(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('subjects')

    new_name = request.POST.get('name')
    grade_id = request.POST.get('grade_id')  # 👈 get grade

    if not new_name:
        messages.error(request, 'Subject name cannot be empty.')
        return redirect('subjects')

    access_token = get_valid_access_token(request)
    if not access_token:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')

    api_url = f"{settings.API_BASE_URL}subjects/{pk}/"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {'name': new_name}

    try:
        response = requests.patch(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            messages.success(request, f'Subject updated successfully.')
        else:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            messages.error(request, f"API Error: {detail}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")

    return redirect(f"{reverse('subjects')}?grade_id={grade_id}")



from collections import OrderedDict
def overall_attendance(request):
    school = request.user.school

    grades = Grade.objects.filter(school=school).order_by('grade_number')
    all_sections = Section.objects.filter(school=school).order_by('name')
    sections = all_sections

    # Get filters from GET request
    grade_id = request.GET.get('grade')
    section_id = request.GET.get('section')
    date_range = request.GET.get('date_range', 'today')  # default: today

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')  

    # Only filter visible sections for dropdown if a grade is selected
    if grade_id:
        sections = all_sections.filter(grade_id=grade_id)
    else:
        sections = Section.objects.none()

    # section by grade (corrected)
    sections_by_grade = {}
    for grade in grades:
        sections_list = list(all_sections.filter(grade=grade).values('id', 'name'))
        sections_by_grade[grade.id] = sections_list 

    attendance = Attendance.objects.filter(student__school=school).order_by('-date')

    # Apply filters
    if grade_id:
        attendance = attendance.filter(student__grade_id=grade_id)
    if section_id:
        attendance = attendance.filter(student__section_id=section_id)
    
    # Date filter
    today = timezone.now().date()
    if date_range == "today":
        attendance = attendance.filter(date=today)

    elif date_range == "week":
        week_start = today - timedelta(days=today.weekday())
        attendance = attendance.filter(date__range=(week_start, today))

    elif date_range == "month":
        month_start = today.replace(day=1)
        attendance = attendance.filter(date__range=(month_start, today))

    elif date_range == "custom" and start_date and end_date:
        attendance = attendance.filter(date__range=(start_date, end_date))


    #Counts
    total_count = attendance.count()     
    # Count by status
    present_count = attendance.filter(status='Present').count()
    absent_count = attendance.filter(status='Absent').count()
    late_count = attendance.filter(status='Late').count()

    # Compute percentages safely
    if total_count > 0:
        present_percent = round((present_count / total_count) * 100, 1)
        absent_percent = round((absent_count / total_count) * 100, 1)
        late_percent = round((late_count / total_count) * 100, 1)
    else:
        present_percent = absent_percent = late_percent = 0

    
    # Weekly data (7 days)
    weekly_data = OrderedDict()
    for i in range(6, -1, -1):  # Last 7 days
        day = today - timedelta(days=i)
        day_label = day.strftime('%a')  # Mon, Tue...
        count = attendance.filter(date=day).count()
        weekly_data[day_label] = count

    context = {
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,

        'present_percent': present_percent,
        'absent_percent': absent_percent,
        'late_percent': late_percent,

        'grades': grades,
        'sections': sections,
        'sections_by_grade': sections_by_grade,

        'selected_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'selected_grade': grade_id,
        'selected_section': section_id,

        'weekly_data': list(weekly_data.items()),  # list of tuples (label, count)


    }
    return render(request, 'dashboard/school_dashboard/overall_attendance.html', context)


from django.http import HttpResponseBadRequest
@login_required
def attendance_details(request):
    school = request.user.school
    status = request.GET.get("status")
    grade_id = request.GET.get("grade")
    section_id = request.GET.get("section")
    date_range = request.GET.get("date_range")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    #Handle empty strings and "None"
    if grade_id in ["", "None"]: grade_id = None
    if section_id in ["", "None"]: section_id = None
    if date_range in ["", "None", None]: date_range = "today"

    if status not in ['present', 'absent', 'late']:
        return HttpResponseBadRequest("Invalid status")

    attendance_qs = Attendance.objects.filter(
        status__iexact=status.capitalize(),
        student__school=school
    )

    # Optional grade/section filter
    if grade_id:
        attendance_qs = attendance_qs.filter(student__grade_id=grade_id)
    if section_id:
        attendance_qs = attendance_qs.filter(student__section_id=section_id)

    today = timezone.now().date()

    try:
        if date_range == "today":
            attendance_qs = attendance_qs.filter(date=today)

        elif date_range == "week":
            week_start = today - timedelta(days=today.weekday())
            attendance_qs = attendance_qs.filter(date__range=(week_start, today))

        elif date_range == "month":
            month_start = today.replace(day=1)
            attendance_qs = attendance_qs.filter(date__range=(month_start, today))

        elif date_range == "custom":
            if start_date and end_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                attendance_qs = attendance_qs.filter(date__range=(start, end))
            # else: don’t filter by date
        else:
            # No date range passed → fallback to dashboard default (e.g. today)
            attendance_qs = attendance_qs.filter(date=today)
    except Exception as e:
        return HttpResponseBadRequest(f"Date error: {str(e)}")

    attendance_qs = attendance_qs.select_related('student').order_by('-date')[:100]

    return render(request, 'dashboard/school_dashboard/attendance_modal_list.html', {
        "attendance_list": attendance_qs,
    })



import csv
def upload_students_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        grade_id = request.POST.get('grade_id')
        section_id = request.POST.get('section_id')

        # Validate grade and section
        try:
            grade = Grade.objects.get(id=grade_id)
            section = Section.objects.get(id=section_id)
        except (Grade.DoesNotExist, Section.DoesNotExist):
            messages.error(request, "Invalid Grade or Section.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Read and parse the CSV file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        created_count = 0
        for row in reader:
            if len(row) < 2:
                continue  # Skip malformed rows

            name, roll_no = row[0].strip(), row[1].strip()
            if name and roll_no:
                Student.objects.create(
                    name=name,
                    roll_number=roll_no,
                    grade=grade,
                    section=section
                )
                created_count += 1

        messages.success(request, f"{created_count} students imported successfully.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    messages.error(request, "No CSV file uploaded.")
    return redirect(request.META.get('HTTP_REFERER', '/'))




def get_teacher_assignments(request):
    school = request.user.school
    routines = Routine.objects.filter(school=school)

    teacher_map = {}

    for r in routines:
        key = f"{r.day}-{r.period_number}"
        tid = str(r.teacher.id)

        if tid not in teacher_map:
            teacher_map[tid] = set()
        teacher_map[tid].add(key)

    for k in teacher_map:
        teacher_map[k] = list(teacher_map[k])

    return JsonResponse(teacher_map)


def routine_setup(request):
    school = request.user.school
    grades = Grade.objects.filter(school=school).order_by('grade_number')
    sections = Section.objects.filter(school=school).order_by('name')
    subjects = Subjects.objects.filter(school=school)
    teachers = TeacherProfile.objects.filter(school=school)

    sections_by_grade = {}
    for grade in grades:
        sections_list = list(sections.filter(grade=grade).values('id', 'name'))
        sections_by_grade[grade.id] = sections_list

     # ✅ Prepare subject mapping
    subjects_by_grade = {}
    for grade in grades:
        subjects_list = list(subjects.filter(grade=grade).values('id', 'name'))
        subjects_by_grade[grade.id] = subjects_list


    context = {
        'grades': grades,
        'sections_by_grade': sections_by_grade,
        #'subjects': subjects,
        'subjects_by_grade': subjects_by_grade,  # ✅ Added
        'teachers': teachers,
    }
    return render(request, 'dashboard/school_dashboard/routine_setupp.html', context)


# views.py
import traceback
from django.views.decorators.csrf import csrf_exempt
from school.models import Routine
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# @csrf_exempt
# def save_routine(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             routines = data.get('routines', {})
#             period_names = data.get('period_names', {})

#             school = request.user.school  # assuming you're using request.user

#             for key, daily_routine in routines.items():
#                 grade_id, section_id = map(int, key.split('-'))
#                 grade = Grade.objects.get(id=grade_id)
#                 section = Section.objects.get(id=section_id)

#                 for day, periods in daily_routine.items():
#                     for period_str, entry in periods.items():
#                         period_number = int(period_str)
#                         subject_id = entry.get('subject_id')
#                         teacher_id = entry.get('teacher_id')

#                         if not subject_id or not teacher_id:
#                             continue

#                         subject = Subjects.objects.get(id=subject_id)
#                         teacher = TeacherProfile.objects.get(id=teacher_id)

#                         # ❌ Check for conflict in other sections
#                         conflict = Routine.objects.filter(
#                             day=day,
#                             period_number=period_number,
#                             teacher=teacher,
#                             school=school
#                         ).exclude(grade=grade, section=section).exists()

#                         if conflict:
#                             return JsonResponse({
#                                 'success': False,
#                                 'error': f"❌ Conflict: Teacher '{teacher.user.get_full_name()}' is already assigned on {day}, Period {period_number} in another class."
#                             })

#                         # ✅ Save or update
#                         Routine.objects.update_or_create(
#                             day=day,
#                             period_number=period_number,
#                             grade=grade,
#                             section=section,
#                             school=school,
#                             defaults={
#                                 'subject': subject,
#                                 'teacher': teacher
#                             }
#                         )


#             return JsonResponse({'success': True})
        
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})

#     return JsonResponse({'success': False, 'error': 'Invalid request method'})

# @csrf_exempt
# def save_routine(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             routines = data.get('routines', {})
#             period_names = data.get('period_names', {})

#             school = request.user.school  # assuming you're using request.user

#             for key, daily_routine in routines.items():
#                 grade_id, section_id = map(int, key.split('-'))
#                 grade = Grade.objects.get(id=grade_id)
#                 section = Section.objects.get(id=section_id)

#                 class_teacher_set = False  # Track if class teacher is already set

#                 for day, periods in daily_routine.items():
#                     for period_str, entry in periods.items():
#                         period_number = int(period_str)
#                         subject_id = entry.get('subject_id')
#                         teacher_id = entry.get('teacher_id')

#                         if not subject_id or not teacher_id:
#                             continue

#                         subject = Subjects.objects.get(id=subject_id)
#                         teacher = TeacherProfile.objects.get(id=teacher_id)

#                         # ❌ Check for conflict in other sections
#                         conflict = Routine.objects.filter(
#                             day=day,
#                             period_number=period_number,
#                             teacher=teacher,
#                             school=school
#                         ).exclude(grade=grade, section=section).exists()

#                         if conflict:
#                             return JsonResponse({
#                                 'success': False,
#                                 'error': f"❌ Conflict: Teacher '{teacher.user.get_full_name()}' is already assigned on {day}, Period {period_number} in another class."
#                             })

#                         # ✅ Save or update routine
#                         Routine.objects.update_or_create(
#                             day=day,
#                             period_number=period_number,
#                             grade=grade,
#                             section=section,
#                             school=school,
#                             defaults={
#                                 'subject': subject,
#                                 'teacher': teacher
#                             }
#                         )

#                         # # ✅ Set Class Teacher if Sunday Period 1
#                         # if day == "Sunday" and period_number == 1 and not class_teacher_set:
#                         #     teacher.grade = grade
#                         #     teacher.section = section
#                         #     teacher.save()
#                         #     class_teacher_set = True

#                         if day == "Sunday" and period_number == 1 and not class_teacher_set:
#                             # Unset any previous class teacher assigned to this grade-section
#                             TeacherProfile.objects.filter(
#                                 grade=grade,
#                                 section=section
#                             ).exclude(id=teacher.id).update(
#                                 grade=None,
#                                 section=None
#                             )

#                             # Set the current teacher as class teacher (if not already)
#                             if teacher.grade_id != grade.id or teacher.section_id != section.id:
#                                 teacher.grade = grade
#                                 teacher.section = section
#                                 teacher.save()

#                             class_teacher_set = True


#             return JsonResponse({'success': True})
        
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})

#     return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@login_required
def save_routine(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            routines = data.get('routines', {})
            period_names = data.get('period_names', {})

            school = request.user.school  # assuming you're using request.user

            for key, daily_routine in routines.items():
                grade_id, section_id = map(int, key.split('-'))
                grade = Grade.objects.get(id=grade_id)
                section = Section.objects.get(id=section_id)

                class_teacher_set = False  # Track if class teacher is already set

                for day, periods in daily_routine.items():
                    # ✅ Step 1: Delete any removed periods
                    existing_periods = Routine.objects.filter(
                        grade=grade,
                        section=section,
                        day=day,
                        school=school
                    ).values_list('period_number', flat=True)

                    submitted_periods = [int(p) for p in periods.keys()]
                    to_delete = set(existing_periods) - set(submitted_periods)

                    if to_delete:
                        Routine.objects.filter(
                            grade=grade,
                            section=section,
                            day=day,
                            school=school,
                            period_number__in=to_delete
                        ).delete()

                    # ✅ Step 2: Save or update submitted periods
                    for period_str, entry in periods.items():
                        period_number = int(period_str)
                        subject_id = entry.get('subject_id')
                        teacher_id = entry.get('teacher_id')

                        if not subject_id or not teacher_id:
                            return JsonResponse({
                                'success': False,
                                'error': f"⚠️ Missing subject or teacher on {day}, Period {period_number} in Grade {grade.grade_number} {section.name}."
                            })

                        subject = Subjects.objects.get(id=subject_id)
                        teacher = TeacherProfile.objects.get(id=teacher_id)

                        # ❌ Check for conflict in other sections
                        conflict = Routine.objects.filter(
                            day=day,
                            period_number=period_number,
                            teacher=teacher,
                            school=school
                        ).exclude(grade=grade, section=section).exists()

                        if conflict:
                            return JsonResponse({
                                'success': False,
                                'error': f"❌ Conflict: Teacher '{teacher.user.get_full_name()}' is already assigned on {day}, Period {period_number} in another class."
                            })

                        # ✅ Save or update routine
                        Routine.objects.update_or_create(
                            day=day,
                            period_number=period_number,
                            grade=grade,
                            section=section,
                            school=school,
                            defaults={
                                'subject': subject,
                                'teacher': teacher
                            }
                        )

                        # ✅ Set or update Class Teacher if Sunday Period 1
                        if day == "Sunday" and period_number == 1 and not class_teacher_set:
                            # Unset any previous class teacher assigned to this grade-section
                            TeacherProfile.objects.filter(
                                grade=grade,
                                section=section
                            ).exclude(id=teacher.id).update(
                                grade=None,
                                section=None
                            )

                            # Set the current teacher as class teacher
                            if teacher.grade_id != grade.id or teacher.section_id != section.id:
                                teacher.grade = grade
                                teacher.section = section
                                teacher.save()

                            class_teacher_set = True

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def load_routine(request):
    grade_id = request.GET.get('grade')
    section_id = request.GET.get('section')

    if not grade_id or not section_id:
        return JsonResponse({'error': 'Missing grade or section'}, status=400)

    key = f"{grade_id}-{section_id}"
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    routine_data = {key: {day: {} for day in days}}

    routines = Routine.objects.filter(grade_id=grade_id, section_id=section_id)

    for entry in routines:
        day = entry.day
        period = entry.period_number

        routine_data[key][day][period] = {
            "subject_id": entry.subject.id,
            "subject": entry.subject.name,
            "teacher_id": entry.teacher.id,
            "teacher": entry.teacher.user.get_full_name(),
        }

    return JsonResponse({'routine': routine_data})





# @login_required
# def get_busy_teachers(request):
#     day = request.GET.get('day')
#     period = request.GET.get('period')

#     if not day or not period:
#         return JsonResponse({'error': 'Missing day or period'}, status=400)

#     school = request.user.school
#     busy_teachers = Routine.objects.filter(
#         day=day,
#         period_number=period,
#         school=school
#     ).values_list('teacher_id', flat=True)

#     return JsonResponse({'busy_teacher_ids': list(busy_teachers)})


@login_required
def get_busy_teachers(request):
    day = request.GET.get('day')
    period = request.GET.get('period')
    grade = request.GET.get('grade')
    section = request.GET.get('section')

    if not day or not period:
        return JsonResponse({'error': 'Missing day or period'}, status=400)

    filters = {
        'day': day,
        'period_number': period,
        'school': request.user.school
    }

    qs = Routine.objects.filter(**filters)

    # 🟢 Exclude the current cell's teacher assignment
    if grade and section:
        qs = qs.exclude(grade_id=grade, section_id=section)

    busy_teachers = qs.values_list('teacher_id', flat=True)

    return JsonResponse({'busy_teacher_ids': list(busy_teachers)})



from django.utils import timezone
def teacher_routine_view(request):
    if request.user.is_teacher:
        teacher_profile = get_object_or_404(TeacherProfile, user=request.user)

        # Get today's weekday name (e.g., "Monday")
        today = datetime.today().strftime('%A')

        routines = Routine.objects.filter(
            teacher=teacher_profile,
            day=today
        ).order_by('period_number')

        return render(request, 'dashboard/teachers/teacher_routine.html', {
            'routines': routines,
            'today': today,
        })
    else:
        return render(request, 'not_authorized.html')



# @csrf_exempt
# def assign_class_teacher(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             grade_id = data.get("grade")
#             section_id = data.get("section")
#             teacher_id = data.get("teacher_id")

#             # Clear previous class teacher for this section
#             TeacherProfile.objects.filter(section_id=section_id).update(grade=None, section=None)

#             # Assign new class teacher
#             teacher = TeacherProfile.objects.get(id=teacher_id)
#             teacher.grade_id = grade_id
#             teacher.section_id = section_id
#             teacher.save()

#             return JsonResponse({'success': True})
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})


# @csrf_exempt
# def assign_class_teacher(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             grade_id = data.get("grade")
#             section_id = data.get("section")
#             teacher_id = data.get("teacher_id")

#             # Clear previous class teacher for this section
#             TeacherProfile.objects.filter(section_id=section_id).update(grade=None, section=None)

#             # Assign new class teacher
#             teacher = TeacherProfile.objects.get(id=teacher_id)
#             teacher.grade_id = grade_id
#             teacher.section_id = section_id
#             teacher.save()

#             # Update or create Sunday Period 1 to assign class teacher
#             days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
#             for day in days:
#                 Routine.objects.update_or_create(
#                     grade_id=grade_id,
#                     section_id=section_id,
#                     day=day,
#                     period_number=1,
#                     defaults={
#                         'teacher': teacher
#                     }
#                 )

#             return JsonResponse({'success': True})

#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})


# def get_class_teacher(request):
#     grade_id = request.GET.get("grade")
#     section_id = request.GET.get("section")

#     all_teachers = TeacherProfile.objects.select_related('user')
#     current_teacher = all_teachers.filter(grade_id=grade_id, section_id=section_id).first()

#     response = {
#         "current_teacher_id": current_teacher.id if current_teacher else None,
#         "teacher_list": []
#     }

#     for t in all_teachers:
#         response["teacher_list"].append({
#             "id": t.id,
#             "name": t.user.get_full_name(),
#             "assigned": bool(t.grade_id and t.section_id and (t.grade_id != int(grade_id) or t.section_id != int(section_id)))
#         })

#     return JsonResponse(response)


import csv
from io import TextIOWrapper

@csrf_exempt
def import_students_csv(request):
    school = request.user.school
    if request.method == 'POST' and request.FILES.get('csv_file'):
        try:
            grade_id = request.POST.get('grade_id')
            section_id = request.POST.get('section_id')

            grade = Grade.objects.get(id=grade_id)
            section = Section.objects.get(id=section_id)

            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            reader = csv.DictReader(csv_file)

            skipped = []

            for row in reader:
                name = row['name'].strip()
                roll_number = row['roll_number'].strip()

                # Check for duplicate roll number in same grade & section
                if Student.objects.filter(
                    grade=grade, section=section, roll_number=roll_number
                ).exists():
                    skipped.append(f"{name} (Roll {roll_number})")
                    continue

                Student.objects.create(
                    name=name,
                    roll_number=roll_number,
                    grade=grade,
                    section=section,
                    school=school,
                )

            message = "✅ Students imported successfully."
            if skipped:
                message += f" ⚠️ Skipped {len(skipped)} duplicate(s): " + ", ".join(skipped[:5])
                if len(skipped) > 5:
                    message += "..."

            return JsonResponse({'success': True, 'message': message})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})



def code(request):
    return render(request,'code.html')