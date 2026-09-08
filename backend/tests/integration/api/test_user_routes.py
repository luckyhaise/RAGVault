from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.security import decode_access_token

CREATE_URL = "/api/v1/user/create"
LOGIN_URL = "/api/v1/user/login"


def _unique_user(**overrides) -> dict:
    suffix = uuid4().hex[:8]
    user = {
        "user_name": f"route_user_{suffix}",
        "phone": f"+1{uuid4().int % 10**10:010d}",
        "email": f"route_{suffix}@example.com",
        "name": "Route Tester",
        "password": "Route@pass1",
    }
    user.update(overrides)
    return user


@pytest.mark.asyncio
async def test_create_account_happy_path(client: AsyncClient):
    payload = _unique_user()
    response = await client.post(CREATE_URL, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"id", "email", "name"}
    assert body["email"] == payload["email"]
    assert body["name"] == payload["name"]
    assert body["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short"},
        {"password": "nouppercase1@"},
        {"phone": "9999999999"},
        {"user_name": "ab"},
        {"email": "not-an-email"},
    ],
)
async def test_create_account_rejects_invalid_body(client: AsyncClient, overrides: dict):
    payload = _unique_user(**overrides)
    response = await client.post(CREATE_URL, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_create_account_rejects_duplicate_email(client: AsyncClient):
    first = _unique_user()
    assert (await client.post(CREATE_URL, json=first)).status_code == 200

    duplicate = _unique_user(email=first["email"])
    response = await client.post(CREATE_URL, json=duplicate)

    assert response.status_code == 409
    assert response.json()["error"]["error_code"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_account_rejects_duplicate_phone(client: AsyncClient):
    first = _unique_user()
    assert (await client.post(CREATE_URL, json=first)).status_code == 200

    duplicate = _unique_user(phone=first["phone"])
    response = await client.post(CREATE_URL, json=duplicate)

    assert response.status_code == 409
    assert response.json()["error"]["error_code"] == "PHONE_NUMBER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_account_rejects_duplicate_username(client: AsyncClient):
    first = _unique_user()
    assert (await client.post(CREATE_URL, json=first)).status_code == 200

    duplicate = _unique_user(user_name=first["user_name"])
    response = await client.post(CREATE_URL, json=duplicate)

    assert response.status_code == 409
    assert response.json()["error"]["error_code"] == "USERNAME_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_login_with_username_returns_usable_token(client: AsyncClient):
    user = _unique_user()
    created = await client.post(CREATE_URL, json=user)
    assert created.status_code == 200
    user_id = created.json()["id"]

    response = await client.post(
        LOGIN_URL,
        json={"user_name": user["user_name"], "password": user["password"]},
    )

    assert response.status_code == 200
    token = response.json()
    assert isinstance(token, str)
    assert decode_access_token(token) == user_id


@pytest.mark.asyncio
async def test_login_with_email_returns_usable_token(client: AsyncClient):
    user = _unique_user()
    created = await client.post(CREATE_URL, json=user)
    assert created.status_code == 200
    user_id = created.json()["id"]

    response = await client.post(
        LOGIN_URL,
        json={"email": user["email"], "password": user["password"]},
    )

    assert response.status_code == 200
    token = response.json()
    assert isinstance(token, str)
    assert decode_access_token(token) == user_id


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client: AsyncClient):
    user = _unique_user()
    assert (await client.post(CREATE_URL, json=user)).status_code == 200

    response = await client.post(
        LOGIN_URL,
        json={"user_name": user["user_name"], "password": "Wrong@pass1"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_rejects_unknown_user(client: AsyncClient):
    response = await client.post(
        LOGIN_URL,
        json={"user_name": f"missing_{uuid4().hex[:8]}", "password": "Route@pass1"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"password": "Route@pass1"},
        {
            "user_name": "someone",
            "email": "someone@example.com",
            "password": "Route@pass1",
        },
    ],
)
async def test_login_rejects_invalid_body(client: AsyncClient, payload: dict):
    response = await client.post(LOGIN_URL, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
