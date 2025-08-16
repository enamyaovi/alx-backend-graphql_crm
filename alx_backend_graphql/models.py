from django.db import models
from django.core.exceptions import ValidationError


class Customer(models.Model):
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )
    email = models.EmailField(
        unique=True,
        null=False,
        blank=False
    )
    phone = models.CharField(
        max_length=15,
        null=False,
        blank=False,
        unique=True
    )

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Product',
        null=False,
        blank=False
    )
    price = models.DecimalField(
        null=False,
        blank=False,
        max_digits=10,
        decimal_places=2  # 2 decimal places for currency
    )
    stock = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0
    )

    def clean(self):
        if self.price is None or self.price < 0:
            raise ValidationError("Price must be set and non-negative.")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative.")

    def __str__(self) -> str:
        return f"{self.name} @GH₵{self.price} ({self.stock} in stock)"


class Order(models.Model):
    customer = models.ForeignKey(
        to=Customer,
        on_delete=models.PROTECT,  # Prevent deletion of customers with orders
        related_name='orders'
    )
    products = models.ManyToManyField(
        to=Product,
        related_name='product_orders'
    )
    order_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        product_names = ", ".join(self.products.values_list('name', flat=True))
        return f"Order {self.pk} by {self.customer.name} | Cart: [{product_names}]"
    
    def total_amount(self):
        pass
