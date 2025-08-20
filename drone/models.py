from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    name_uz = models.CharField(max_length=100, verbose_name="Kategoriya nomi (O'zbek)", default="")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, verbose_name="Tavsif")
    image = models.ImageField(upload_to='categories/', blank=True, verbose_name="Rasm")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name_uz


class Drone(models.Model):
    name = models.CharField(max_length=200, verbose_name="Dron nomi")
    name_uz = models.CharField(max_length=200, verbose_name="Dron nomi (O'zbek)", default="")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategoriya")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narx")
    description = models.TextField(verbose_name="Tavsif")
    description_uz = models.TextField(verbose_name="Tavsif (O'zbek)", default="")
    specifications = models.JSONField(default=dict, verbose_name="Texnik xususiyatlar")
    image = models.ImageField(upload_to='drone/', verbose_name="Asosiy rasm")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Ombordagi miqdor")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_featured = models.BooleanField(default=False, verbose_name="Tavsiya etilgan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dron"
        verbose_name_plural = "Dronlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.name_uz

    def get_absolute_url(self):
        return reverse('drone_detail', kwargs={'pk': self.pk})


class DroneImage(models.Model):
    drone = models.ForeignKey(Drone, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='drone_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.drone.name_uz} - Rasm"


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    address = models.TextField(verbose_name="Manzil")
    city = models.CharField(max_length=100, verbose_name="Shahar")
    postal_code = models.CharField(max_length=10, verbose_name="Pochta indeksi")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Tug'ilgan sana")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return self.drone.price * self.quantity

    class Meta:
        unique_together = ('cart', 'drone')


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Tasdiqlangan'),
        ('processing', 'Tayyorlanmoqda'),
        ('shipped', 'Yuborilgan'),
        ('delivered', 'Yetkazilgan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField(verbose_name="Yetkazib berish manzili")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"Buyurtma #{self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.price * self.quantity


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 yulduz'),
        (2, '2 yulduz'),
        (3, '3 yulduz'),
        (4, '4 yulduz'),
        (5, '5 yulduz'),
    ]

    drone = models.ForeignKey(Drone, related_name='reviews', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(verbose_name="Sharh")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        unique_together = ('drone', 'customer')

    def __str__(self):
        return f"{self.drone.name_uz} - {self.rating} yulduz"