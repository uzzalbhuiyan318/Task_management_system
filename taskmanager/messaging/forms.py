from django import forms
from .models import Message
from tasks.models import CustomUser

class MessageForm(forms.ModelForm):
    # The recipient field will be populated by the view
    recipient = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(), 
        label="To",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # **THIS META CLASS WAS MISSING**
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Write your message...'}),
        }
