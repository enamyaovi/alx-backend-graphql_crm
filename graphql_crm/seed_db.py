import os
import django
import random
from decimal import Decimal
from faker import Faker

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql.settings")
django.setup()

from crm.models import Customer, Product, Order
from django.db import transaction
from django.utils import timezone

fake = Faker()

NUM_CUSTOMERS = 20
NUM_PRODUCTS = 10
NUM_ORDERS = 15

def generate_safe_phone():
    """Generate a phone number matching your regex."""
    if random.choice([True, False]):
        # +1234567890 format
        return f"+{random.randint(1000000000, 9999999999)}"
    else:
        # 123-456-7890 format
        return f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

def create_customers():
    customers = []
    for _ in range(NUM_CUSTOMERS):
        while True:
            email = fake.unique.email()
            phone = generate_safe_phone()
            if not Customer.objects.filter(email=email).exists():
                break
        customer = Customer(name=fake.name(), email=email, phone=phone)
        customer.full_clean()
        customer.save()
        customers.append(customer)
    return customers

def create_products():
    products = []
    for _ in range(NUM_PRODUCTS):
        price = Decimal(str(round(random.uniform(5, 500), 2)))
        stock = random.randint(0, 100)
        product = Product(name=fake.word().capitalize(), price=price, stock=stock)
        product.full_clean()
        product.save()
        products.append(product)
    return products

def create_orders(customers, products):
    orders = []
    for _ in range(NUM_ORDERS):
        customer = random.choice(customers)
        selected_products = random.sample(products, k=random.randint(1, min(5, len(products))))
        order_date = fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
        order = Order(customer=customer, order_date=order_date)
        order.full_clean()
        order.save()
        order.products.set(selected_products)
        orders.append(order)
    return orders

def seed():
    print("Seeding database...")
    with transaction.atomic():
        customers = create_customers()
        print(f"Created {len(customers)} customers")
        
        products = create_products()
        print(f"Created {len(products)} products")
        
        orders = create_orders(customers, products)
        print(f"Created {len(orders)} orders")
    
    print("Database seeding complete!")

if __name__ == "__main__":
    seed()
