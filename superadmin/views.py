from django.shortcuts import render, redirect
from school.models import School, Student, TeacherProfile
from django.contrib import messages

# Create your views here.
def superadmin_dashboard(request):
    total_schools = School.objects.all().count()
    total_students = Student.objects.all().count() 
    total_teachers = TeacherProfile.objects.all().count() 

    context = {
        'total_schools': total_schools,
        'total_students': total_students,
        'total_teachers': total_teachers,
    }
    return render(request, 'superadmin/admin_dashboard.html', context)


from django.db.models import Prefetch
def school_list(request):
    # Optimized query to get schools with their admin users
    schools = School.objects.prefetch_related(
        Prefetch(
            'customuser_set',
            queryset=CustomUser.objects.filter(is_school_admin=True),
            to_attr='admin_users'
        )
    ).all()

    context = {
        'schools': schools,
    }
    return render(request, 'superadmin/school_list.html', context)


from django.contrib.auth import get_user_model
CustomUser = get_user_model()

def add_school(request):
    if request.method == "POST":
        school_name = request.POST.get('school_name', '').strip()
        school_email = request.POST.get('school_email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Validate inputs
        if not all([school_name, school_email, username, password]):
            messages.error(request, "All fields are required")
            return redirect('school_list')
        
        # Check if school already exists
        if School.objects.filter(name__iexact=school_name).exists():
            messages.warning(request, f"A school named '{school_name}' already exists")
            return redirect('school_list')
        
        # Check if username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.warning(request, "Username already taken")
            return redirect('school_list')
            
        if CustomUser.objects.filter(email=school_email).exists():
            messages.warning(request, "Email already registered")
            return redirect('school_list')

        try:
            # Create school first
            school = School.objects.create(name=school_name)
            
            # Create user account with school relationship
            user = CustomUser.objects.create_user(
                username=username,
                email=school_email,
                password=password,
                school=school,
                is_school_admin=True  # Set as school admin by default
            )   
            
            messages.success(request, f"School '{school.name}' added successfully. Admin account created.")
            return redirect('school_list')
            
        except Exception as e:
            # Clean up if any error occurs
            if 'school' in locals():
                school.delete()
            if 'user' in locals():
                user.delete()
            messages.error(request, f"Error creating school: {str(e)}")
            return redirect('school_list')
    
    return redirect('school_list')



from django.db.models import Count
def school_wise_student(request):
    school_list = School.objects.annotate(student_count=Count('student'))


    context = {
        'school_list': school_list,
    }
    return render(request, 'superadmin/school_wise_student.html', context)