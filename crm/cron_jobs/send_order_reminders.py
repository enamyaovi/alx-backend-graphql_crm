#!/usr/bin/env python3

import os
import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Detect project root (two directories up from this script)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure standalone logger
LOG_FILE = "/tmp/order_reminders_log.txt"
logger = logging.getLogger("order_reminders")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)


def main():
    # GraphQL endpoint
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Calculate cutoff date (7 days ago)
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=7)).date().isoformat()

    # GraphQL query
    query = gql("""
    query GetRecentOrders($cutoff: Date!) {
        orders(orderDate_Gte: $cutoff) {
            id
            customer {
                email
            }
        }
    }
    """)

    params = {"cutoff": cutoff}

    try:
        result = client.execute(query, variable_values=params)
        orders = result.get("orders", [])
    except Exception as e:
        logger.error(f"Error while fetching orders: {e}", exc_info=True)
        print("Error while fetching orders.")
        return

    # Log results
    for order in orders:
        logger.info(f"Reminder: Order {order['id']} for {order['customer']['email']}")

    print("Order reminders processed!")


if __name__ == "__main__":
    main()
