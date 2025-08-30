import logging
import os
import requests
from celery import shared_task
from django.conf import settings
from datetime import datetime

# Ensure logger writes to /tmp/crm_report_log.txt
logger = logging.getLogger("crm")
logger.setLevel(logging.INFO)

log_file = "/tmp/crm_report_log.txt"
if not logger.handlers:  
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


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

        logger.info(
            "Report: %s customers, %s orders, %s revenue",
            customers,
            orders,
            revenue,
        )

    except Exception as e:
        logger.error("Error generating CRM report: %s", e, exc_info=True)
