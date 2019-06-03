"""
Hubspot tasks
"""
import logging

from hubspot.api import (
    send_hubspot_request,
    make_contact_sync_message,
    make_product_sync_message,
    make_deal_sync_message,
    make_line_item_sync_message,
    get_sync_errors,
    hubspot_timestamp,
)
from hubspot.models import HubspotErrorCheck
from mitxpro.celery import app
from mitxpro.utils import now_in_utc

log = logging.getLogger()

HUBSPOT_SYNC_URL = "/extensions/ecomm/v1/sync-messages"


@app.task
def sync_contact_with_hubspot(user_id):
    """Send a sync-message to sync a user with a hubspot contact"""
    body = [make_contact_sync_message(user_id)]
    response = send_hubspot_request("CONTACT", HUBSPOT_SYNC_URL, "PUT", body=body)
    response.raise_for_status()


@app.task
def sync_product_with_hubspot(product_id):
    """Send a sync-message to sync a product with a hubspot product"""
    body = [make_product_sync_message(product_id)]
    response = send_hubspot_request("PRODUCT", HUBSPOT_SYNC_URL, "PUT", body=body)
    response.raise_for_status()


@app.task
def sync_deal_with_hubspot(order_id):
    """Send a sync-message to sync an order with a hubspot deal"""
    body = [make_deal_sync_message(order_id)]
    response = send_hubspot_request("DEAL", HUBSPOT_SYNC_URL, "PUT", body=body)
    response.raise_for_status()


@app.task
def sync_line_item_with_hubspot(line_id):
    """Send a sync-message to sync a line with a hubspot line item"""
    body = [make_line_item_sync_message(line_id)]
    response = send_hubspot_request("LINE_ITEM", HUBSPOT_SYNC_URL, "PUT", body=body)
    response.raise_for_status()


@app.task
def check_hubspot_api_errors():
    """Check for and log any errors that occurred since the last time this was run"""
    last_check, _ = HubspotErrorCheck.objects.get_or_create(
        defaults={"checked_on": now_in_utc()}
    )
    last_timestamp = hubspot_timestamp(last_check.checked_on)
    for error in get_sync_errors(last_timestamp):
        msg = "Hubspot error for {obj_type} id {obj_id}: {details}".format(
            obj_type=error.get("objectType", "N/A"),
            obj_id=error.get("integratorObjectId", "N/A"),
            details=error.get("details", ""),
        )
        log.error(msg)

    last_check.checked_on = now_in_utc()
    last_check.save()
