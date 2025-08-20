from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import uuid

from .models import Drone, Category, Customer, Cart, CartItem, Order, OrderItem, Review
from .forms import CustomUserCreationForm, LoginForm, CustomerProfileForm, ReviewForm, CheckoutForm, ContactForm


def home(request):
    """Bosh sahifa"""
    featured_drones = Drone.objects.filter(is_featured=True, is_active=True)[:4]
    categories = Category.objects.all()[:6]
    latest_drones = Drone.objects.filter(is_active=True).order_by('-created_at')[:8]

    context = {
        'featured_drones': featured_drones,
        'categories': categories,
        'latest_drones': latest_drones,
    }
    return render(request, 'drone/home.html', context)


def drone_list(request):
    """Dronlar ro'yxati"""
    drones = Drone.objects.filter(is_active=True)
    categories = Category.objects.all()

    # Filtrlash
    category_id = request.GET.get('category')
    if category_id:
        drones = drones.filter(category_id=category_id)

    # Qidiruv
    search_query = request.GET.get('search')
    if search_query:
        drones = drones.filter(
            Q(name_uz__icontains=search_query) |
            Q(description_uz__icontains=search_query)
        )

    # Narx bo'yicha filtrlash
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        drones = drones.filter(price__gte=min_price)
    if max_price:
        drones = drones.filter(price__lte=max_price)

    # Saralash
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        drones = drones.order_by('price')
    elif sort_by == 'price_high':
        drones = drones.order_by('-price')
    elif sort_by == 'newest':
        drones = drones.order_by('-created_at')
    else:
        drones = drones.order_by('name_uz')

    # Sahifalash
    paginator = Paginator(drones, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_id,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'drone/drone_list.html', context)


def drone_detail(request, pk):
    """Dron tafsilotlari"""
    drone = get_object_or_404(Drone, pk=pk, is_active=True)
    reviews = drone.reviews.filter(is_approved=True).order_by('-created_at')
    related_drones = Drone.objects.filter(
        category=drone.category,
        is_active=True
    ).exclude(pk=drone.pk)[:4]

    # O'rtacha reyting
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    # Sharh formasi
    review_form = ReviewForm()

    context = {
        'drone': drone,
        'reviews': reviews,
        'related_drones': related_drones,
        'avg_rating': avg_rating,
        'review_form': review_form,
    }
    return render(request, 'drone/drone_detail.html', context)


def register(request):
    """Ro'yxatdan o'tish"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Xush kelibsiz, {username}! Hisobingiz muvaffaqiyatli yaratildi.')
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'drone/register.html', {'form': form})


def user_login(request):
    """Kirish"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Email orqali ham kirish imkoniyati
            if '@' in username:
                try:
                    from django.contrib.auth.models import User
                    user = User.objects.get(email=username)
                    username = user.username
                except User.DoesNotExist:
                    pass

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Noto\'g\'ri foydalanuvchi nomi yoki parol.')
    else:
        form = LoginForm()

    return render(request, 'drone/login.html', {'form': form})


def user_logout(request):
    """Chiqish"""
    logout(request)
    messages.success(request, 'Siz muvaffaqiyatli chiqdingiz.')
    return redirect('home')


@login_required
def profile(request):
    """Foydalanuvchi profili"""
    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilingiz muvaffaqiyatli yangilandi.')
            return redirect('profile')
    else:
        form = CustomerProfileForm(instance=customer)

    # Foydalanuvchi buyurtmalari
    orders = Order.objects.filter(customer=customer).order_by('-created_at')[:5]

    context = {
        'form': form,
        'customer': customer,
        'orders': orders,
    }
    return render(request, 'drone/profile.html', context)


# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


# ... barcha importlar ...

@csrf_exempt
@login_required
def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))

            if quantity < 1:
                return JsonResponse({'success': False, 'error': 'Noto\'g\'ri miqdor'}, status=400)

            customer, created = Customer.objects.get_or_create(user=request.user)
            cart, created = Cart.objects.get_or_create(customer=customer)
            drone = get_object_or_404(Drone, id=product_id, is_active=True)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                drone=drone,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return JsonResponse({
                'success': True,
                'message': 'Mahsulot savatga qo\'shildi',
                'cart_total': cart.get_total_price(),
                'cart_items': cart.get_total_items()
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Noto\'g\'ri so\'rov'}, status=400)


