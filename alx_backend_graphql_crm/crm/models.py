from django.db import models

# Create your models here.

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
        verbose_name= 'Product',
        null=False,
        blank=False
    )
    price = models.DecimalField(
        null=False,
        blank=False,
        max_digits=10,
        decimal_places=3
    )
    stock = models.PositiveIntegerField(
        null=False,
        blank=False,
        default=0
    )

    def __str__(self) -> str:
        return f"{self.name} @GH{self.price}. {self.stock}"
    
    def validate_price(self):
        if not self.price and self.stock >= 0:
            raise ValueError

class Order(models.Model):
    customer_id = models.ForeignKey(
        to=Customer,
        on_delete=models.DO_NOTHING,
        related_name='orders'
    )
    product_id = models.ForeignKey(
        on_delete=models.DO_NOTHING,
        to=Product,
        related_name='product_orders'
    )
    order_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return f"{self.product_id.name} by {self.customer_id.name}"