from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('cart/', views.cart_view, name='cart'),
    path('drones/', views.drone_list, name='drone_list'),
    path('contact/', views.contact, name='contact'),

    # API endpoints
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/products/', views.products_api, name='products_api'),

    # Autentifikatsiya
    path('royxatdan-otish/', views.register, name='register'),
    path('kirish/', views.user_login, name='login'),
    path('chiqish/', views.user_logout, name='logout'),
    path('profil/', views.profile, name='profile'),

    # Savat va buyurtmalar
    path('savatga-qoshish/<int:drone_id>/', views.add_to_cart, name='add_to_cart'),
    path('savat/', views.cart_view, name='cart_view'),
    path('savat-yangilash/', views.update_cart, name='update_cart'),
    path('buyurtma-berish/', views.checkout, name='checkout'),
    path('buyurtma-muvaffaqiyatli/<int:order_id>/', views.order_success, name='order_success'),
    path('buyurtmalar-tarixi/', views.order_history, name='order_history'),

    # Sharhlar
    path('sharh-qoshish/<int:drone_id>/', views.add_review, name='add_review'),

    # AJAX
    path('savat-soni/', views.get_cart_count, name='get_cart_count'),
]