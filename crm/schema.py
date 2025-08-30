import re
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from crm.models import Product, Customer, Order
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from decimal import Decimal
from crm.filters import CustomerFilter, ProductFilter, OrderFilter
from graphql import GraphQLError

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class OrderType(DjangoObjectType):
    orderDate = graphene.DateTime(source="order_date")
    
    def resolve_product(parent, info):
        return self.products.first()
    
    class Meta:
        model = Order
        fields = "__all__"

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        try:
            if Customer.objects.filter(email=input.email).exists():
                raise GraphQLError("Email already exists")
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone
            )
            customer.full_clean()
            customer.save()
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except ValidationError as e:
            raise GraphQLError(str(e)) from None

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(CustomerInput), required=True)
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        created_customers = []
        errors = []
        for i, data in enumerate(input):
            try:
                if Customer.objects.filter(email=data.email).exists():
                    errors.append(f"Customer {i+1}: Email already exists")
                    continue
                if data.phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', data.phone):
                    errors.append(f"Customer {i+1}: Invalid phone format")
                    continue
                customer = Customer(
                    name=data.name,
                    email=data.email,
                    phone=data.phone
                )
                customer.full_clean()
                customer.save()
                created_customers.append(customer)
            except ValidationError as e:
                errors.append(f"Customer {i+1}: {str(e)}")
            except Exception as e:
                errors.append(f"Customer {i+1}: {str(e)}")
        return BulkCreateCustomers(customers=created_customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input):
        try:
            product = Product(
                name=input.name,
                price=Decimal(input.price),
                stock=input.stock if input.stock is not None else 0
            )
            product.full_clean()
            product.save()
            return CreateProduct(product=product)
        except ValidationError as e:
            raise GraphQLError(str(e)) from None

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    order = graphene.Field(OrderType)

    @staticmethod
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except ObjectDoesNotExist:
            raise GraphQLError("Invalid customer ID")

        products = Product.objects.filter(pk__in=input.product_ids)
        if not products.exists() or products.count() != len(set(map(str, input.product_ids))):
            raise GraphQLError("Invalid product ID")

        try:
            order = Order(
                customer=customer,
                order_date=input.order_date or timezone.now(),
                total_amount=sum(p.price for p in products)
            )
            order.full_clean()
            order.save()
            order.products.set(products)
            return CreateOrder(order=order)
        except ValidationError as e:
            raise GraphQLError(str(e)) from None
        except Exception as e:
            raise GraphQLError(str(e)) from None

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass 

    success = graphene.String()
    updated_products = graphene.List(ProductType)

    @classmethod
    def mutate(cls, root, info):
        updated = []
        low_stock_products = Product.objects.filter(stock__lt=10)

        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)

        return UpdateLowStockProducts(
            success=f"Restocked {len(updated)} products",
            updated_products=updated,
        )

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
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
