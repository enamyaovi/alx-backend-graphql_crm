import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from crm.models import Customer, Product, Order
from decimal import Decimal

NUM_CUSTOMERS = 20
NUM_PRODUCTS = 10
NUM_ORDERS = 15

class Command(BaseCommand):
    help = "Seed the database with dummy data for Customers, Products, and Orders"

    def handle(self, *args, **options):
        fake = Faker()
        self.stdout.write("Seeding database...")

        customers = self.create_customers(fake)
        self.stdout.write(f"Created {len(customers)} customers")

        products = self.create_products(fake)
        self.stdout.write(f"Created {len(products)} products")

        orders = self.create_orders(fake, customers, products)
        self.stdout.write(f"Created {len(orders)} orders")

        self.stdout.write(self.style.SUCCESS("Database seeding complete!"))

    def create_customers(self, fake):
        customers = []
        for _ in range(NUM_CUSTOMERS):
            while True:
                email = fake.unique.email()
                phone = fake.phone_number()
                if not Customer.objects.filter(email=email).exists():
                    break
            customer = Customer.objects.create(
                name=fake.name(),
                email=email,
                phone=phone
            )
            customers.append(customer)
        return customers

    def create_products(self, fake):
        products = []
        for _ in range(NUM_PRODUCTS):
            product = Product.objects.create(
                name=fake.word().capitalize(),
                price=round(random.uniform(5, 500), 2),
                stock=random.randint(0, 100)
            )
            products.append(product)
        return products

    def create_orders(self, fake, customers, products):
        orders = []
        for _ in range(NUM_ORDERS):
            customer = random.choice(customers)
            selected_products = random.sample(products, k=random.randint(1, min(5, len(products))))
            order_date = fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
            total_amount = sum(p.price for p in selected_products)

            order = Order.objects.create(
                customer=customer,
                order_date=order_date,
                total_amount=total_amount
            )
            order.products.set(selected_products)
            orders.append(order)
        return orders
