from django.db import models
from users.models import School

class Grade(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade_number = models.PositiveIntegerField(blank=True, null=True)
    name = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        unique_together = ('school', 'name', 'grade_number')

    def __str__(self):
        return f"{self.grade_number} ({self.school.name})"
    
class Section(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='sections', null=True, blank=True)
    name = models.CharField(max_length=10)
    
    class Meta:
        unique_together = ('grade', 'name',)

    def __str__(self):
        if self.grade:
            return f"{self.name} ({self.grade})"
        return f"{self.name} (No Grade)"

    
class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    roll_number = models.PositiveIntegerField()
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)  # Date of Birth
    address = models.TextField(blank=True, null=True)
    parents_contact = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        unique_together = ('school', 'grade', 'section', 'roll_number')

    def __str__(self):
        return self.name


from django.conf import settings
class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)  # Date of Birth
    address = models.TextField(blank=True, null=True)
    edu_qualification = models.CharField(max_length=100, blank=True, null=True)  # Educational Qualification
    specialization = models.CharField(max_length=100, blank=True, null=True)  # Specialization
    year_of_experience = models.PositiveIntegerField(default=0, blank=True, null=True)  # Years of Experience

    # 👉 Specific class teacher role
    grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    section = models.OneToOneField(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


    def __str__(self):
        return f"TeacherProfile: {self.user.username}"

    

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10)  # 'Present' or 'Absent'
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'date')

class Subjects(models.Model):
    name = models.CharField(max_length=50)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subjects')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)

    def __str__(self):
        return self.name
    

class Routine(models.Model):
    DAY_CHOICES = [
        ("Sunday", "Sunday"),
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    period_number = models.PositiveIntegerField()
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['day', 'period_number', 'grade', 'section', 'school']

    def __str__(self):
        return f"{self.grade} {self.section} | {self.day} P{self.period_number} - {self.subject} ({self.teacher})"




class Announcement(models.Model):
    ANNOUNCEMENT_TYPES = [
        ('general', 'General'),
        ('event', 'Event'),
        ('exam', 'Exam'),
        ('holiday', 'Holiday'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='general')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    school = models.ForeignKey(School, on_delete=models.CASCADE)


    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)  # blank=True allows unassigned teachers to skip
    description = models.TextField(blank=True)
    due_date = models.DateField()
    assignment_file = models.FileField(upload_to='assignments/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)

    # Optional grade & section fields
    grade = models.ForeignKey(Grade, null=True, blank=True, on_delete=models.SET_NULL)
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title