def products_api(request):
    products = Drone.objects.all()
    products_data = []

    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name_uz,
            'description': product.description_uz,
            'price': str(product.price),
            'image': product.image.url if product.image else None,
            'is_featured': product.is_featured,
            'is_new': product.is_new,
            'discount': getattr(product, 'discount_percentage', 0)
        })

    return JsonResponse({'products': products_data})

@login_required
def cart_view(request):
    """Savat ko'rinishi"""
    customer, created = Customer.objects.get_or_create(user=request.user)
    cart, created = Cart.objects.get_or_create(customer=customer)

    context = {
        'cart': cart,
    }
    return render(request, 'drone/cart.html', context)


@login_required
@require_POST
def update_cart(request):
    """Savatni yangilash"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))

        try:
            customer = Customer.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart__customer=customer)

            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

            cart = cart_item.cart
            return JsonResponse({
                'success': True,
                'cart_total': cart.get_total_price(),
                'cart_items': cart.get_total_items()
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Mahsulot topilmadi'})

    return JsonResponse({'success': False, 'error': 'Noto\'g\'ri so\'rov'})


@login_required
def checkout(request):
    """Buyurtma berish"""
    customer, created = Customer.objects.get_or_create(user=request.user)
    cart, created = Cart.objects.get_or_create(customer=customer)

    if not cart.items.exists():
        messages.warning(request, 'Savatingiz bo\'sh!')
        return redirect('cart_view')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Buyurtma yaratish
            order = Order.objects.create(
                customer=customer,
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                total_amount=cart.get_total_price(),
                shipping_address=form.cleaned_data['shipping_address'],
                phone=form.cleaned_data['phone'],
                notes=form.cleaned_data['notes']
            )

            # Buyurtma elementlarini yaratish
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    drone=cart_item.drone,
                    quantity=cart_item.quantity,
                    price=cart_item.drone.price
                )

                # Ombor miqdorini kamaytirish
                drone = cart_item.drone
                drone.stock_quantity -= cart_item.quantity
                drone.save()

            # Savatni tozalash
            cart.items.all().delete()

            messages.success(request, f'Buyurtmangiz #{order.order_number} qabul qilindi!')
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm(initial={
            'shipping_address': customer.address,
            'phone': customer.phone
        })

    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'drone/checkout.html', context)


@login_required
def order_success(request, order_id):
    """Buyurtma muvaffaqiyatli"""
    customer = Customer.objects.get(user=request.user)
    order = get_object_or_404(Order, id=order_id, customer=customer)

    context = {
        'order': order,
    }
    return render(request, 'drone/order_success.html', context)


@login_required
def order_history(request):
    """Buyurtmalar tarixi"""
    customer = Customer.objects.get(user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'drone/order_history.html', context)


@login_required
def add_review(request, drone_id):
    """Sharh qo'shish"""
    if request.method == 'POST':
        drone = get_object_or_404(Drone, id=drone_id)
        customer, created = Customer.objects.get_or_create(user=request.user)

        # Foydalanuvchi bu dronni sotib olganmi tekshirish
        has_purchased = OrderItem.objects.filter(
            order__customer=customer,
            drone=drone,
            order__status='delivered'
        ).exists()

        if not has_purchased:
            messages.error(request, 'Siz faqat sotib olgan mahsulotlarga sharh yoza olasiz.')
            return redirect('drone_detail', pk=drone_id)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review, created = Review.objects.get_or_create(
                drone=drone,
                customer=customer,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment']
                }
            )

            if created:
                messages.success(request, 'Sharhingiz qo\'shildi va ko\'rib chiqilmoqda.')
            else:
                review.rating = form.cleaned_data['rating']
                review.comment = form.cleaned_data['comment']
                review.is_approved = False
                review.save()
                messages.success(request, 'Sharhingiz yangilandi.')

            return redirect('drone_detail', pk=drone_id)

    return redirect('drone_detail', pk=drone_id)


def contact(request):
    """Aloqa sahifasi"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Bu yerda email yuborish yoki ma'lumotni saqlash logikasini qo'shishingiz mumkin
            messages.success(request, 'Xabaringiz yuborildi! Tez orada siz bilan bog\'lanamiz.')
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
    }
    return render(request, 'drone/contact.html', context)


def about(request):
    """Biz haqimizda sahifasi"""
    return render(request, 'drone/about.html')


# AJAX views
@csrf_exempt
def get_cart_count(request):
    """Savat elementlari sonini olish"""
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            cart = Cart.objects.get(customer=customer)
            count = cart.get_total_items()
        except (Customer.DoesNotExist, Cart.DoesNotExist):
            count = 0
    else:
        count = 0

    return JsonResponse({'count': count})