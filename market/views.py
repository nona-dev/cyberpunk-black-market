from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q
from .models import Item, Category, Order, OrderItem, UserProfile, Cart, CartItem
from .forms import CustomUserCreationForm, OrderForm

def home(request):
    # Показываем все товары на главной, фильтрация будет в item_list
    featured_items = Item.objects.filter(is_available=True)[:6]
    categories = Category.objects.filter(parent=None)  # Только родительские категории
    
    context = {
        'featured_items': featured_items,
        'categories': categories,
    }
    return render(request, 'market/home.html', context)

def item_list(request):
    items = Item.objects.filter(is_available=True)
    
    # Получаем все категории для фильтра
    all_categories = Category.objects.all()
    
    # Фильтрация по TIER (показываем только товары, доступные для текущего TIER пользователя)
    if request.user.is_authenticated:
        user_profile = getattr(request.user, 'userprofile', None)
        if user_profile:
            items = items.filter(required_tier__lte=user_profile.tier)
    else:
        # Для неавторизованных пользователей показываем только TIER 1 товары
        items = items.filter(required_tier=1)
    
    # Фильтрация по категории (включая подкатегории)
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            # Если это родительская категория, показываем все дочерние
            if category.is_parent():
                child_categories = category.get_all_children()
                child_ids = [cat.id for cat in child_categories] + [category.id]
                items = items.filter(category__in=child_ids)
            else:
                items = items.filter(category=category)
        except Category.DoesNotExist:
            pass
    
    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'items': items,
        'all_categories': all_categories,
        'search_query': search_query,
        'selected_category': category_id,
    }
    return render(request, 'market/item_list.html', context)

def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    # Проверка доступа по TIER
    user_can_view = True
    user_can_buy = True
    required_tier = None
    
    if item.required_tier > 1:  # Если товар требует TIER выше 1
        if not request.user.is_authenticated:
            user_can_view = (item.required_tier == 1)
            user_can_buy = False
            required_tier = item.get_required_tier_display()
        else:
            user_profile = getattr(request.user, 'userprofile', None)
            if user_profile:
                if user_profile.tier < item.required_tier:
                    user_can_buy = False
                    required_tier = item.get_required_tier_display()
            else:
                user_can_view = (item.required_tier == 1)
                user_can_buy = False
                required_tier = item.get_required_tier_display()
    
    context = {
        'item': item,
        'user_can_buy': user_can_buy,
        'required_tier': required_tier,
    }
    return render(request, 'market/item_detail.html', context)

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'market/cart_detail.html', context)

@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    
    # Проверка доступа по TIER
    user_profile = getattr(request.user, 'userprofile', None)
    if user_profile and user_profile.tier < item.required_tier:
        messages.error(request, f'Этот товар доступен только с {item.get_required_tier_display()}. Ваш текущий TIER: {user_profile.get_tier_display()}')
        return redirect('item_list')
    
    # Получаем или создаем корзину
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Проверяем, есть ли уже такой товар в корзине
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        item=item,
        defaults={'quantity': 1, 'price': item.price}
    )
    
    # Если товар уже есть, увеличиваем количество
    if not created:
        # Проверяем, можно ли добавить еще один товар (учитывая текущее количество)
        if cart_item.quantity + 1 <= item.stock:
            cart_item.quantity += 1
            cart_item.price = item.price  # Обновляем цену на случай изменения
            cart_item.save()
            messages.success(request, f'Количество {item.name} увеличено в корзине!')
        else:
            messages.warning(request, f'Недостаточно товара {item.name} в наличии. Доступно: {item.stock}')
    else:
        messages.success(request, f'{item.name} добавлен в корзину!')
    
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(Item, id=item_id)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, item=item)
        cart_item.delete()
        messages.success(request, f'{item.name} удален из корзины.')
    except CartItem.DoesNotExist:
        messages.error(request, 'Товар не найден в корзине.')
    
    return redirect('cart_detail')

@login_required
def update_cart(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                item_id = key.split('_')[1]
                try:
                    quantity = int(value)
                    if quantity > 0:
                        # Проверяем наличие товара
                        item = get_object_or_404(Item, id=item_id)
                        if quantity <= item.stock:
                            cart_item, created = CartItem.objects.get_or_create(
                                cart=cart,
                                item_id=item_id,
                                defaults={'quantity': quantity, 'price': item.price}
                            )
                            if not created:
                                cart_item.quantity = quantity
                                cart_item.price = item.price  # Обновляем цену
                                cart_item.save()
                        else:
                            messages.warning(request, f'Недостаточно товара {item.name} в наличии. Доступно: {item.stock}')
                    elif quantity == 0:
                        CartItem.objects.filter(cart=cart, item_id=item_id).delete()
                except (ValueError, CartItem.DoesNotExist):
                    continue
        
        messages.success(request, 'Корзина обновлена.')
    
    return redirect('cart_detail')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.items.count() == 0:
        messages.warning(request, 'Ваша корзина пуста.')
        return redirect('cart_detail')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Создаем заказ
            order = form.save(commit=False)
            order.buyer = request.user
            order.total_price = cart.get_total_price()
            order.save()
            
            # Переносим товары из корзины в заказ
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    item=cart_item.item,
                    quantity=cart_item.quantity,
                    price=cart_item.price  # Используем цену из корзины
                )
            
            # Очищаем корзину
            cart.items.all().delete()
            
            messages.success(request, 'Заказ оформлен! Ожидайте подтверждения.')
            return redirect('order_history')
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'market/checkout.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(buyer=request.user)
    context = {
        'orders': orders,
    }
    return render(request, 'market/order_history.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем профиль пользователя
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать в Черный Рынок.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'market/register.html', context)

def about(request):
    return render(request, 'market/about.html')