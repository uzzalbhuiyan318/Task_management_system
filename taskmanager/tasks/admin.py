from django.contrib import admin
from .models import *


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display =('task_name', 'description', 'assigned_to','email', 'priority', 'status','due_date', 'created_date')
    list_filter =('status', 'priority', 'due_date')
    search_fields = ('task_name', 'assigned_to')

    # This is the new line that adds pagination
    list_per_page = 10

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('timestamp',)
    list_per_page = 20

@admin.register(WorkUpdate)
class WorkUpdateAdmin(admin.ModelAdmin):
    list_display = ('task', 'employee', 'new_status', 'review_status', 'reviewed_by', 'created_at')
    list_filter = ('review_status', 'new_status', 'created_at')
    search_fields = ('task__task_name', 'employee__username')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
admin.site.register(CustomUser)
admin.site.register(EmployeeProfile)
admin.site.register(AdminProfile)
admin.site.register(testForm)

    
