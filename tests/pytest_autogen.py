import pytest
import json
from httpx import AsyncClient
from fastapi import FastAPI
from app.main import app as main_app


async def test_all_openapi_endpoints(async_client: AsyncClient) -> None:
    """
    Automatically test all API endpoints from OpenAPI schema.
    """

    # Step 1: Get the OpenAPI schema
    resp = await async_client.get("/openapi.json")
    assert resp.status_code == 200, "Failed to fetch OpenAPI schema"
    schema = resp.json()

    # Step 2: Iterate over paths and methods
    for path, methods in schema.get("paths", {}).items():
        for method, details in methods.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue

            # Skip OAuth/token routes from automation to avoid rate limits or login complexity
            if "token" in path or "login" in path:
                continue

            # Build request kwargs
            kwargs = {}
            if method.lower() in ("post", "put", "patch"):
                # Generate example body if schema has requestBody
                req_body = details.get("requestBody", {}).get("content", {}).get(
                    "application/json", {}
                )
                if "example" in req_body:
                    kwargs["json"] = req_body["example"]
                elif "examples" in req_body:
                    first_example = next(iter(req_body["examples"].values()))
                    kwargs["json"] = first_example.get("value", {})
                else:
                    kwargs["json"] = {}  # fallback

            # Step 3: Make request
            url = path.replace("{id}", "1").replace("{user_id}", "1")
            response = await async_client.request(method.upper(), url, **kwargs)

            # Step 4: Basic status code check
            assert response.status_code < 500, (
                f"{method.upper()} {path} failed "
                f"with {response.status_code}: {response.text}"
            )
