# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('create/<int:user_id>/', views.create_conversation, name='create_conversation'),
    path('admin/', views.admin_conversations, name='admin_conversations'),
    # Новый URL для админской функции
    path('mark-as-read/<int:message_id>/', views.mark_as_read_admin, name='mark_as_read_admin'),
]