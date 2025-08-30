import logging
import os
import requests
from datetime import datetime
from django.conf import settings

logger = logging.getLogger("crm")

def log_crm_heartbeat():
    """
    Cron job to log CRM heartbeat and optionally check GraphQL hello.
    """
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    logger.info(f"{timestamp} CRM is alive")

    graphql_endpoint = os.getenv(
        "GRAPHQL_ENDPOINT",
        getattr(settings, "GRAPHQL_ENDPOINT", "http://localhost:8000/graphql")
    )

    try:
        query = """query { hello }"""
        response = requests.post(graphql_endpoint, json={"query": query})
        response.raise_for_status()
        data = response.json()
        logger.info(f"GraphQL hello response: {data.get('data', {}).get('hello')}")
    except Exception as e:
        logger.error(f"Error querying GraphQL hello: {e}", exc_info=True)


def update_low_stock():
    """
    Cron job to update low-stock products via GraphQL mutation.
    """
    graphql_endpoint = os.getenv(
        "GRAPHQL_ENDPOINT",
        getattr(settings, "GRAPHQL_ENDPOINT", "http://localhost:8000/graphql")
    )

    mutation = """
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

    try:
        response = requests.post(graphql_endpoint, json={"query": mutation})
        response.raise_for_status()
        data = response.json()

        products = data.get("data", {}).get("updateLowStockProducts", {}).get("updatedProducts", [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if products:
            for p in products:
                logger.info(f"{timestamp} - Restocked {p['name']} to {p['stock']}")
        else:
            logger.info(f"{timestamp} - No low-stock products updated")

    except Exception as e:
        logger.error(f"Error updating low-stock products: {e}", exc_info=True)
