# Generated by Django 5.2.4 on 2025-07-23 07:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0007_alter_student_unique_together'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='student',
            unique_together={('school', 'roll_number')},
        ),
    ]
