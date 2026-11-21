import uuid

import pytest

from app.api.v1.endpoints import items as items_endpoint
from app.models.image import ItemImage
from tests.helpers import ITEM_BODY, accept_item, create_item, create_delivery


def test_create_item_without_iban_returns_400(client, buyer_headers):
    response = client.post("/api/v1/items/create-item", headers=buyer_headers, json=ITEM_BODY)

    assert response.status_code == 400


def test_create_item_with_iban(client, seller_headers):
    response = client.post("/api/v1/items/create-item", headers=seller_headers, json=ITEM_BODY)

    assert response.status_code == 201
    assert response.json()["is_sold"] is False
    assert response.json()["price"] == 400


def test_create_item_without_token_returns_401(client):
    response = client.post("/api/v1/items/create-item", json=ITEM_BODY)

    assert response.status_code == 401


@pytest.mark.parametrize("price", [0, -5, 100_001])
def test_create_item_with_invalid_price_returns_422(client, seller_headers, price):
    response = client.post("/api/v1/items/create-item", headers=seller_headers, json={**ITEM_BODY, "price": price})

    assert response.status_code == 422


def test_create_item_with_short_description_returns_422(client, seller_headers):
    response = client.post("/api/v1/items/create-item", headers=seller_headers, json={**ITEM_BODY, "description": "short"})

    assert response.status_code == 422


def test_list_items(client, item):
    response = client.get("/api/v1/items/")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_new_item_is_pending_and_hidden_from_list(client, seller_headers):
    created = create_item(client, seller_headers)

    response = client.get("/api/v1/items/")

    assert created["status"] == "pending"
    assert response.json()["total"] == 0


def test_search_is_case_insensitive(client, db, seller_headers, item):
    accept_item(db, create_item(client, seller_headers, title="Bicycle")["id"])

    response = client.get("/api/v1/items/", params={"search": "iphone"})

    assert [i["title"] for i in response.json()["items"]] == ["iPhone 13"]


def test_price_filter(client, db, seller_headers):
    for title, price in [("Cheap", 10), ("Mid", 100), ("Expensive", 1000)]:
        accept_item(db, create_item(client, seller_headers, title=title, price=price)["id"])

    response = client.get("/api/v1/items/", params={"min_price": 50, "max_price": 500})

    assert [i["title"] for i in response.json()["items"]] == ["Mid"]


def test_get_unknown_item_returns_404(client):
    response = client.get(f"/api/v1/items/get-item-by-id/{uuid.uuid4()}")

    assert response.status_code == 404


def test_item_detail_does_not_leak_owner_email(client, item):
    response = client.get(f"/api/v1/items/get-item-by-id/{item['id']}")

    assert response.status_code == 200
    assert "email" not in response.json()["owner"]


def test_update_own_item(client, seller_headers, item):
    response = client.patch(f"/api/v1/items/update-item/{item['id']}", headers=seller_headers, json={"price": 350})

    assert response.status_code == 200
    assert response.json()["price"] == 350


def test_update_foreign_item_returns_403(client, buyer_headers, item):
    response = client.patch(f"/api/v1/items/update-item/{item['id']}", headers=buyer_headers, json={"price": 1})

    assert response.status_code == 403


def test_update_with_null_title_keeps_old_title(client, seller_headers, item):
    response = client.patch(f"/api/v1/items/update-item/{item['id']}", headers=seller_headers, json={"title": None})

    assert response.status_code == 200
    assert response.json()["title"] == "iPhone 13"


def test_update_sold_item_returns_400(client, seller_headers, paid_order):
    response = client.patch(f"/api/v1/items/update-item/{paid_order.item['id']}", headers=seller_headers, json={"price": 1})

    assert response.status_code == 400


def test_delete_foreign_item_returns_403(client, buyer_headers, item):
    response = client.delete(f"/api/v1/items/{item['id']}", headers=buyer_headers)

    assert response.status_code == 403


def test_delete_own_item(client, seller_headers, item):
    response = client.delete(f"/api/v1/items/{item['id']}", headers=seller_headers)

    assert response.status_code == 204
    assert client.get(f"/api/v1/items/get-item-by-id/{item['id']}").status_code == 404


def test_delete_paid_item_returns_400(client, seller_headers, paid_order):
    response = client.delete(f"/api/v1/items/{paid_order.item['id']}", headers=seller_headers)

    assert response.status_code == 400


def test_delete_item_with_buyer_draft_delivery(client, seller_headers, buyer_headers, item):
    create_delivery(client, buyer_headers, item["id"])

    response = client.delete(f"/api/v1/items/{item['id']}", headers=seller_headers)

    assert response.status_code == 204


def test_delete_item_survives_cloudinary_failure(client, db, seller_headers, item, monkeypatch):
    db.add(ItemImage(item_id=uuid.UUID(item["id"]), image_url="https://img.test/1.jpg", public_id="baracholka/1"))
    db.commit()
    calls = []

    def broken_delete(public_id):
        calls.append(public_id)
        raise RuntimeError("Cloudinary is down")

    monkeypatch.setattr(items_endpoint, "delete_photo", broken_delete)

    response = client.delete(f"/api/v1/items/{item['id']}", headers=seller_headers)

    assert response.status_code == 204
    assert calls == ["baracholka/1"]
    assert db.query(ItemImage).count() == 0


def test_upload_rejects_fake_image(client, seller_headers, item, monkeypatch):
    monkeypatch.setattr(items_endpoint, "upload_photo", lambda f: pytest.fail("must not reach Cloudinary"))
    files = [("files", ("virus.png", b"MZ\x90\x00 this is not an image", "image/png"))]

    response = client.post(f"/api/v1/items/{item['id']}/images", headers=seller_headers, files=files)

    assert response.status_code == 400


def test_upload_to_foreign_item_returns_403(client, buyer_headers, item):
    files = [("files", ("a.png", b"\x89PNG\r\n\x1a\n" + b"0" * 10, "image/png"))]

    response = client.post(f"/api/v1/items/{item['id']}/images", headers=buyer_headers, files=files)

    assert response.status_code == 403
