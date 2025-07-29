# messaging/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from .models import Conversation, Message, AdminAlias
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def inbox(request):
    """Входящие сообщения"""
    # Получаем все диалоги пользователя
    conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).prefetch_related('messages', 'participants').order_by('-updated_at')
    
    # Отмечаем непрочитанные сообщения
    for conversation in conversations:
        unread_count = conversation.messages.filter(
            ~Q(sender=request.user) & Q(is_read=False)
        ).count()
        conversation.unread_count = unread_count
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    """Детали диалога"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Отмечаем сообщения как прочитанные
    conversation.messages.filter(
        ~Q(sender=request.user) & Q(is_read=False)
    ).update(is_read=True)
    
    # Получаем все сообщения в диалоге
    messages_list = conversation.messages.all().select_related('sender')
    
    # Получаем других участников диалога
    other_participants = conversation.participants.exclude(id=request.user.id)
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_participants': other_participants,
    }
    return render(request, 'messaging/conversation_detail.html', context)

@login_required
def send_message(request, conversation_id):
    """Отправить сообщение"""
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        content = request.POST.get('content', '').strip()
        
        if content:
            # Создаем сообщение
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # Обновляем время диалога
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # УБРАЛИ messages.success(request, 'Сообщение отправлено!')
        # else:
            # УБРАЛИ messages.error(request, 'Сообщение не может быть пустым!')
    
    return redirect('messaging:conversation_detail', conversation_id=conversation_id)

@login_required
def create_conversation(request, user_id):
    """Создать новый диалог"""
    other_user = get_object_or_404(User, id=user_id)
    
    if request.user == other_user:
        messages.error(request, 'Нельзя создать диалог с самим собой!')
        return redirect('market:home')
    
    # Проверяем, существует ли уже диалог между этими пользователями
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).filter(
        is_active=True
    ).distinct()
    
    if existing_conversation.exists():
        conversation = existing_conversation.first()
    else:
        # Создаем новый диалог
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return redirect('messaging:conversation_detail', conversation_id=conversation.id)

@login_required
def admin_conversations(request):
    """Панель администратора для просмотра всех диалогов"""
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    conversations = Conversation.objects.filter(is_active=True).prefetch_related('messages', 'participants')
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/admin_conversations.html', context)

@require_POST
@login_required
def mark_as_read_admin(request, message_id):
    """Админ отмечает конкретное сообщение как прочитанное"""
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    message = get_object_or_404(Message, id=message_id)
    message.is_read = True
    message.save()
    
    return JsonResponse({'status': 'success'})