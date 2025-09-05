# tests/test_users.py

import pytest
from httpx import AsyncClient

# --- FIX: Re-enable the asyncio marker for the pytest-asyncio library ---
pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient):
    """
    Tests successful registration of a new user.
    """
    response = await client.post("/users/register", json={
        "email": "testuser@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data

async def test_register_existing_user(client: AsyncClient):
    """
    Tests attempting to register with an email that already exists.
    """
    # First, register a user
    await client.post("/users/register", json={
        "email": "existing@example.com",
        "password": "testpassword123"
    })
    # Then, try again with the same email
    response = await client.post("/users/register", json={
        "email": "existing@example.com",
        "password": "anotherpassword"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

async def test_login_for_access_token(client: AsyncClient):
    """
    Tests successful login and receiving an access token.
    """
    # First, register the user
    email = "loginuser@example.com"
    password = "loginpassword123"
    await client.post("/users/register", json={"email": email, "password": password})

    # Then, log in with the same credentials
    response = await client.post("/users/login", data={"username": email, "password": password})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
