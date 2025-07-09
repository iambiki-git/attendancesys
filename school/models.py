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


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10)  # 'Present' or 'Absent'

    class Meta:
        unique_together = ('student', 'date')
