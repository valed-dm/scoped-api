async def test_user_registration_and_auth_flow(async_client, db_session):
    # Step 1: Register a new user
    register_payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "NewPass123!",
        "full_name": "New User"
    }
    resp = await async_client.post("/register", json=register_payload)
    assert resp.status_code == 200, f"Registration failed: {resp.text}"
    user_data = resp.json()
    assert user_data["username"] == "newuser"

    # Step 2: Login to get token
    login_payload = {
        "username": "newuser",
        "password": "NewPass123!"
    }
    resp = await async_client.post(
        "/token",
        data=login_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    assert token

    # Step 3: Access a protected endpoint
    resp = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, f"Protected endpoint failed: {resp.text}"
    me_data = resp.json()
    assert me_data["username"] == "newuser"


async def test_admin_access(async_client, admin_token):
    # Try accessing an admin-only endpoint
    resp = await async_client.get(
        "/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # This assumes you have a `/admin/dashboard` route for admins
    assert resp.status_code == 200, f"Admin endpoint failed: {resp.text}"
    data = resp.json()
    assert "stats" in data  # example check
