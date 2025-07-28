from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              verbose_name='Родительская категория', related_name='children')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name
    
    def get_full_name(self):
        """Возвращает полное имя категории с учетом иерархии"""
        if self.parent:
            return f"{self.parent.get_full_name()} → {self.name}"
        return self.name
    
    def is_parent(self):
        """Проверяет, является ли категория родительской"""
        return self.children.exists()
    
    def get_children(self):
        """Возвращает дочерние категории"""
        return self.children.all()
    
    def get_all_children(self):
        """Возвращает все дочерние категории рекурсивно"""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children

class Item(models.Model):
    RARITY_CHOICES = [
        ('common', 'Обычный'),
        ('rare', 'Редкий'),
        ('epic', 'Эпический'),
        ('legendary', 'Легендарный'),
    ]
    
    TYPE_CHOICES = [
        ('cyberware', 'Киберимплант'),
        ('weapon', 'Оружие'),
        ('armor', 'Броня'),
        ('drug', 'Наркотик'),
        ('electronics', 'Электроника'),
        ('info', 'Информация'),
        ('other', 'Другое'),
    ]
    
    MOUNT_LOCATION_CHOICES = [
        ('head', 'Голова'),
        ('eyes', 'Глаза'),
        ('arms', 'Руки'),
        ('torso', 'Торс'),
        ('legs', 'Ноги'),
        ('nervous', 'Нервная система'),
        ('internal', 'Внутренний'),
        ('external', 'Внешний'),
        ('none', 'Нет'),
    ]
    
    TIER_CHOICES = [
        (1, 'TIER 1'),
        (2, 'TIER 2'),
        (3, 'TIER 3'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена (eb)')
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common', verbose_name='Редкость')
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other', verbose_name='ТИП')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    image = models.ImageField(upload_to='items/', blank=True, null=True, verbose_name='Изображение')
    stock = models.PositiveIntegerField(default=1, verbose_name='Количество в наличии')
    is_available = models.BooleanField(default=True, verbose_name='Доступен для продажи')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    
    # Новые поля для киберпанк характеристик
    requirement = models.CharField(max_length=100, blank=True, verbose_name='ТРЕБОВАНИЕ')
    mount_location = models.CharField(max_length=20, choices=MOUNT_LOCATION_CHOICES, default='none', verbose_name='МЕСТО УСТАНОВКИ')
    humanity_loss = models.PositiveIntegerField(default=0, verbose_name='ПОТЕРЯ ЧЕЛОВЕЧНОСТИ')
    bonus_to_hit = models.IntegerField(default=0, verbose_name='БОНУС К ПОПАДАНИЮ')
    damage = models.CharField(max_length=50, blank=True, verbose_name='УРОН')
    sdp = models.PositiveIntegerField(default=0, verbose_name='СКА')  # Structural Damage Points
    ammo_capacity = models.PositiveIntegerField(default=0, verbose_name='ОБОЙМА')
    upgrade_slots = models.PositiveIntegerField(default=0, verbose_name='СЛОТЫ УЛУЧШЕНИЯ')
    
    # Система TIER вместо VIP
    required_tier = models.IntegerField(choices=TIER_CHOICES, default=1, verbose_name='Требуемый TIER')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('item_detail', kwargs={'pk': self.pk})

    def get_required_tier_display(self):
        return dict(self.TIER_CHOICES)[self.required_tier]

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
    
    def __str__(self):
        return f'Корзина {self.user.username}'
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, verbose_name='Корзина')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за единицу')  # Добавлено поле price
    
    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = ('cart', 'item')
    
    def __str__(self):
        return f'{self.quantity} x {self.item.name}'
    
    def get_total_price(self):
        return self.quantity * self.price  # Используем сохраненную цену
        
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    street_karma = models.IntegerField(default=0, verbose_name='Уличная карма')
    credits = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00, verbose_name='Кредиты')
    tier = models.IntegerField(choices=[(1, 'TIER 1'), (2, 'TIER 2'), (3, 'TIER 3')], default=1, verbose_name='TIER пользователя')
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f'{self.user.username} - TIER {self.tier} - {self.credits} eb'

    def get_tier_display(self):
        return dict([(1, 'TIER 1'), (2, 'TIER 2'), (3, 'TIER 3')])[self.tier]

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('confirmed', 'Подтверждён'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Покупатель')
    items = models.ManyToManyField(Item, through='OrderItem', verbose_name='Товары')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Общая стоимость')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    delivery_address = models.TextField(verbose_name='Адрес доставки')
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Заказ #{self.id} от {self.buyer.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f'{self.quantity} x {self.item.name}'