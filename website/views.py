from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import SignUpForm, LoginForm, UserProfileForm
from school_management.models import UserProfile
from django.contrib import messages

def home(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)  # Create UserProfile with default empty fields
            login(request, user)
            messages.info(request, "Please complete your profile to continue.")
            return redirect('profile_setup')
    form = SignUpForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            try:
                profile = user.userprofile
                # Check if profile is incomplete (e.g., missing phone or date_of_birth)
                if user.is_superuser:
                    return redirect('admin_dashboard')
                if not profile.phone or not profile.date_of_birth:
                    messages.info(request, "Please complete your profile to continue.")
                    return redirect('profile_setup')
                # Redirect based on Django user roles
                elif user.is_staff:
                    return redirect('teacher_dashboard')
                else:
                    return redirect('student_dashboard')
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
                messages.info(request, "Please complete your profile to continue.")
                return redirect('profile_setup')
    form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def profile_setup(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            # Redirect based on user role
            if request.user.is_superuser:
                return redirect('admin_dashboard')
            elif request.user.is_staff:
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    else:
        form = UserProfileForm(instance=profile)
        form.initial['date_of_birth'] = form['date_of_birth'].value().strftime('%Y-%m-%d')
        print(form['date_of_birth'].value())

    return render(request, 'profile_setup.html', {'form': form})
