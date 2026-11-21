import os

os.environ.update({
    "DATABASE_URL": "sqlite://",
    "SECRET_KEY": "test-secret-key-that-is-at-least-32-bytes-long",
    "STRIPE_SECRET_KEY": "sk_test_fake",
    "STRIPE_WEBHOOK_SECRET": "whsec_fake",
    "CLOUDINARY_CLOUD_NAME": "fake",
    "CLOUDINARY_API_KEY": "fake",
    "CLOUDINARY_API_SECRET": "fake",
    "PACKETA_WEBHOOK_SECRET": "packeta-test-secret",
    "ADMIN_SECRET_KEY": "admin-test-secret-key-that-is-long-enough",
})

from types import SimpleNamespace

import pytest
import stripe
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.core.limiter import limiter
from app.models.base import Base
from app.models import user, item, image, delivery, payments  # noqa
from tests.helpers import register_and_login, create_item, accept_item, create_delivery, checkout, send_stripe_event

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

limiter.enabled = False


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(db):
    from app.admin.main import create_admin_app
    return TestClient(create_admin_app(TestingSession))


@pytest.fixture
def buyer_headers(client):
    return register_and_login(client, "buyer@example.com")


@pytest.fixture
def other_buyer_headers(client):
    return register_and_login(client, "buyer2@example.com")


@pytest.fixture
def seller_headers(client):
    headers = register_and_login(client, "seller@example.com")
    client.patch("/api/v1/user/me/iban", headers=headers, json={"iban": "SK8975000000000012345671"})
    return headers


@pytest.fixture
def item(client, db, seller_headers):
    created = create_item(client, seller_headers)
    accept_item(db, created["id"])
    return created


@pytest.fixture
def draft_delivery(client, buyer_headers, item):
    return create_delivery(client, buyer_headers, item["id"])


@pytest.fixture
def fake_stripe(monkeypatch):
    state = SimpleNamespace(created=[], expired=[], refunds=[], retrieve_status="open", refund_error=None)

    def create(**kwargs):
        state.created.append(kwargs)
        n = len(state.created)
        return SimpleNamespace(id=f"cs_test_{n}", url=f"https://checkout.test/{n}")

    def retrieve(session_id):
        return SimpleNamespace(id=session_id, status=state.retrieve_status, payment_intent="pi_test")

    def expire(session_id):
        state.expired.append(session_id)

    def refund(**kwargs):
        if state.refund_error:
            raise state.refund_error
        state.refunds.append(kwargs)

    monkeypatch.setattr(stripe.checkout.Session, "create", create)
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", retrieve)
    monkeypatch.setattr(stripe.checkout.Session, "expire", expire)
    monkeypatch.setattr(stripe.Refund, "create", refund)
    return state


@pytest.fixture
def paid_order(client, monkeypatch, fake_stripe, buyer_headers, item, draft_delivery):
    session_id = checkout(client, buyer_headers, item["id"]).json()["session_id"]
    send_stripe_event(client, monkeypatch, "checkout.session.completed", session_id)
    delivery = client.get(f"/api/v1/delivery/{draft_delivery['id']}", headers=buyer_headers).json()
    return SimpleNamespace(item=item, delivery=delivery, session_id=session_id)
