import os
import django
import random
from faker import Faker

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
django.setup()

from crm.models import Customer, Product, Order
from django.utils import timezone

fake = Faker()

NUM_CUSTOMERS = 20
NUM_PRODUCTS = 10
NUM_ORDERS = 15

def create_customers():
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

def create_products():
    products = []
    for _ in range(NUM_PRODUCTS):
        product = Product.objects.create(
            name=fake.word().capitalize(),
            price=round(random.uniform(5, 500), 2),
            stock=random.randint(0, 100)
        )
        products.append(product)
    return products

def create_orders(customers, products):
    orders = []
    for _ in range(NUM_ORDERS):
        customer = random.choice(customers)
        selected_products = random.sample(products, k=random.randint(1, min(5, len(products))))
        order_date = fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
        order = Order.objects.create(
            customer=customer,
            order_date=order_date,
            total_amount=sum(p.price for p in selected_products)
        )
        order.products.set(selected_products)
        orders.append(order)
    return orders

def run():
    print("Seeding database...")
    customers = create_customers()
    print(f"Created {len(customers)} customers")
    
    products = create_products()
    print(f"Created {len(products)} products")
    
    orders = create_orders(customers, products)
    print(f"Created {len(orders)} orders")
    
    print("Database seeding complete!")

if __name__ == "__main__":
    run()
