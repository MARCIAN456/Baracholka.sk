import uuid
from types import SimpleNamespace

import stripe

ITEM_BODY = {
    "title": "iPhone 13",
    "description": "Good condition, battery 88%, full set included",
    "price": 400,
    "weight": "under_1kg",
}

DELIVERY_BODY = {"username": "Buyer Name", "phone": "+421912345678", "addressId": "1234"}

PACKETA_TOKEN = "packeta-test-secret"


def register_and_login(client, email, password="password123"):
    client.post("/api/v1/auth/register", json={
        "name": "Test User", "email": email, "password": password, "city": "Kosice",
    })
    response = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_item(client, headers, **overrides):
    response = client.post("/api/v1/items/create-item", headers=headers, json={**ITEM_BODY, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def accept_item(db, item_id):
    from app.models.item import Item, ItemStatus
    db.get(Item, uuid.UUID(item_id)).status = ItemStatus.ACCEPTED.value
    db.commit()


def create_delivery(client, headers, item_id):
    response = client.post(f"/api/v1/delivery/create-delivery/{item_id}", headers=headers, json=DELIVERY_BODY)
    assert response.status_code == 201, response.text
    return response.json()


def checkout(client, headers, item_id):
    return client.post(f"/api/v1/payments/create-checkout-session/{item_id}", headers=headers)


def send_stripe_event(client, monkeypatch, event_type, session_id, payment_intent="pi_test"):
    event = SimpleNamespace(
        type=event_type,
        data=SimpleNamespace(object=SimpleNamespace(id=session_id, payment_intent=payment_intent)),
    )
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda payload, sig, secret: event)
    return client.post("/api/v1/payments/webhook", content=b"{}", headers={"stripe-signature": "test"})


def send_packeta(client, barcode, status_code, token=PACKETA_TOKEN):
    return client.post(
        "/api/v1/delivery/packeta_webhook",
        headers={"X-Packeta-Token": token},
        json={"packetId": "1", "barcode": barcode, "statusCode": status_code},
    )
