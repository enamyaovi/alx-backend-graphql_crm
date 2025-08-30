#!/bin/bash
# Deletes customers with no orders in the past year and logs results

# Dynamically detect project root (two directories up)
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$DIR")")"
LOG_FILE="/tmp/customer_cleanup_log.txt"

cd "$PROJECT_DIR" || exit 1

/usr/bin/python3 manage.py shell -c "
from datetime import timedelta, datetime
from django.utils import timezone
from crm.models import Customer

cutoff = timezone.now() - timedelta(days=365)
qs = Customer.objects.filter(order__created_at__lte=cutoff).distinct()
deleted_count, deleted_details = qs.delete()
print(f'{datetime.now()} - Deleted {deleted_count} objects. Breakdown: {deleted_details}')
" >> \"$LOG_FILE\" 2>&1
