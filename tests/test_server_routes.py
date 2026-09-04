"""Regression tests for server mutation routes."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers import servers


@pytest.mark.asyncio
async def test_delete_commits_before_returning(monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful response must only be sent after deletion is committed."""
    db = AsyncMock(spec=AsyncSession)
    delete = AsyncMock(return_value=True)
    monkeypatch.setattr(servers.server_service, "delete_server", delete)

    result = await servers.delete_server(
        server_id=42,
        db=db,
        current_user="admin",
    )

    assert result is None
    delete.assert_awaited_once_with(db, 42)
    db.commit.assert_awaited_once()
