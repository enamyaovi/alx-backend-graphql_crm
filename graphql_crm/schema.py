import re
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from crm.models import Customer, Product, Order
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from crm.filters import CustomerFilter, ProductFilter, OrderFilter

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order


class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()

class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(customer=None, message="Email already exists")
        if input.phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', input.phone):
            return CreateCustomer(customer=None, message="Invalid phone number format")
        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(BulkCustomerInput), required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created_customers = []
        errors = []
        for i, data in enumerate(input):
            try:
                if Customer.objects.filter(email=data.email).exists():
                    errors.append(f"Customer {i+1}: Email already exists: {data.email}")
                    continue
                if data.phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', data.phone):
                    errors.append(f"Customer {i+1}: Invalid phone format: {data.phone}")
                    continue
                customer = Customer.objects.create(
                    name=data.name,
                    email=data.email,
                    phone=data.phone
                )
                created_customers.append(customer)
            except Exception as e:
                errors.append(f"Customer {i+1}: {str(e)}")
        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    def mutate(self, info, input):
        if Decimal(input.price) <= 0:
            return CreateProduct(product=None, message="Price must be positive")
        if input.stock is not None and input.stock < 0:
            return CreateProduct(product=None, message="Stock cannot be negative")
        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock if input.stock is not None else 0
        )
        return CreateProduct(product=product, message="Product created successfully")


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(order=None, message="Invalid customer ID")

        if not input.product_ids:
            return CreateOrder(order=None, message="At least one product must be selected")

        products = Product.objects.filter(id__in=input.product_ids)
        if not products.exists() or products.count() != len(input.product_ids):
            return CreateOrder(order=None, message="Some product IDs are invalid")

        total_amount = sum(p.price for p in products)

        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=input.order_date or timezone.now()
        )
        order.products.set(products)
        return CreateOrder(order=order, message="Order created successfully")

class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)

    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
