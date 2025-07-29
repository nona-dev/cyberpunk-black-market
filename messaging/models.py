# messaging/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Conversation(models.Model):
    """Диалог между пользователями"""
    participants = models.ManyToManyField(User, related_name='conversations', verbose_name='Участники')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = ", ".join([user.username for user in self.participants.all()])
        return f"Диалог: {participant_names}"

class Message(models.Model):
    """Сообщение в диалоге"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name='Диалог')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='Отправитель')
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата отправки')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Сообщение от {self.sender.username} в {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_as_read(self):
        """Пометить сообщение как прочитанное"""
        self.is_read = True
        self.save()

class AdminAlias(models.Model):
    """Алиасы для администраторов (чтобы отвечать с разных аккаунтов)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_aliases', verbose_name='Пользователь')
    alias_name = models.CharField(max_length=100, verbose_name='Имя алиаса')
    alias_description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    class Meta:
        verbose_name = 'Админ алиас'
        verbose_name_plural = 'Админ алиасы'
    
    def __str__(self):
        return f"{self.alias_name} ({self.user.username})"