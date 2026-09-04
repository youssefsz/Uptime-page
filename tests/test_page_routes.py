"""Regression tests for server-rendered page routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("path", ["/", "/dashboard", "/login"])
def test_page_route_renders_html(path: str) -> None:
    """Page routes use Starlette's request-first TemplateResponse API."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
