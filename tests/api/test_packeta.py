import stripe

from app.models.item import Item
from app.models.payments import Payment, Payout
from tests.helpers import checkout, create_delivery, send_packeta


def test_wrong_token_returns_403(client, paid_order):
    assert send_packeta(client, paid_order.delivery["tracking_number"], 7, token="hacker").status_code == 403


def test_missing_token_returns_403(client):
    response = client.post("/api/v1/delivery/packeta_webhook",
                           json={"packetId": "1", "barcode": "Z1", "statusCode": 7})

    assert response.status_code == 403


def test_unknown_barcode_is_ignored(client, db):
    assert send_packeta(client, "Z000000000", 7).json()["status"] == "ignored"


def test_delivered_completes_payment_and_creates_payout(client, db, paid_order):
    response = send_packeta(client, paid_order.delivery["tracking_number"], 7)

    assert response.json()["status"] == "delivered"
    assert db.query(Payment).one().status == "completed"
    payout = db.query(Payout).one()
    assert payout.amount == 400
    assert payout.iban == "SK8975000000000012345671"
    assert payout.status == "pending"


def test_delivered_twice_creates_one_payout(client, db, paid_order):
    send_packeta(client, paid_order.delivery["tracking_number"], 7)
    send_packeta(client, paid_order.delivery["tracking_number"], 7)

    assert db.query(Payout).count() == 1


def test_returned_refunds_buyer_and_relists_item(client, db, fake_stripe, paid_order):
    response = send_packeta(client, paid_order.delivery["tracking_number"], 10)

    assert response.json()["status"] == "returned_and_refunded"
    assert fake_stripe.refunds == [{"payment_intent": "pi_test"}]
    assert db.query(Payment).one().status == "refunded"
    assert db.query(Item).one().is_sold is False
    assert client.get("/api/v1/items/").json()["total"] == 1


def test_buyer_can_buy_again_after_return(client, db, fake_stripe, buyer_headers, paid_order):
    send_packeta(client, paid_order.delivery["tracking_number"], 10)

    new_delivery = create_delivery(client, buyer_headers, paid_order.item["id"])
    response = checkout(client, buyer_headers, paid_order.item["id"])

    assert new_delivery["id"] != paid_order.delivery["id"]
    assert response.status_code == 200
    assert db.query(Payment).count() == 2


def test_returned_with_stripe_error_changes_nothing(client, db, fake_stripe, paid_order):
    fake_stripe.refund_error = stripe.APIConnectionError("network down")

    response = send_packeta(client, paid_order.delivery["tracking_number"], 10)

    assert response.status_code == 502
    assert db.query(Payment).one().status == "paid"
    assert db.query(Item).one().is_sold is True
