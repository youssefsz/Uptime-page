"""Regression tests for server deletion behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import Delete

from app.models import Server
from app.services.server_service import delete_server


@pytest.mark.asyncio
@pytest.mark.parametrize(("rowcount", "expected"), [(1, True), (0, False)])
async def test_delete_server_uses_one_database_delete(
    rowcount: int,
    expected: bool,
) -> None:
    """Deletion must not materialize a server's full uptime history in Python."""
    db = AsyncMock(spec=AsyncSession)
    db.execute.return_value = MagicMock(rowcount=rowcount)

    deleted = await delete_server(db, server_id=42)

    assert deleted is expected
    statement = db.execute.await_args.args[0]
    assert isinstance(statement, Delete)
    assert statement.table.name == "servers"
    db.delete.assert_not_awaited()
    db.flush.assert_awaited_once()


def test_server_relationship_relies_on_database_cascade() -> None:
    """Future ORM deletes must also avoid loading child history rows."""
    assert Server.uptime_records.property.passive_deletes is True
