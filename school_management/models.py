from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    class_groups = models.ManyToManyField('ClassGroup', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class ClassGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    resources = models.FileField(upload_to='course_resources/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.class_group.name})"

class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course.name} - {self.day_of_week} {self.start_time}-{self.end_time}"

class Grade(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': False, 'is_superuser': False})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    description = models.CharField(max_length=100, blank=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.course.name}: {self.score}"

class Absence(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': False, 'is_superuser': False})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.course.name} on {self.date}"

class ReportCard(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': False, 'is_superuser': False})
    semester = models.CharField(max_length=50)
    average = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.semester}"
