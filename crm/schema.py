import graphene
from graphql import GraphQLError
# from graphene_validators
from graphene_django import DjangoObjectType
from crm.models import Customer, Order, Product
import datetime, re

def phone_number_validator(number):
    pattern = r"^\+[0-9\-\(\)\/\.\s]{6,15}[0-9]$"
    return re.match(pattern, number) is not None

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=True)
    
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
    all_customers = graphene.List(CustomerType)
    customers_by_name = graphene.Field(
        CustomerType, name=graphene.String(required=True))
    
    def resolve_all_orders(parent, info): # type: ignore
        return Order.objects.select_related('customer_id').select_related('product_id').all()
    
    def resolve_all_customers(parent, info): # type: ignore
        return Customer.objects.prefetch_related('orders').all()
    
    def resolve_customers_by_name(parent, info, name): # type: ignore
        try:
            return Customer.objects.prefetch_related('orders').get(name=name)
        except Customer.DoesNotExist:
            return None
        
    def resolve_all_products(parent, info): # type: ignore
        return Product.objects.prefetch_related('product_orders').all()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.Field(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, name, email, phone):

        if Customer.objects.filter(email=email).exists():
            raise GraphQLError("Sorry Customer with email exists")

        if Customer.objects.filter(phone=phone).exists():
            raise GraphQLError("Sorry a user with this phone number exists")

        if phone_number_validator(number=phone) is None:
            raise GraphQLError("Invalid Phone Number")

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        message = f"Customer {customer.name} created!"
        return CreateCustomer(
            customer=customer, message=message)  # type: ignore
    

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(CustomerInput, required=True)
    
    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    message= graphene.Field(graphene.String)
    ok = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, customers):
        errors = []
        valid_objs = []

        incoming_emails = [c.email.lower() for c in customers]
        incoming_phone_nums = [c.phone for c in customers]

        existing_emails = set(
            Customer.objects.filter(email__in=incoming_emails).values_list(
                'email', flat=True))
        existing_phone_nums = set(
            Customer.objects.filter(phone__in=incoming_phone_nums).values_list(
                'phone', flat=True))
        
        for index, customer in enumerate(customers):
            if customer.email in existing_emails:
                errors.append(f"[{index}]: Customer with {customer.email} already exists")
                continue

            if customer.phone in existing_phone_nums:
                errors.append(f"[{index}]: Customer with {customer.phone} already exists")
                continue
                
            if phone_number_validator(number=customer.phone) is None:
                errors.append(f"[{index}]: {customer.phone} is not valid")
                continue



            valid_objs.append(Customer(
                name=customer.name,
                email=customer.email,
                phone=customer.phone))
            
            #didn't use this method because it results in more database hits than needed
        # for customer in customers:
            # if Customer.objects.filter(email=customer.email).exists():
            # if Customer.objects.filter(phone=customer.phone).exists():

        if valid_objs:
            Customer.objects.bulk_create(valid_objs)

        #output message
        if valid_objs and errors:
            message = f"Created {len(valid_objs)} customers, {len(errors)} failed."
        elif valid_objs:
            message = f"Successfully created {len(valid_objs)} customers."
        else:
            message = "No customers created."

        return BulkCreateCustomers(
            created_customers=valid_objs, errors=errors, ok=bool(valid_objs),message=message) # type: ignore


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(default_value=0)

    product = graphene.Field(ProductType)

    def mutate(parent, info, name, price, stock): # type: ignore

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
        product_ids=graphene.ID(required=True)
        order_date=graphene.DateTime(default=datetime.datetime.now())
        
    order = graphene.Field(OrderType)

    def mutate(parent, info, customer_id, product_id, order_date): # type: ignore
        if not Customer.objects.filter(id=customer_id).exists():
                raise Customer.DoesNotExist(f"Customer: {customer_id} Does Not Exist")
        if not Product.objects.filter(id=product_id).exists():
            raise Product.DoesNotExist(f"Product with id: {product_id} does not exist")
        order = Order(customer_id=customer_id, product_id=product_id, order_date=order_date)
        order.save()
        return CreateOrder(order=order) # type: ignore

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)


#dummy code for the checker

# class Query(graphene.ObjectType):
    # hello = graphene.String(default_value="Hello, GraphQL!")
# 
    # def resolve_hello(parent, info): # type: ignore
        # return 'Hello, GraphQL!'
    

# schema = graphene.Schema(query=Query)

#total_amount
#try:
#except: