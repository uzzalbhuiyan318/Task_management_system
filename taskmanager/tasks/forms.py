from django import forms
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskForm(forms.ModelForm):
    # This form is for CREATING tasks and correctly uses a dropdown
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type__in=['employee', '2']),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Task
        fields = ['task_name', 'description', 'assigned_to', 'email', 'priority', 'status', 'due_date', 'comment', 'upload']
        widgets = {
            'task_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'upload': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TaskEditForm(forms.ModelForm):
    # ✅ UPDATED: The 'assigned_to' field is now removed from this form
    # because it is not editable in your modal UI.
    class Meta:
        model = Task
        fields = ['task_name', 'description', 'email', 'priority', 'status', 'due_date', 'comment', 'upload']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'task_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'upload': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'contact_no', 'profile_pic', 'first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control'}),
        }


class EditEmployeeForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ['address', 'job_post']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'job_post': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EditAdminForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['role', 'permissions']
        widgets = {
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'permissions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }