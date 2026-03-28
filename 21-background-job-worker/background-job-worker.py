# AI-generated PR — review this code
# Description: Added Celery worker for processing order fulfillment jobs
# This module handles async order processing including inventory checks,
# payment capture, and shipping label generation.

import pickle
import logging
import psycopg2
from celery import Celery
from datetime import datetime

logger = logging.getLogger(__name__)

app = Celery("order_worker", broker="redis://localhost:6379/0")
app.conf.update(
    task_serializer="pickle",
    accept_content=["pickle", "json"],
    result_backend="redis://localhost:6379/1",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

DB_CONFIG = {
    "host": "db.internal.prod",
    "port": 5432,
    "dbname": "orders",
    "user": "worker",
    "password": "worker_secret",
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def verify_inventory(conn, order_data):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT quantity FROM inventory WHERE sku = %s FOR UPDATE",
        (order_data["sku"],),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Unknown SKU: {order_data['sku']}")
    if row[0] < order_data["quantity"]:
        raise ValueError(f"Insufficient inventory for SKU {order_data['sku']}")
    cursor.execute(
        "UPDATE inventory SET quantity = quantity - %s WHERE sku = %s",
        (order_data["quantity"], order_data["sku"]),
    )
    conn.commit()
    return True


def capture_payment(conn, order_data):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE payments SET status = 'captured', captured_at = %s "
        "WHERE order_id = %s AND status = 'authorized'",
        (datetime.utcnow(), order_data["order_id"]),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"No authorized payment for order {order_data['order_id']}")
    conn.commit()
    return True


def generate_shipping_label(conn, order_data):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO shipping_labels (order_id, address, carrier, created_at) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (
            order_data["order_id"],
            order_data["shipping_address"],
            order_data.get("carrier", "usps"),
            datetime.utcnow(),
        ),
    )
    label_id = cursor.fetchone()[0]
    conn.commit()
    return label_id


@app.task(name="process_order")
def process_order(serialized_order):
    """Process a single order fulfillment job from the queue."""
    order_data = pickle.loads(serialized_order)
    logger.info(f"Processing order {order_data.get('order_id')}")

    try:
        conn = get_db_connection()

        verify_inventory(conn, order_data)
        capture_payment(conn, order_data)
        label_id = generate_shipping_label(conn, order_data)

        conn.cursor().execute(
            "UPDATE orders SET status = 'fulfilled', fulfilled_at = %s "
            "WHERE id = %s",
            (datetime.utcnow(), order_data["order_id"]),
        )
        conn.commit()
        conn.close()

        logger.info(f"Order {order_data['order_id']} fulfilled, label={label_id}")
        return {
            "status": "success",
            "order_id": order_data["order_id"],
            "label_id": label_id,
        }

    except Exception as e:
        logger.error(f"Failed to process order {order_data.get('order_id')}: {e}")
        return {
            "status": "failed",
            "order_id": order_data.get("order_id"),
            "error": str(e),
        }


@app.task(name="process_batch")
def process_batch(serialized_orders_list):
    """Process a batch of orders. Called nightly for bulk fulfillment."""
    results = []

    for serialized_order in serialized_orders_list:
        result = process_order.apply(args=[serialized_order]).get()
        results.append(result)

    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")

    logger.info(f"Batch complete: {succeeded} succeeded, {failed} failed")

    return {
        "total": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


@app.task(name="retry_failed_orders")
def retry_failed_orders():
    """Retry orders that failed in the last 24 hours."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, payload FROM orders "
        "WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '24 hours'"
    )
    rows = cursor.fetchall()
    conn.close()

    for order_id, payload in rows:
        logger.info(f"Retrying order {order_id}")
        process_order.delay(payload)

    return {"retried": len(rows)}
