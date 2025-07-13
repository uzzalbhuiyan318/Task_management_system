from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model =Task
        fields = ['task_name', 'description','assigned_to','email','priority','status','due_date']
        widgets = {
            'due_date': forms.DateInput(attrs ={'type': 'date'}),
        }