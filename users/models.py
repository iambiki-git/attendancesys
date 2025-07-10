from django.contrib.auth.models import AbstractUser
from django.db import models

class School(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    is_school_admin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    # def save(self, *args, **kwargs):
    #     # Ensure mutual exclusivity
    #     if self.is_school_admin:
    #         self.is_teacher = False
    #         self.is_student = False
    #     elif self.is_teacher:
    #         self.is_school_admin = False
    #         self.is_student = False
    #     super().save(*args, **kwargs)