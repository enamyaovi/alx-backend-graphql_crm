# CRM Automation

This project extends the CRM app with scheduled tasks for reporting, cleanup, and reminders using **cron jobs** and **Celery**.

---

## Features

* **Heartbeat Monitor**
  Logs a timestamped "CRM is alive" message to `/tmp/crm_heartbeat_log.txt`.

* **Customer Cleanup**
  Deletes customers with no orders in the past year and logs the results to `/tmp/customer_cleanup_log.txt`.

* **Order Reminders**
  Fetches recent orders (past 7 days) from the GraphQL API and logs reminders to `/tmp/order_reminders_log.txt`.

* **Celery Reports**
  Scheduled via `django-celery-beat` to generate a CRM summary report with totals for:

  * Customers
  * Orders
  * Revenue

---

## Requirements

* Python 3.10+
* Django
* Redis (for Celery)
* gql (GraphQL client) with requests transport

Install dependencies:

```bash
pip install -r requirements.txt
```

For GraphQL client specifically:

```bash
pip install gql[requests]
```

---

## Cron Jobs

Scripts are located in:
`crm/cron_jobs/scripts/`

* `customer_cleanup.sh` – yearly cleanup
* `order_reminders.py` – weekly reminders

Make scripts executable:

```bash
chmod +x crm/cron_jobs/scripts/*.sh
chmod +x crm/cron_jobs/scripts/*.py
```

Register cron jobs with **django-crontab**:

```bash
python manage.py crontab add
python manage.py crontab show
```

---

## Celery Setup

1. Start Redis (default: `redis://localhost:6379/0`).
2. Start Celery worker:

```bash
celery -A project_name worker -l info
```

3. Start Celery beat scheduler:

```bash
celery -A project_name beat -l info
```

---

## Logs

* Heartbeat → `/tmp/crm_heartbeat_log.txt`
* Cleanup → `/tmp/customer_cleanup_log.txt`
* Reminders → `/tmp/order_reminders_log.txt`
* Reports → `/tmp/crm_report_log.txt`

---

## Notes

* Update `settings.py` with your project’s actual