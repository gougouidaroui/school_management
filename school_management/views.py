from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import UserProfile, Course, Schedule, Grade, Absence, ReportCard, ClassGroup, CourseResource
from .forms import StudentForm, TeacherForm, ClassGroupForm, CourseResourceForm, UserProfileForm, CourseForm, CourseResourceForm
from django.contrib import messages
from django.contrib.auth.models import User
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from io import BytesIO

def user_role_required(is_superuser=False, is_staff=False, is_student=False):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if is_superuser and not request.user.is_superuser:
                messages.error(request, "Access denied. Admin privileges required.")
                return redirect('login')
            elif is_staff and not request.user.is_staff:
                messages.error(request, "Access denied. Teacher privileges required.")
                return redirect('login')
            elif is_student and (request.user.is_staff or request.user.is_superuser):
                messages.error(request, "Access denied. Student account required.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

@user_role_required(is_student=True)
def student_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    courses = Course.objects.filter(class_group__in=profile.class_groups.all())
    report_cards = ReportCard.objects.filter(student=request.user).order_by('-created_at')
    context = {'profile': profile, 'courses': courses, 'report_cards': report_cards}
    return render(request, 'school_management/student_dashboard.html', context)

@user_role_required(is_student=True)
def student_schedule(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    courses = Course.objects.filter(class_group__in=profile.class_groups.all())
    schedules = Schedule.objects.filter(course__in=courses)
    context = {'schedules': schedules}
    return render(request, 'school_management/student_schedule.html', context)

@user_role_required(is_student=True)
def student_grades(request):
    grades = Grade.objects.filter(student=request.user)
    context = {'grades': grades}
    return render(request, 'school_management/student_grades.html', context)

@user_role_required(is_student=True)
def student_absences(request):
    absences = Absence.objects.filter(student=request.user)
    context = {'absences': absences}
    return render(request, 'school_management/student_absences.html', context)

@user_role_required(is_student=True)
def download_report_card(request, report_card_id):
    report_card = get_object_or_404(ReportCard, id=report_card_id, student=request.user)
    grades = Grade.objects.filter(student=request.user, date__lte=report_card.created_at)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=90, bottomMargin=72)
    styles = getSampleStyleSheet()

    # Define modern and tasteful styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#021859'),  # Dark blue from your palette
        spaceAfter=20,
        alignment=1  # Center alignment
    )
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.HexColor('#0D0D0D'),  # Near black
        spaceAfter=10
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.whitesmoke
    )

    elements = []

    # Header with modern layout
    elements.append(Paragraph(f"Report Card - {request.user.get_full_name()}", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Semester: {report_card.semester}", normal_style))
    elements.append(Paragraph(f"Average: {report_card.average:.2f}", normal_style))
    if report_card.remarks:
        elements.append(Paragraph(f"Remarks: {report_card.remarks}", normal_style))
    elements.append(Spacer(1, 20))

    # Grade table with modern design
    data = [['Course', 'Score', 'Date']]
    for grade in grades:
        data.append([grade.course.name, str(grade.score), grade.date.strftime('%B %d, %Y')])

    table = Table(data, colWidths=[200, 100, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#021859')),  # Dark blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F2E3D5')),  # Light beige for rows
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#A66C4B')),  # Rusty brown grid
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#A66C4B')),  # Border around table
    ]))
    elements.append(table)

    # Footer with date and generated by
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Generated on: {report_card.created_at.strftime('%B %d, %Y %I:%M %p')}", normal_style))
    elements.append(Paragraph("School Management System", normal_style))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_card_{report_card.id}.pdf"'
    response.write(buffer.read())
    buffer.close()
    return response

# Teacher Views
@user_role_required(is_staff=True)
def teacher_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    courses = Course.objects.filter(teacher=request.user)
    schedules = Schedule.objects.filter(course__in=courses)
    context = {'profile': profile, 'courses': courses, 'schedules': schedules}
    return render(request, 'school_management/teacher_dashboard.html', context)

@user_role_required(is_staff=True)
def manage_grades(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        score = request.POST.get('score')
        description = request.POST.get('description')
        try:
            student = User.objects.get(id=student_id, is_staff=False, is_superuser=False)
            Grade.objects.create(student=student, course=course, score=float(score), description=description)
            messages.success(request, "Grade added successfully.")
        except (User.DoesNotExist, ValueError):
            messages.error(request, "Invalid student or score.")
        return redirect('manage_grades', course_id=course.id)
    students = User.objects.filter(is_staff=False, is_superuser=False, userprofile__class_groups=course.class_group)
    grades = Grade.objects.filter(course=course)
    context = {'course': course, 'students': students, 'grades': grades}
    return render(request, 'school_management/manage_grades.html', context)

@user_role_required(is_staff=True)
def manage_absences(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        date = request.POST.get('date')
        reason = request.POST.get('reason')
        try:
            student = User.objects.get(id=student_id, is_staff=False, is_superuser=False)
            Absence.objects.create(student=student, course=course, date=date, reason=reason)
            messages.success(request, "Absence recorded.")
        except (User.DoesNotExist, ValueError):
            messages.error(request, "Invalid student or date.")
        return redirect('manage_absences', course_id=course.id)
    students = User.objects.filter(is_staff=False, is_superuser=False, userprofile__class_groups=course.class_group)
    absences = Absence.objects.filter(course=course)
    context = {'course': course, 'students': students, 'absences': absences}
    return render(request, 'school_management/manage_absences.html', context)

@user_role_required(is_staff=True)
def upload_resource(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        if 'resource_file' in request.FILES:
            course.resources = request.FILES['resource_file']
            course.save()
            messages.success(request, "Course PDF uploaded successfully.")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "No file provided.")
    return render(request, 'school_management/upload_resource.html', {'course': course})

@user_role_required(is_staff=True)
def upload_course_resource(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        resource_type = request.POST.get('resource_type')
        file = request.FILES.get('file')
        url = request.POST.get('url')
        if not title or not resource_type or (resource_type == 'pdf' and not file) or (resource_type in ['link', 'video'] and not url):
            messages.error(request, "Missing required fields.")
        else:
            CourseResource.objects.create(course=course, title=title, resource_type=resource_type, file=file, url=url)
            messages.success(request, "Resource added successfully.")
            return redirect('teacher_dashboard')
    return render(request, 'school_management/upload_course_resource.html', {'course': course})

@user_role_required(is_student=True)
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, class_group__in=request.user.userprofile.class_groups.all())
    resources = course.additional_resources.all()
    context = {'course': course, 'resources': resources}
    return render(request, 'school_management/course_detail.html', context)

@user_role_required(is_staff=True)
def manage_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    resources = CourseResource.objects.filter(course=course)

    if request.method == 'POST':
        if 'course_form' in request.POST:
            course_form = CourseForm(request.POST, instance=course)
            if course_form.is_valid():
                course_form.save()
                messages.success(request, "Course details updated successfully.")
            else:
                messages.error(request, "Invalid course details.")
            return redirect('manage_course', course_id=course.id)

        elif 'resource_form' in request.POST:
            resource_id = request.POST.get('resource_id')
            resource = get_object_or_404(CourseResource, id=resource_id, course=course)
            resource_form = CourseResourceForm(request.POST, request.FILES, instance=resource)
            if resource_form.is_valid():
                if resource_form.cleaned_data['delete_file'] and resource.file:
                    resource.file.delete()
                if resource_form.cleaned_data['delete_url'] and resource.url:
                    resource.url = ''
                resource_form.save()
                messages.success(request, "Resource updated successfully.")
            else:
                messages.error(request, "Invalid resource data.")
            return redirect('manage_course', course_id=course.id)

        elif 'delete_resource' in request.POST:
            resource_id = request.POST.get('resource_id')
            resource = get_object_or_404(CourseResource, id=resource_id, course=course)
            resource.delete()
            messages.success(request, "Resource deleted successfully.")
            return redirect('manage_course', course_id=course.id)

        elif 'add_resource_form' in request.POST:
            add_resource_form = CourseResourceForm(request.POST, request.FILES)
            if add_resource_form.is_valid():
                resource = add_resource_form.save(commit=False)
                resource.course = course
                resource.save()
                messages.success(request, "Resource added successfully.")
            else:
                messages.error(request, "Invalid resource data.")
            return redirect('manage_course', course_id=course.id)

        elif 'main_resource_form' in request.POST:
            if 'main_resource_file' in request.FILES:
                course.resources = request.FILES['main_resource_file']
                course.save()
                messages.success(request, "Main PDF updated successfully.")
            elif 'remove_main_resource' in request.POST:
                if course.resources:
                    course.resources.delete()
                    course.save()
                    messages.success(request, "Main PDF removed successfully.")
            else:
                messages.error(request, "No file provided for main PDF.")
            return redirect('manage_course', course_id=course.id)

    course_form = CourseForm(instance=course)
    add_resource_form = CourseResourceForm()
    resource_forms = [(resource, CourseResourceForm(instance=resource)) for resource in resources]
    context = {
        'course': course,
        'course_form': course_form,
        'add_resource_form': add_resource_form,
        'resource_forms': resource_forms,
    }
    return render(request, 'school_management/manage_course.html', context)

# Admin Views
@user_role_required(is_superuser=True)
def admin_dashboard(request):
    students = User.objects.filter(is_staff=False, is_superuser=False)
    teachers = User.objects.filter(is_staff=True)
    class_groups = ClassGroup.objects.all()
    context = {'students': students, 'teachers': teachers, 'class_groups': class_groups}
    return render(request, 'school_management/admin_dashboard.html', context)

@user_role_required(is_superuser=True)
def manage_schedules(request):
    current_time = timezone.now()  # Current date and time: 2025-06-11 16:52:00+01:00
    # Remove schedules that have passed
    Schedule.objects.filter(end_time__lt=current_time).delete()

    schedules = Schedule.objects.all()  # Fetch remaining schedules
    courses = Course.objects.all()  # For the form, assuming courses are selectable

    if request.method == "POST":
        # Handle form submission (existing logic)
        course_id = request.POST.get('course_id')
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        if course_id and day and start_time and end_time:
            Schedule.objects.create(
                course_id=course_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time
            )
        return redirect('manage_schedules')

    context = {
        'schedules': schedules,
        'courses': courses,
    }
    return render(request, 'school_management/manage_schedules.html', context)

@user_role_required(is_superuser=True)
def manage_students(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, "Student created successfully.")
            return redirect('manage_students')
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = StudentForm()
    students = User.objects.filter(is_staff=False, is_superuser=False)
    context = {'form': form, 'students': students}
    return render(request, 'school_management/manage_students.html', context)

@user_role_required(is_superuser=True)
def edit_student(request, student_id):
    student = get_object_or_404(User, id=student_id, is_staff=False, is_superuser=False)
    profile = get_object_or_404(UserProfile, user=student)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, "Student updated successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = StudentForm(instance=student)
        profile_form = UserProfileForm(instance=profile)
    return render(request, 'school_management/edit_student.html', {'form': form, 'profile_form': profile_form, 'student': student})

@user_role_required(is_superuser=True)
def manage_teacher_roles(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = 'promote' if 'promote' in request.POST else 'demote'
        try:
            user = User.objects.get(id=user_id)
            if user.is_superuser:
                messages.error(request, "Cannot modify admin roles.")
            elif action == 'promote' and not user.is_staff:
                user.is_staff = True
                user.save()
                try:
                    UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(user=user)
                messages.success(request, f"{user.get_full_name()} promoted to teacher.")
            elif action == 'demote' and user.is_staff:
                user.is_staff = False
                user.save()
                messages.success(request, f"{user.get_full_name()} removed from teacher role.")
            else:
                messages.error(request, "Invalid action or user is already in desired role.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
        return redirect('manage_teacher_roles')
    users = User.objects.all()
    context = {'users': users}
    return render(request, 'school_management/manage_teacher_roles.html', context)

@user_role_required(is_superuser=True)
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, is_staff=True)
    profile = get_object_or_404(UserProfile, user=teacher)
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request.user, "Teacher updated successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = TeacherForm(instance=teacher)
        profile_form = UserProfileForm(instance=profile)
    return render(request, 'school_management/edit_teacher.html', {'form': form, 'profile_form': profile_form, 'teacher': teacher})

@user_role_required(is_superuser=True)
def manage_classes(request):
    if request.method == 'POST':
        if 'delete_class_id' in request.POST:
            class_id = request.POST.get('delete_class_id')
            try:
                class_group = ClassGroup.objects.get(id=class_id)
                class_name = class_group.name
                class_group.delete()
                messages.success(request, f"Class group '{class_name}' deleted successfully.")
            except ClassGroup.DoesNotExist:
                messages.error(request, "Class group not found.")
            return redirect('manage_classes')
        else:
            form = ClassGroupForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Class group created successfully.")
                return redirect('manage_classes')
            else:
                messages.error(request, "Invalid form data.")
    else:
        form = ClassGroupForm()
    class_groups = ClassGroup.objects.all()
    context = {'form': form, 'class_groups': class_groups}
    return render(request, 'school_management/manage_classes.html', context)

@user_role_required(is_superuser=True)
def edit_class(request, class_id):
    class_group = get_object_or_404(ClassGroup, id=class_id)
    if request.method == 'POST':
        form = ClassGroupForm(request.POST, instance=class_group)
        if form.is_valid():
            form.save()
            # Clear existing student assignments
            class_group.userprofile_set.clear()
            # Assign new students
            student_ids = request.POST.getlist('students')
            students = User.objects.filter(id__in=student_ids, is_staff=False, is_superuser=False)
            for student in students:
                try:
                    profile = student.userprofile
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(user=student)
                profile.class_groups.add(class_group)
            # Handle teacher assignment
            teacher_id = request.POST.get('teacher')
            if teacher_id:
                try:
                    teacher = User.objects.get(id=teacher_id, is_staff=True)
                    course, _ = Course.objects.get_or_create(class_group=class_group, defaults={'name': class_group.name, 'teacher': teacher})
                    course.teacher = teacher
                    course.name = class_group.name
                    course.save()
                except User.DoesNotExist:
                    messages.error(request, "Invalid teacher selected.")
            else:
                # Remove teacher by deleting the course if it exists
                Course.objects.filter(class_group=class_group).delete()
            messages.success(request, "Class group updated successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = ClassGroupForm(instance=class_group)
    students = User.objects.filter(is_staff=False, is_superuser=False)
    teachers = User.objects.filter(is_staff=True)
    current_teacher = Course.objects.filter(class_group=class_group).first().teacher if Course.objects.filter(class_group=class_group).exists() else None
    context = {'form': form, 'class_group': class_group, 'students': students, 'teachers': teachers, 'current_teacher': current_teacher}
    return render(request, 'school_management/edit_class.html', context)

@user_role_required(is_superuser=True)
def generate_report_card(request, student_id):
    student = get_object_or_404(User, id=student_id, is_staff=False, is_superuser=False)
    grades = Grade.objects.filter(student=student)
    absences = Absence.objects.filter(student=student)
    if not grades:
        messages.error(request, "No grades available for this student.")
        return redirect('admin_dashboard')
    average = sum(grade.score for grade in grades) / len(grades)
    remarks = request.POST.get('remarks', '') if request.method == 'POST' else ''
    semester = request.POST.get('semester', 'Default Semester') if request.method == 'POST' else 'Default Semester'
    if request.method == 'POST':
        report_card = ReportCard.objects.create(student=student, semester=semester, average=average, remarks=remarks)
        messages.success(request, f"Report card generated for {student.get_full_name()}.")
        return redirect('admin_dashboard')
    return render(request, 'school_management/generate_report_card.html', {'student': student, 'average': average})
