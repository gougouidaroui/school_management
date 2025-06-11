# school_management/admin.py
from django.contrib import admin
from .models import UserProfile, ClassGroup, Course, CourseResource, Schedule, Grade, Absence, ReportCard

# Register each model
admin.site.register(UserProfile)
admin.site.register(ClassGroup)
admin.site.register(Course)
admin.site.register(CourseResource)
admin.site.register(Schedule)
admin.site.register(Grade)
admin.site.register(Absence)
admin.site.register(ReportCard)
