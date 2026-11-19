import pytest

from app.models.payments import Payout
from tests.helpers import send_packeta


def test_set_iban_shows_in_profile(client, buyer_headers):
    response = client.patch("/api/v1/user/me/iban", headers=buyer_headers, json={"iban": "SK8975000000000012345671"})

    assert response.status_code == 200
    assert client.get("/api/v1/user/me", headers=buyer_headers).json()["iban"] == "SK8975000000000012345671"


@pytest.mark.parametrize("bad_iban", ["123", "SK89", "1234567890123456789"])
def test_invalid_iban_rejected(client, buyer_headers, bad_iban):
    response = client.patch("/api/v1/user/me/iban", headers=buyer_headers, json={"iban": bad_iban})

    assert response.status_code == 422


def test_iban_change_updates_pending_payout(client, db, seller_headers, paid_order):
    send_packeta(client, paid_order.delivery["tracking_number"], 7)

    client.patch("/api/v1/user/me/iban", headers=seller_headers, json={"iban": "CZ6508000000192000145399"})

    assert db.query(Payout).one().iban == "CZ6508000000192000145399"
