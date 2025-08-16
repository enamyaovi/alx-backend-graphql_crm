from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        validators=[RegexValidator(
            regex=r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$',
            message="Phone number must be in the format +1234567890 or 123-456-7890"
        )])

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.price is None or self.price <= 0:
            raise ValidationError("Price must be positive.")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative.")

    def __str__(self):
        return f"{self.name} @GH₵{self.price} ({self.stock} in stock)"


class Order(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    products = models.ManyToManyField(
        Product,
        related_name='product_orders'
    )
    order_date = models.DateTimeField(default=timezone.now)

    def total_amount(self):
        return sum(product.price for product in self.products.all())

    def __str__(self):
        product_names = ", ".join(self.products.values_list('name', flat=True))
        return f"Order {self.pk} by {self.customer.name} | Cart: [{product_names}] | Total: GH₵{self.total_amount()}"
