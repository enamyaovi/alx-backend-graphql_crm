from django.test import TestCase
from graphene.test import Client
from crm.schema import schema
from crm.models import Customer, Product
from django.utils import timezone

class GraphQLMutationTests(TestCase):

    def setUp(self):
        # Initialize GraphQL client
        self.client = Client(schema)

    def test_create_single_customer(self):
        mutation = '''
        mutation {
          createCustomer(input: {
            name: "Alice",
            email: "alice@example.com",
            phone: "+1234567890"
          }) {
            customer {
              id
              name
              email
              phone
            }
            message
          }
        }
        '''
        response = self.client.execute(mutation)
        data = response.get("data", {}).get("createCustomer", {})
        self.assertIsNotNone(data.get("customer"))
        self.assertEqual(data["customer"]["name"], "Alice")
        self.assertEqual(data["customer"]["email"], "alice@example.com")
        self.assertEqual(data["customer"]["phone"], "+1234567890")
        self.assertEqual(data["message"], "Customer created successfully")

    def test_bulk_create_customers(self):
        mutation = '''
        mutation {
          bulkCreateCustomers(input: [
            { name: "Bob", email: "bob@example.com", phone: "123-456-7890" },
            { name: "Carol", email: "carol@example.com" }
          ]) {
            customers {
              id
              name
              email
            }
            errors
          }
        }
        '''
        response = self.client.execute(mutation)
        data = response.get("data", {}).get("bulkCreateCustomers", {})
        customers = data.get("customers", [])
        errors = data.get("errors", [])
        self.assertEqual(len(customers), 2)
        self.assertEqual(customers[0]["name"], "Bob")
        self.assertEqual(customers[1]["name"], "Carol")
        self.assertEqual(len(errors), 0)

    def test_create_product(self):
        mutation = '''
        mutation {
          createProduct(input: {
            name: "Laptop",
            price: 999.99,
            stock: 10
          }) {
            product {
              id
              name
              price
              stock
            }
          }
        }
        '''
        response = self.client.execute(mutation)
        data = response.get("data", {}).get("createProduct", {})
        product = data.get("product", {})
        self.assertEqual(product["name"], "Laptop")
        self.assertEqual(float(product["price"]), 999.99)
        self.assertEqual(product["stock"], 10)

    def test_create_order_with_products(self):
        # First, create a customer and products to reference
        customer = Customer.objects.create(name="Dave", email="dave@example.com", phone="+1987654321")
        product1 = Product.objects.create(name="Item 1", price=50, stock=10)
        product2 = Product.objects.create(name="Item 2", price=150, stock=5)

        mutation = f'''
        mutation {{
          createOrder(input: {{
            customerId: "{customer.id}",
            productIds: ["{product1.id}", "{product2.id}"]
          }}) {{
            order {{
              id
              customer {{
                name
              }}
              products {{
                name
                price
              }}
              totalAmount
              orderDate
            }}
          }}
        }}
        '''
        response = self.client.execute(mutation)
        order_data = response.get("data", {}).get("createOrder", {}).get("order", {})
        self.assertIsNotNone(order_data)
        self.assertEqual(order_data["customer"]["name"], "Dave")
        self.assertEqual(len(order_data["products"]), 2)
        self.assertEqual(order_data["totalAmount"], product1.price + product2.price)
