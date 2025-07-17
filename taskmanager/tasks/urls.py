
from django.urls import path
from . import views
from .views import *
app_name = 'tasks'

urlpatterns = [
    path('', home, name='home'),
    path('task_list/', task_list, name='task_list'),
    path('data/', views.jqgrid_tasks, name='task_jqgrid'),
    path('create/', task_create, name='task_create'),
    path('<int:pk>/', task_detail, name='task_detail'),
    path('<int:pk>/update/', task_update, name='task_update'),
    path('<int:pk>/delete/', task_delete, name='task_delete'),
    path('registration/', registration, name='registration'),
    path('loginPage/', loginPage, name='loginPage'),
    path('logoutPage/', logoutPage, name='logoutPage'),
    path('AdminProfilePage/', AdminProfilePage, name='AdminProfilePage'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('login_required/', login_required, name='login_required'),
    path('AdminDashboard/', AdminDashboard, name='AdminDashboard'),
]
