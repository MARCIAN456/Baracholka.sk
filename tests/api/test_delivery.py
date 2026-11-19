from tests.helpers import DELIVERY_BODY


def test_create_delivery_is_draft_with_item_weight(client, draft_delivery):
    assert draft_delivery["status"] == "draft"
    assert draft_delivery["weight"] == 1.0     # under_1kg -> 1.0, клієнт вагу не передає
    assert draft_delivery["value"] == 400


def test_cannot_create_delivery_for_own_item(client, seller_headers, item):
    response = client.post(f"/api/v1/delivery/create-delivery/{item['id']}", headers=seller_headers, json=DELIVERY_BODY)

    assert response.status_code == 400


def test_invalid_phone_returns_422(client, buyer_headers, item):
    response = client.post(f"/api/v1/delivery/create-delivery/{item['id']}", headers=buyer_headers,
                           json={**DELIVERY_BODY, "phone": "call me"})

    assert response.status_code == 422


def test_second_create_updates_same_draft(client, buyer_headers, item, draft_delivery):
    response = client.post(f"/api/v1/delivery/create-delivery/{item['id']}", headers=buyer_headers,
                           json={**DELIVERY_BODY, "phone": "+421900111222"})

    assert response.json()["id"] == draft_delivery["id"]
    assert response.json()["phone"] == "+421900111222"


def test_foreign_user_cannot_see_delivery(client, other_buyer_headers, draft_delivery):
    response = client.get(f"/api/v1/delivery/{draft_delivery['id']}", headers=other_buyer_headers)

    assert response.status_code == 403


def test_seller_does_not_see_unpaid_drafts(client, seller_headers, draft_delivery):
    response = client.get("/api/v1/delivery/my", headers=seller_headers, params={"role": "seller"})

    assert response.json()["total"] == 0


def test_seller_sees_paid_delivery(client, seller_headers, paid_order):
    response = client.get(f"/api/v1/delivery/{paid_order.delivery['id']}", headers=seller_headers)

    assert response.status_code == 200
    assert client.get("/api/v1/delivery/my", headers=seller_headers, params={"role": "seller"}).json()["total"] == 1
