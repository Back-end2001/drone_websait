from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, Drone, DroneImage, Customer, Cart, CartItem, Order, OrderItem, Review

# Admin site customization
admin.site.site_header = "AeroKo'rish Admin Panel"
admin.site.site_title = "AeroKo'rish Admin"
admin.site.index_title = "Boshqaruv Paneli"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name_uz', 'name', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'name_uz']
    prepopulated_fields = {'slug': ('name',)}


class DroneImageInline(admin.TabularInline):
    model = DroneImage
    extra = 1


@admin.register(Drone)
class DroneAdmin(admin.ModelAdmin):
    list_display = ['get_image', 'name_uz', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured',
                    'created_at']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'name_uz', 'description']
    list_editable = ['price', 'stock_quantity', 'is_active', 'is_featured']
    inlines = [DroneImageInline]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'name_uz', 'category', 'price', 'image')
        }),
        ('Tavsif', {
            'fields': ('description', 'description_uz', 'specifications')
        }),
        ('Ombor va holat', {
            'fields': ('stock_quantity', 'is_active', 'is_featured')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                               obj.image.url)
        return "Rasm yo'q"

    get_image.short_description = 'Rasm'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_email', 'phone', 'city', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_full_name.short_description = 'To\'liq ism'

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'get_total_items', 'get_total_price', 'created_at']
    list_filter = ['created_at']
    inlines = [CartItemInline]

    def get_total_items(self, obj):
        return obj.get_total_items()

    get_total_items.short_description = 'Jami mahsulotlar'

    def get_total_price(self, obj):
        return f"${obj.get_total_price()}"

    get_total_price.short_description = 'Jami narx'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['drone', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'get_customer_name', 'status', 'total_amount', 'created_at', 'get_actions']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer__user__first_name', 'customer__user__last_name']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order_number', 'customer', 'status', 'total_amount')
        }),
        ('Yetkazib berish', {
            'fields': ('shipping_address', 'phone', 'notes')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_customer_name(self, obj):
        return f"{obj.customer.user.first_name} {obj.customer.user.last_name}"

    get_customer_name.short_description = 'Mijoz'

    def get_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'processing': 'purple',
            'shipped': 'gray',
            'delivered': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )

    get_status_badge.short_description = 'Holat'

    def get_actions(self, obj):
        return format_html(
            '<a href="{}" class="button">Ko\'rish</a>',
            reverse('admin:Drones_order_change', args=[obj.pk])
        )

    get_actions.short_description = 'Amallar'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['drone', 'customer', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['drone__name_uz', 'customer__user__first_name', 'comment']
    list_editable = ['is_approved']

    def get_customer_name(self, obj):
        return f"{obj.customer.user.first_name} {obj.customer.user.last_name}"

    get_customer_name.short_description = 'Mijoz'