from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, ClassGroup, Course, CourseResource

class StudentForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class TeacherForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = ['name', 'description']

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-2 block w-full px-4 py-2 rounded-lg border-2 border-gray-300 bg-gray-50 text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
                'placeholder': 'Enter course name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-2 block w-full px-4 py-2 rounded-lg border-2 border-gray-300 bg-gray-50 text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
                'placeholder': 'Enter course description',
                'rows': 4,
            }),
        }

class CourseResourceForm(forms.ModelForm):
    delete_file = forms.BooleanField(required=False, label="Remove existing file")
    delete_url = forms.BooleanField(required=False, label="Remove existing URL")

    class Meta:
        model = CourseResource
        fields = ['title', 'resource_type', 'file', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-2 block w-full px-4 py-2 rounded-lg border-2 border-gray-300 bg-gray-50 text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
                'placeholder': 'Enter resource title',
            }),
            'resource_type': forms.Select(attrs={
                'class': 'mt-2 block w-full px-4 py-2 rounded-lg border-2 border-gray-300 bg-gray-50 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            }),
            'file': forms.FileInput(attrs={
                'class': 'mt-2 block w-full text-gray-600',
                'accept': '.pdf',
            }),
            'url': forms.URLInput(attrs={
                'class': 'mt-2 block w-full px-4 py-2 rounded-lg border-2 border-gray-300 bg-gray-50 text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
                'placeholder': 'Enter URL (e.g., https://youtube.com...)',
            }),
        }
