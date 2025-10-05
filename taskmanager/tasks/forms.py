from django import forms
from .models import *
from django.contrib.auth import get_user_model
from datetime import date, datetime
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomDateInput(forms.DateInput):
    """Custom date input widget that handles DD-MM-YY format"""

    def format_value(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        # Convert date object to DD-MM-YY format for display
        return value.strftime('%d-%m-%y')

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        print(f"🔍 CustomDateInput received value: '{value}'")
        if value:
            try:
                # Handle different date formats
                if value.count('-') == 2:
                    parts = value.split('-')
                    print(f"🔍 CustomDateInput parts: {parts}")
                    
                    # YYYY-MM-DD format (from frontend JavaScript)
                    if len(parts[0]) == 4 and len(parts[1]) <= 2 and len(parts[2]) <= 2:
                        print(f"🔍 CustomDateInput: YYYY-MM-DD format detected: '{value}'")
                        return value  # Already in correct format
                    
                    # DD-MM-YY format (from datepicker) - Bootstrap datepicker uses DD-MM-YY
                    elif len(parts[2]) == 2:
                        day, month, year = parts
                        full_year = '20' + year
                        converted = f"{full_year}-{month.zfill(2)}-{day.zfill(2)}"
                        print(f"🔍 CustomDateInput converting DD-MM-YY:")
                        print(f"   Original: '{value}' -> Day: {day}, Month: {month}, Year: {year}")
                        print(f"   Converted: '{converted}'")
                        
                        # Validate the converted date to ensure it's valid
                        try:
                            parsed_date = datetime.strptime(converted, '%Y-%m-%d').date()
                            print(f"🔍 Validation successful: {parsed_date}")
                            return converted
                        except ValueError as parse_error:
                            print(f"❌ Invalid date after conversion: {parse_error}")
                            raise ValidationError(f"Invalid date: {value}")
                        
                print(f"🔍 CustomDateInput could not parse format: '{value}'")
            except (ValueError, IndexError) as e:
                print(f"🔍 CustomDateInput parsing error: {e}")
        return value

class TaskForm(forms.ModelForm):
    # This form is for CREATING tasks and correctly uses a dropdown
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type__in=['employee', '2']),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Make upload field optional
    upload = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
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
            # 📅 CUSTOM DATE INPUT: Custom widget for MM-DD-YY format
            'due_date': CustomDateInput(attrs={
                'type': 'text',
                'class': 'form-control datepicker-custom',
                'placeholder': 'dd-mm-yy',
                'readonly': 'readonly'  # Prevent manual typing, force calendar use
            }),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        today = date.today()
        print(f"🔍 TaskForm clean_due_date received: {due_date} (type: {type(due_date)})")
        print(f"🔍 Today's date for comparison: {today}")
        
        # If due_date is still a string, try to parse it
        if isinstance(due_date, str):
            try:
                print(f"🔍 Parsing string date: '{due_date}'")
                # Try YYYY-MM-DD format first
                if len(due_date.split('-')[0]) == 4:
                    due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                    print(f"🔍 Successfully parsed as YYYY-MM-DD: {due_date}")
                # Try DD-MM-YY format
                else:
                    due_date = datetime.strptime(due_date, '%d-%m-%y').date()
                    print(f"🔍 Successfully parsed as DD-MM-YY: {due_date}")
            except ValueError as e:
                print(f"🔍 Date parsing failed: {e}")
                raise ValidationError("Invalid date format. Please use a valid date.")

        # Enhanced date validation with detailed logging
        if due_date:
            print(f"🔍 Comparing due_date {due_date} with today {today}")
            if due_date < today:
                print(f"❌ Date validation failed: {due_date} < {today}")
                raise ValidationError(
                    "Due date cannot be in the past. Please select today's date or a future date."
                )
            else:
                print(f"✅ Date validation passed: {due_date} >= {today}")

        return due_date

class TaskEditForm(forms.ModelForm):
    # ✅ UPDATED: The 'assigned_to' field is now removed from this form
    # because it is not editable in your modal UI.
    
    # 🔧 FIXED: Make upload field optional for editing
    upload = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Task
        fields = ['task_name', 'description', 'email', 'priority', 'status', 'due_date', 'comment', 'upload']
        widgets = {
            # 📅 FIXED: Use CustomDateInput for consistent date handling
            'due_date': CustomDateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'task_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # upload field is defined above as explicit field with custom validation
        }
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        print(f"🔍 TaskEditForm clean_due_date received: {due_date} (type: {type(due_date)})")
        
        # If due_date is still a string, try to parse it
        if isinstance(due_date, str):
            try:
                print(f"🔍 TaskEditForm parsing string date: '{due_date}'")
                # Try YYYY-MM-DD format first
                if len(due_date.split('-')[0]) == 4:
                    due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                    print(f"🔍 TaskEditForm successfully parsed as YYYY-MM-DD: {due_date}")
                # Try DD-MM-YY format
                else:
                    due_date = datetime.strptime(due_date, '%d-%m-%y').date()
                    print(f"🔍 TaskEditForm successfully parsed as DD-MM-YY: {due_date}")
            except ValueError as e:
                print(f"🔍 TaskEditForm date parsing failed: {e}")
                raise ValidationError("Invalid date format. Please use a valid date.")
        
        if due_date and due_date < date.today():
            raise ValidationError("Due date cannot be in the past. Please select today's date or a future date.")
        return due_date

    def clean_upload(self):
        upload = self.cleaned_data.get('upload')
        print(f"🔍 TaskEditForm clean_upload received: {upload}")
        
        # If no file is uploaded (empty file), return None to keep existing file
        if upload and hasattr(upload, 'size') and upload.size == 0:
            print("🔍 TaskEditForm: Empty file detected, keeping existing file")
            return None
        elif upload and hasattr(upload, 'name') and not upload.name:
            print("🔍 TaskEditForm: File with empty name detected, keeping existing file") 
            return None
            
        print(f"🔍 TaskEditForm: Valid file upload: {upload}")
        return upload


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


