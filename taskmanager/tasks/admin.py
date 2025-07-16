from django.contrib import admin
from .models import *


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display =('task_name', 'description', 'assigned_to','email', 'priority', 'status','due_date', 'created_date')
    list_filter =('status', 'priority', 'due_date')
    search_fields = ('task_name', 'assigned_to')

    # This is the new line that adds pagination
    list_per_page = 10
    
admin.site.register(CustomUser)
admin.site.register(EmployeeProfile)

    
