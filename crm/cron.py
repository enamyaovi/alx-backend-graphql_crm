import logging
import os
from datetime import datetime
from django.conf import settings
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure separate loggers for cron jobs
heartbeat_logger = logging.getLogger("crm.heartbeat")
low_stock_logger = logging.getLogger("crm.low_stock")

heartbeat_handler = logging.FileHandler("/tmp/crm_heartbeat_log.txt")
heartbeat_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
heartbeat_logger.addHandler(heartbeat_handler)
heartbeat_logger.setLevel(logging.INFO)

low_stock_handler = logging.FileHandler("/tmp/low_stock_updates_log.txt")
low_stock_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
low_stock_logger.addHandler(low_stock_handler)
low_stock_logger.setLevel(logging.INFO)


def get_client():
    graphql_endpoint = os.getenv(
        "GRAPHQL_ENDPOINT",
        getattr(settings, "GRAPHQL_ENDPOINT", "http://localhost:8000/graphql"),
    )
    transport = RequestsHTTPTransport(url=graphql_endpoint, verify=True, retries=3)
    return Client(transport=transport, fetch_schema_from_transport=True)


def log_crm_heartbeat():
    """
    Cron job to log CRM heartbeat and check GraphQL hello.
    """
    client = get_client()
    query = gql("""query { hello }""")

    try:
        result = client.execute(query)
        hello_value = result.get("hello", "No response")
        heartbeat_logger.info(f"CRM is alive - GraphQL hello response: {hello_value}")
    except Exception as e:
        heartbeat_logger.error(f"Error querying GraphQL hello: {e}", exc_info=True)


def update_low_stock():
    """
    Cron job to update low-stock products via GraphQL mutation.
    """
    client = get_client()
    mutation = gql(
        """
        mutation {
            updateLowStockProducts {
                success
                updatedProducts {
                    name
                    stock
                }
            }
        }
        """
    )

    try:
        result = client.execute(mutation)
        products = result.get("updateLowStockProducts", {}).get("updatedProducts", [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if products:
            for p in products:
                low_stock_logger.info(f"{timestamp} - Restocked {p['name']} to {p['stock']}")
        else:
            low_stock_logger.info(f"{timestamp} - No low-stock products updated")

    except Exception as e:
        low_stock_logger.error(f"Error updating low-stock products: {e}", exc_info=True)
