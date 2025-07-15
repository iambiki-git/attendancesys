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

from django.http import HttpResponseForbidden
@login_required(login_url='/')
def school_dashboard(request):
    if not request.user.is_staff and not request.user.is_school_admin:
        return HttpResponseForbidden("You are not authorized to access this page.")
    
    school = request.user.school
    students = Student.objects.filter(school=school)
    teachers = TeacherProfile.objects.filter(school=school)
    grades = Grade.objects.filter(school=school)
    today = datetime.today()

    total_students = students.count()
    total_teachers = teachers.count()
    total_grades = grades.count
    today_attendance = Attendance.objects.filter(student__school=school, date=today)

    # present_count = today_attendance.filter(status='Present').count()
    # absent_count = today_attendance.filter(status='Absent').count()

    context = {
        'school': school,
        'total_students': total_students,
        'total_teachers': total_teachers,
        # 'present_count': present_count,
        # 'absent_count': absent_count,
        'total_grades': total_grades,
        'today': today,

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
                subjects=subjects
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
            # Update user fields
            user = teacher.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.save()
            
            # Update teacher profile
            teacher.subjects = request.POST.get('subject', teacher.subjects)
            
            # Update grade and section with school scope
            grade_id = request.POST.get('grade_level')
            if grade_id:
                teacher.grade = get_object_or_404(Grade, id=grade_id, school=request.user.school)
            else:
                teacher.grade = None
                
            section_id = request.POST.get('section')
            if section_id:
                teacher.section = get_object_or_404(Section, id=section_id, school=request.user.school)
            else:
                teacher.section = None
                
            teacher.save()
            
            return JsonResponse({
                'success': True,
                'teacher': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'subject': teacher.subjects,
                    'grade': teacher.grade.grade_number if teacher.grade else None,
                    'section': teacher.section.name if teacher.section else None,
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


from django.utils import timezone
import nepali_datetime
def teacher_dashboard(request):
    teacher = request.user.teacherprofile
    grade = teacher.grade
    section = teacher.section
    today_ad = timezone.now().date()
    today_bs = nepali_datetime.date.from_datetime_date(today_ad)
    first_day_of_month = today_ad.replace(day=1)


    nepali_weekday = today_bs.strftime("%A")
    nepali_date_str = today_bs.strftime("%B %d, %Y")

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
    }
    return render(request, 'dashboard/teachers/teacher_dashboard.html', context)



from datetime import date
def attendance(request):
    teacher = request.user.teacherprofile
    grade = teacher.grade
    section = teacher.section
    today = timezone.now().date()

    students = Student.objects.filter(
        grade = grade,
        section = section,
        school = teacher.school
    ).order_by('roll_number')

    # Check if any attendance exists for today
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


from django.views.decorators.http import require_POST
from datetime import datetime
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
            attendance_date = datetime.now().strftime('%Y-%m-%d')

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

                # Use PATCH for existing records, POST for new ones
                method = 'PATCH' if is_existing_record(student_id, attendance_date) else 'POST'
                endpoint = f"{API_URL}{student_id}/{attendance_date}/" if method == 'PATCH' else API_URL

                response = requests.request(
                    method,
                    endpoint,
                    headers=HEADERS,
                    json=payload,
                    timeout=5
                )

                if response.status_code not in [200, 201]:
                    error_data = response.json()
                    messages.error(request, f"Error for student {student_id}: {error_data}")
                    return redirect('attendance')

        messages.success(request, "Attendance saved successfully!")
        return redirect('attendance')

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Connection failed: {str(e)}")
        return redirect('attendance')

def is_existing_record(student_id, date):
    """Check if record exists (you might need to call your API for this)"""
    # This is a placeholder - implement based on your API
    # Example implementation might call GET /attendance/{student_id}/{date}/
    return False  # Default to False if you can't check


def student_status(request):
    teacher_profile = request.user.teacherprofile
    
    # Get students in teacher's grade/section
    students = Student.objects.filter(
        grade=teacher_profile.grade,
        section=teacher_profile.section,
        school=teacher_profile.school
    ).order_by('roll_number')  # Ordered by roll number
    
    # Get today's date
    today = timezone.now().date()
    
    # Get attendance data for today
    attendance_today = Attendance.objects.filter(
        student__in=students,
        date=today
    ).select_related('student')
    
    # Create a dictionary of attendance statuses
    attendance_status = {att.student_id: att.status for att in attendance_today}
    
    # Count attendance types
    present_count = sum(1 for status in attendance_status.values() if status == 'Present')
    late_count = sum(1 for status in attendance_status.values() if status == 'Late')
    absent_count = sum(1 for status in attendance_status.values() if status == 'Absent')
    
    context = {
        'teacher_profile': teacher_profile,
        'students': students,
        'attendance_status': attendance_status,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'current_date': today
    }

    return render(request, 'dashboard/teachers/student_status.html', context)


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

# def subjects(request):
#     subjects = Subjects.objects.filter(school=request.user.school)

#     context = {
#         'subjects': subjects,
#     }
#     return render(request, 'dashboard/school_dashboard/subjects.html', context)


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


def overall_attendance(request):
    return render(request, 'dashboard/school_dashboard/overall_attendance.html')


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

    context = {
        'grades': grades,
        'sections_by_grade': sections_by_grade,
        'subjects': subjects,
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

@csrf_exempt
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
                    for period_str, entry in periods.items():
                        period_number = int(period_str)
                        subject_id = entry.get('subject_id')
                        teacher_id = entry.get('teacher_id')

                        if not subject_id or not teacher_id:
                            continue

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

                        # ✅ Set Class Teacher if Sunday Period 1
                        if day == "Sunday" and period_number == 1 and not class_teacher_set:
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

    routines = Routine.objects.filter(grade_id=grade_id, section_id=section_id)

    routine_data = {}
    for entry in routines:
        key = f"{entry.grade.id}-{entry.section.id}"
        day = entry.day
        period = entry.period_number

        if key not in routine_data:
            routine_data[key] = {}
        if day not in routine_data[key]:
            routine_data[key][day] = {}

        routine_data[key][day][period] = {
            "subject_id": entry.subject.id,
            "subject": entry.subject.name,
            "teacher_id": entry.teacher.id,
            "teacher": entry.teacher.user.get_full_name(),
        }

    return JsonResponse({'routine': routine_data})




@login_required
def get_busy_teachers(request):
    day = request.GET.get('day')
    period = request.GET.get('period')

    if not day or not period:
        return JsonResponse({'error': 'Missing day or period'}, status=400)

    school = request.user.school
    busy_teachers = Routine.objects.filter(
        day=day,
        period_number=period,
        school=school
    ).values_list('teacher_id', flat=True)

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


def get_class_teacher(request):
    grade_id = request.GET.get("grade")
    section_id = request.GET.get("section")
    print(grade_id)
    print(section_id)

    try:
        teacher = TeacherProfile.objects.get(grade_id=grade_id, section_id=section_id)
        return JsonResponse({'teacher_name': teacher.user.get_full_name()})
    except TeacherProfile.DoesNotExist:
        return JsonResponse({})
