
from django.urls import path
from . import views
from .views import *
app_name = 'tasks'

urlpatterns = [
    path('', home, name='home'),
    path('task_list/', task_list, name='task_list'),
    path('get-employee-email/<int:employee_id>/', views.get_employee_email, name='get_employee_email'),
    path('data/', views.jqgrid_tasks, name='task_jqgrid'),
    path('create/', task_create, name='task_create'),
    path('<int:pk>/', task_detail, name='task_detail'),
    path('<int:pk>/update/', task_update, name='task_update'),
    path('<int:pk>/delete/', task_delete, name='task_delete'),
    path('<int:pk>/update_status/', views.update_task_status, name='update_task_status'),
    path('registration/', registration, name='registration'),
    path('loginPage/', loginPage, name='loginPage'),
    path('logoutPage/', logoutPage, name='logoutPage'),
    path('AdminProfilePage/', AdminProfilePage, name='AdminProfilePage'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('login_required_view/', login_required_view, name='login_required_view'),
    path('AdminDashboard/', AdminDashboard, name='AdminDashboard'),
    path('admin_base/', admin_base, name='admin_base'),
    path('employeeProfilePage/', employeeProfilePage, name='employeeProfilePage'),
    path('employeeDashboard/', employeeDashboard, name='employeeDashboard'),
    path('work-updates/', work_updates, name='work_updates'),
    path('work_update_count/',work_update_count, name='work_update_count'),
    path('task_notification_count/', views.task_notification_count, name='task_notification_count'),
    path('approve-work-update/<int:update_id>/', approve_work_update, name='approve_work_update'),
    path('reject-work-update/<int:update_id>/', reject_work_update, name='reject_work_update'),
    path('employee-work-updates/', employee_work_updates, name='employee_work_updates'),
    path('mark-work-update-seen/<int:update_id>/', views.mark_work_update_seen, name='mark_work_update_seen'),
    path('mark-task-seen/<int:task_id>/', views.mark_task_seen, name='mark_task_seen'),
    path('contactPage/', contactPage, name='contactPage'),
    path('aboutUs/', aboutUs, name='aboutUs'),
    path('contact-messages/', all_contact_messages, name='all_contact_messages'),
    path('mark-message-read/<int:message_id>/', mark_message_read, name='mark_message_read'),
    path('contact-message-count/', contact_message_count, name='contact_message_count'),
    path('formHandler/', formHandler, name='formHandler'),


]
