from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

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

class CourseResource(models.Model):
    RESOURCE_TYPES = (
        ('pdf', 'PDF'),
        ('link', 'Link'),
        ('video', 'Video'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='additional_resources')
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='course_resources/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.resource_type})"

class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10, choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday')])
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Add full datetime for comparison if needed
    full_end_datetime = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.full_end_datetime:  # Set initial datetime based on current year and week
            current_date = timezone.now().date()
            day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}
            day_offset = day_map[self.day_of_week]
            base_date = current_date - timezone.timedelta(days=current_date.weekday() - day_offset)
            self.full_end_datetime = timezone.make_aware(timezone.datetime.combine(base_date, self.end_time))
        super().save(*args, **kwargs)

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

@receiver(post_delete, sender=Course)
@receiver(post_delete, sender=CourseResource)
def delete_files_when_row_deleted_from_db(sender, instance, **kwargs):
    for field in sender._meta.concrete_fields:
        if isinstance(field, models.FileField):
            instance_file_field = getattr(instance, field.name)
            delete_file_if_unused(sender, instance, field, instance_file_field)

@receiver(pre_save, sender=Course)
@receiver(pre_save, sender=CourseResource)
def delete_files_when_file_changed(sender, instance, **kwargs):
    if not instance.pk:
        return
    for field in sender._meta.concrete_fields:
        if isinstance(field, models.FileField):
            try:
                instance_in_db = sender.objects.get(pk=instance.pk)
            except sender.DoesNotExist:
                return
            instance_in_db_file_field = getattr(instance_in_db, field.name)
            instance_file_field = getattr(instance, field.name)
            if instance_in_db_file_field.name != instance_file_field.name:
                delete_file_if_unused(sender, instance, field, instance_in_db_file_field)

def delete_file_if_unused(model, instance, field, instance_file_field):
    dynamic_field = {}
    dynamic_field[field.name] = instance_file_field.name
    other_refs_exist = model.objects.filter(**dynamic_field).exclude(pk=instance.pk).exists()
    if not other_refs_exist:
        instance_file_field.delete(False)
