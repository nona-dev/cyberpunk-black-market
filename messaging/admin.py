# messaging/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Conversation, Message, AdminAlias

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('participants__username', 'participants__email')
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()[:3]])
    get_participants.short_description = 'Участники'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'get_conversation_participants', 'short_content', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at', 'sender')
    search_fields = ('content', 'sender__username')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    
    def get_conversation_participants(self, obj):
        participants = obj.conversation.participants.all()
        return ", ".join([user.username for user in participants[:2]])
    get_conversation_participants.short_description = 'Диалог'
    
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Содержание'

@admin.register(AdminAlias)
class AdminAliasAdmin(admin.ModelAdmin):
    list_display = ('alias_name', 'user', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('alias_name', 'user__username', 'alias_description')

# Расширим админку пользователей для удобства
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')

# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)