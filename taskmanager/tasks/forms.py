from django import forms
from .models import *

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['task_name', 'description', 'assigned_to', 'email', 'priority', 'status', 'due_date', 'comment','file']
        widgets = {
            'due_date': forms.DateInput(attrs ={'type': 'date'}),
        }

class TaskEditForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['task_name', 'description', 'status', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs ={'type': 'date'}),
        }

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'contact_no', 'profile_pic']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'contact_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your contact number'
            }),
            'profile_pic': forms.FileInput(attrs={
                'class': 'form-control',
            }),
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