# Generated by Django 5.2.4 on 2025-07-23 07:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0008_alter_student_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='student',
            unique_together=set(),
        ),
    ]
