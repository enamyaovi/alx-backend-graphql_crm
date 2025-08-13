import graphene
from graphql import GraphQLError
# from graphene_validators
from graphene_django import DjangoObjectType
from crm.models import Customer, Order, Product
import datetime, re

def phone_number_validator(number):
    pattern = r"^\+[0-9\-\(\)\/\.\s]{6,15}[0-9]$"
    return re.match(pattern, number) is not None

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"

class OrderType(DjangoObjectType):
    class Meta:
        model = Order 
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class Query(graphene.ObjectType):
    all_orders = graphene.List(OrderType)
    all_products = graphene.List(ProductType)
    customers_by_name = graphene.Field(
        CustomerType, name=graphene.String(required=True))
    
    def resolve_all_orders(self, info):
        return Order.objects.select_related('customer_id').all()
    
    def resolve_customers_by_name(self, info, name):
        try:
            return Customer.objects.prefetch_related('orders').get(name=name)
        except Customer.DoesNotExist:
            return None
        
    def resolve_all_products(self, info):
        return Product.objects.prefetch_related('product_orders').all()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)
    
    customer = graphene.Field(CustomerType)

    
    def mutate(self, info, name, email, phone):

        if Customer.objects.filter(email=email).exists():
            raise GraphQLError("Sorry Customer with email exists")

        if Customer.objects.filter(phone=phone).exists():
            raise GraphQLError("Sorry a user with this phone number exists")

        if phone_number_validator(number=phone) is None:
            raise GraphQLError("Invalid Phone Number")

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer)  # type: ignore
    

# class BulkCreateCustomers(graphene.Mutation):
    # pass 

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(default_value=0)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):

        if not price >= 0:
            raise ValueError("The Product Price should be positive")
        
        if not stock >= 0:
            raise ValueError("Stock cannot be less than zero")
        
        product = Product(name, price, stock)
        product.save()
        return CreateProduct(product=product) # type: ignore
    
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id=graphene.ID(required=True)
        product_id=graphene.ID(required=True)
        order_date=graphene.DateTime(default=datetime.datetime.now())
        
    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_id, order_date):
        if not Customer.objects.filter(id=customer_id).exists():
                raise Customer.DoesNotExist(f"Customer: {customer_id} Does Not Exist")
        if not Product.objects.filter(id=product_id).exists():
            raise Product.DoesNotExist(f"Product with id: {product_id} does not exist")
        order = Order(customer_id=customer_id, product_id=product_id, order_date=order_date)
        order.save()
        return CreateOrder(order=order) # type: ignore

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    create_product = CreateProduct.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
