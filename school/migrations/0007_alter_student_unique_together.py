# Generated by Django 5.2.4 on 2025-07-23 07:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0006_student_address_student_father_name_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='student',
            unique_together=set(),
        ),
    ]
