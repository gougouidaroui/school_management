from django.urls import path
from . import views

urlpatterns = [
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/absences/', views.student_absences, name='student_absences'),
    path('student/report_card/<int:report_card_id>/', views.download_report_card, name='download_report_card'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/grades/<int:course_id>/', views.manage_grades, name='manage_grades'),
    path('teacher/absences/<int:course_id>/', views.manage_absences, name='manage_absences'),
    path('teacher/upload_resource/<int:course_id>/', views.upload_resource, name='upload_resource'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/schedules/', views.manage_schedules, name='manage_schedules'),
    path('admin/students/', views.manage_students, name='manage_students'),
    path('admin/students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('admin/teacher_roles/', views.manage_teacher_roles, name='manage_teacher_roles'),
    path('admin/teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('admin/classes/', views.manage_classes, name='manage_classes'),
    path('admin/classes/edit/<int:class_id>/', views.edit_class, name='edit_class'),
    path('admin/report_card/<int:student_id>/', views.generate_report_card, name='generate_report_card'),
]
