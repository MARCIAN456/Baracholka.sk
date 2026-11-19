import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.models.user import User

def test_register_creates_user(client):

    body = {"name": "Anna Test", "email": "anna@example.com", "password": "password123", "city": "Kosice"}


    response = client.post("/api/v1/auth/register", json=body)


    assert response.status_code == 201
    assert response.json()["email"] == "anna@example.com"
    assert "password" not in response.json()

def test_register_with_the_same_email(client):
    body = {"name": "Anna Test", "email": "anna@example.com", "password": "password123", "city": "Kosice"}

    client.post("/api/v1/auth/register", json=body)
    response = client.post("/api/v1/auth/register", json=body)

    assert response.status_code == 400

def test_register_with_small_password(client, db):
    body = {"name": "Mark Test", "email": "anna@example.com", "password": "pas", "city": "Kosice"}

    response = client.post("/api/v1/auth/register", json=body)

    assert response.status_code == 422
    assert db.query(User).count() == 0

def test_login(client, buyer_headers):
    response = client.post("/api/v1/auth/login", data={"username": "buyer@example.com", "password": "password123"})

    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_with_bad_password_email(client):
    client.post("/api/v1/auth/register", json={
        "name": "Anna Test", "email": "anna@example.com", "password": "password123", "city": "Kosice",
    })

    response_bad_email = client.post("/api/v1/auth/login", data={
        "username": "nobody@example.com", "password": "password123",
    })
    response_bad_password = client.post("/api/v1/auth/login", data={
        "username": "anna@example.com", "password": "wrong-password",
    })

    assert response_bad_email.status_code == 401
    assert response_bad_password.status_code == 401
    assert response_bad_email.json() == response_bad_password.json()

def test_page_me_with_other_signed_secret(client):
    fake = jwt.encode({"sub": "123", "role": "ADMIN"}, "hacker-secret", algorithm="HS256")
    response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {fake}"})

    assert response.status_code == 401

def test_me_with_fake_token(client):
    response = client.get("/api/v1/user/me", headers={"Authorization": "Bearer abc.def.ghi"})

    assert response.status_code == 401

def test_me_without_token(client):
    response = client.get("/api/v1/user/me")

    assert response.status_code == 401

def test_me_returns_profile(client, buyer_headers):
    response = client.get("/api/v1/user/me", headers=buyer_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "buyer@example.com"







def make_token(sub, minutes=5):
    payload = {"sub": sub, "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def test_token_with_non_uuid_sub_returns_401(client):
    token = make_token("not-a-uuid")

    response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_expired_token_returns_401(client, buyer_headers):
    user_id = client.get("/api/v1/user/me", headers=buyer_headers).json()["id"]
    token = make_token(user_id, minutes=-1)

    response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_token_for_unknown_user_returns_401(client):
    token = make_token(str(uuid.uuid4()))

    response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_login_error_is_same_for_unknown_email_and_wrong_password(client, buyer_headers):
    wrong_password = client.post("/api/v1/auth/login", data={"username": "buyer@example.com", "password": "wrongpass1"})
    unknown_email = client.post("/api/v1/auth/login", data={"username": "nobody@example.com", "password": "wrongpass1"})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
