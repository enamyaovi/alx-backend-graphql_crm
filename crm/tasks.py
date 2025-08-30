import logging
import os
import requests
from celery import shared_task
from django.conf import settings
from datetime import datetime

logger = logging.getLogger("crm")

@shared_task
def generate_crm_report():
    """
    Celery task that queries CRM stats via GraphQL and logs them.
    """
    graphql_endpoint = os.getenv(
        "GRAPHQL_ENDPOINT",
        getattr(settings, "GRAPHQL_ENDPOINT", "http://localhost:8000/graphql")
    )

    query = """
    query {
        totalCustomers
        totalOrders
        totalRevenue
    }
    """

    try:
        response = requests.post(graphql_endpoint, json={"query": query})
        response.raise_for_status()
        data = response.json()

        stats = data.get("data", {})
        customers = stats.get("totalCustomers", 0)
        orders = stats.get("totalOrders", 0)
        revenue = stats.get("totalRevenue", 0.0)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"{timestamp} - Report: {customers} customers, {orders} orders, {revenue} revenue")

    except Exception as e:
        logger.error(f"Error generating CRM report: {e}", exc_info=True)
