from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Category, Item, UserProfile, Order, OrderItem, Cart, CartItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    ordering = ('parent__name', 'name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'category', 'price', 'rarity', 'stock', 'is_available', 'required_tier')
    list_filter = ('category', 'rarity', 'item_type', 'is_available', 'required_tier', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'is_available', 'required_tier')
    
    # Добавим действие для копирования
    actions = ['duplicate_items']
    
    def duplicate_items(self, request, queryset):
        """Действие: Сделать копии выбранных товаров"""
        count = 0
        for item in queryset:
            # Создаем копию товара
            item.pk = None  # Сбрасываем первичный ключ, чтобы создать новую запись
            item.name = f"{item.name} (копия)"
            item.save()
            count += 1
        
        self.message_user(request, f"Создано {count} копий товаров.")
    
    duplicate_items.short_description = "Сделать копии выбранных товаров"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'street_karma', 'credits', 'tier')
    list_filter = ('tier',)
    search_fields = ('user__username', 'user__email')
    list_editable = ('street_karma', 'credits', 'tier')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'buyer')
    search_fields = ('buyer__username', 'id', 'delivery_address')
    readonly_fields = ('created_at',)
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} заказов помечены как подтверждённые.")
    mark_as_confirmed.short_description = "Пометить как подтверждённые"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f"{queryset.count()} заказов помечены как отправленные.")
    mark_as_shipped.short_description = "Пометить как отправленные"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, f"{queryset.count()} заказов помечены как доставленные.")
    mark_as_delivered.short_description = "Пометить как доставленные"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} заказов помечены как отменённые.")
    mark_as_cancelled.short_description = "Пометить как отменённые"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'price')
    list_filter = ('order__created_at',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'item', 'quantity', 'price')
    list_filter = ('cart__created_at',)