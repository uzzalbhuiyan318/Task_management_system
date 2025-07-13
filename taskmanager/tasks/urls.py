
from django.urls import path
from . import views
from .views import *
app_name = 'tasks'

urlpatterns = [
    path('', task_list, name='task_list'),
    path('data/', views.jqgrid_tasks, name='task_jqgrid'),
    path('create/', task_create, name='task_create'),
    path('<int:pk>/', task_detail, name='task_detail'),
    path('<int:pk>/update/', task_update, name='task_update'),
    path('<int:pk>/delete/', task_delete, name='task_delete'),
]
