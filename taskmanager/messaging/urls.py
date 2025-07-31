from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('compose/', views.compose_message, name='compose'),
    path('<int:message_id>/', views.message_detail, name='message_detail'),
]
