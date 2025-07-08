
from django.urls import path
from .views import task_list, task_create, task_detail, task_update, task_delete

urlpatterns = [
    path('', task_list, name='task_list'),
    path('create/', task_create, name='task_create'),
    path('<int:pk>/', task_detail, name='task_detail'),
    path('<int:pk>/update/', task_update, name='task_update'),
    path('<int:pk>/delete/', task_delete, name='task_delete'),
]
