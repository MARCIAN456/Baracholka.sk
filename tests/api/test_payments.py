import stripe

from app.models.item import Item
from app.models.payments import Payment
from tests.helpers import checkout, create_delivery, send_stripe_event


def test_checkout_without_delivery_returns_400(client, fake_stripe, buyer_headers, item):
    response = checkout(client, buyer_headers, item["id"])

    assert response.status_code == 400
    assert fake_stripe.created == []


def test_checkout_own_item_returns_400(client, fake_stripe, seller_headers, item):
    assert checkout(client, seller_headers, item["id"]).status_code == 400


def test_checkout_sends_exact_cents_to_stripe(client, db, fake_stripe, seller_headers, buyer_headers, item):
    client.patch(f"/api/v1/items/update-item/{item['id']}", headers=seller_headers, json={"price": 19.99})
    create_delivery(client, buyer_headers, item["id"])

    response = checkout(client, buyer_headers, item["id"])

    assert response.status_code == 200
    assert fake_stripe.created[0]["line_items"][0]["price_data"]["unit_amount"] == 1999
    payment = db.query(Payment).one()
    assert payment.status == "pending"
    assert payment.amount == 19.99


def test_second_checkout_expires_old_session_and_reuses_payment(client, db, fake_stripe, buyer_headers, item, draft_delivery):
    checkout(client, buyer_headers, item["id"])

    checkout(client, buyer_headers, item["id"])

    assert fake_stripe.expired == ["cs_test_1"]
    payment = db.query(Payment).one()
    assert payment.stripe_session_id == "cs_test_2"


def test_checkout_blocked_when_previous_session_already_paid(client, fake_stripe, buyer_headers, item, draft_delivery):
    checkout(client, buyer_headers, item["id"])
    fake_stripe.retrieve_status = "complete"

    response = checkout(client, buyer_headers, item["id"])

    assert response.status_code == 400
    assert len(fake_stripe.created) == 1


def test_webhook_rejects_invalid_signature(client):
    response = client.post("/api/v1/payments/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=fake"})

    assert response.status_code == 400


def test_completed_marks_paid_and_sold(client, db, paid_order):
    payment = db.query(Payment).one()
    assert payment.status == "paid"
    assert db.query(Item).one().is_sold is True
    assert paid_order.delivery["status"] == "pending"
    assert paid_order.delivery["tracking_number"].startswith("Z")
    assert client.get("/api/v1/items/").json()["total"] == 0


def test_completed_deletes_other_buyers_drafts(client, monkeypatch, fake_stripe, buyer_headers, other_buyer_headers, item, draft_delivery):
    create_delivery(client, other_buyer_headers, item["id"])
    session_id = checkout(client, buyer_headers, item["id"]).json()["session_id"]

    send_stripe_event(client, monkeypatch, "checkout.session.completed", session_id)

    assert client.get("/api/v1/delivery/my", headers=other_buyer_headers).json()["total"] == 0
    assert client.get("/api/v1/delivery/my", headers=buyer_headers).json()["total"] == 1


def test_duplicate_completed_event_does_not_refund(client, db, monkeypatch, fake_stripe, paid_order):
    send_stripe_event(client, monkeypatch, "checkout.session.completed", paid_order.session_id)

    assert fake_stripe.refunds == []
    assert db.query(Payment).one().status == "paid"


def _two_buyers_race(client, monkeypatch, buyer_headers, other_buyer_headers, item):
    create_delivery(client, buyer_headers, item["id"])
    create_delivery(client, other_buyer_headers, item["id"])
    first = checkout(client, buyer_headers, item["id"]).json()["session_id"]
    second = checkout(client, other_buyer_headers, item["id"]).json()["session_id"]
    send_stripe_event(client, monkeypatch, "checkout.session.completed", first)
    return second


def test_late_payment_for_sold_item_is_refunded(client, db, monkeypatch, fake_stripe, buyer_headers, other_buyer_headers, item):
    second = _two_buyers_race(client, monkeypatch, buyer_headers, other_buyer_headers, item)

    response = send_stripe_event(client, monkeypatch, "checkout.session.completed", second, payment_intent="pi_second")

    assert response.json()["status"] == "item_already_sold_refunded"
    assert fake_stripe.refunds == [{"payment_intent": "pi_second", "idempotency_key": f"refund-{second}"}]
    assert db.query(Payment).filter_by(stripe_session_id=second).one().status == "refunded"


def test_refund_already_done_on_stripe_still_marks_refunded(client, db, monkeypatch, fake_stripe, buyer_headers, other_buyer_headers, item):
    second = _two_buyers_race(client, monkeypatch, buyer_headers, other_buyer_headers, item)
    fake_stripe.refund_error = stripe.InvalidRequestError("already refunded", None, code="charge_already_refunded")

    send_stripe_event(client, monkeypatch, "checkout.session.completed", second)

    assert db.query(Payment).filter_by(stripe_session_id=second).one().status == "refunded"


def test_refund_failure_returns_502_and_keeps_pending(client, db, monkeypatch, fake_stripe, buyer_headers, other_buyer_headers, item):
    second = _two_buyers_race(client, monkeypatch, buyer_headers, other_buyer_headers, item)
    fake_stripe.refund_error = stripe.APIConnectionError("network down")

    response = send_stripe_event(client, monkeypatch, "checkout.session.completed", second)

    assert response.status_code == 502
    assert db.query(Payment).filter_by(stripe_session_id=second).one().status == "pending"


def test_expired_cancels_pending_and_checkout_reuses_it(client, db, monkeypatch, fake_stripe, buyer_headers, item, draft_delivery):
    checkout(client, buyer_headers, item["id"])
    send_stripe_event(client, monkeypatch, "checkout.session.expired", "cs_test_1")
    assert db.query(Payment).one().status == "cancelled"

    checkout(client, buyer_headers, item["id"])

    payment = db.query(Payment).one()
    assert payment.status == "pending"
    assert payment.stripe_session_id == "cs_test_2"


def test_expired_does_not_touch_paid_payment(client, db, monkeypatch, paid_order):
    send_stripe_event(client, monkeypatch, "checkout.session.expired", paid_order.session_id)

    assert db.query(Payment).one().status == "paid"
