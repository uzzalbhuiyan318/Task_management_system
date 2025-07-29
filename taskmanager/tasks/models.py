from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
        GENDER =[
        ('male','Male'),
        ('female','Female'),
        ('others','Others'),
        ]
        
        USER_TYPE = [
            ('employee', 'Employee'),
            ('admin', 'Admin'),
        ]
        user_type = models.CharField(max_length=20,choices=USER_TYPE, null=True)
        username = models.CharField(max_length=30, null=True, unique=True)
        gender = models.CharField(choices=GENDER, null=True, max_length=20)
        age = models.IntegerField(null=True)
        contact_no = models.CharField(max_length=25, null=True)
        profile_pic = models.ImageField(upload_to='Media/profile_pic', null=True)
        
        
        USERNAME_FIELD = 'username'
        REQUIRED_FIELDS = []
        
        def __str__(self):
            return f"username: {self.username}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ]
    
    Status_Choice = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ]
    
    task_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='Task')
    email = models.EmailField(max_length=50, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=Status_Choice, default='Pending')
    due_date = models.DateField()
    created_date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='Media/files', null=True)
    
    def __str__(self):
        return self.task_name

class EmployeeProfile(models.Model):
    
    username = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='employee')
    address = models.CharField(max_length=255, null=True)
    job_post = models.CharField(max_length= 50, null=True)
    
    
    def __str__(self):
        return f"username: {self.username}"


class AdminProfile(models.Model):
    username = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='admin')
    role = models.CharField(max_length=100, null=True)
    permissions = models.TextField(null=True)
    
    def __str__(self):
        
        return f"Admin Profile for {self.username}"
    


    
    