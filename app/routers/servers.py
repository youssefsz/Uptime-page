"""Server management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.schemas import (
    ServerCreate,
    ServerReorder,
    ServerResponse,
    ServerUpdate,
    ServerWithStatus,
    ServerWithUptimeBars,
    UptimeRecordResponse,
)
from app.services import server_service
from app.services.ping_service import ping_server_now

router = APIRouter(prefix="/servers", tags=["Servers"])


# ============== Protected Routes (Require Auth) ==============

@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[str, Depends(get_current_user)]
) -> ServerResponse:
    """Create a new server to monitor (requires authentication)."""
    server = await server_service.create_server(db, server_data)
    return server


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[str, Depends(get_current_user)]
) -> ServerResponse:
    """Update a server (requires authentication)."""
    server = await server_service.update_server(db, server_id, server_data)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[str, Depends(get_current_user)]
) -> None:
    """Delete a server (requires authentication)."""
    deleted = await server_service.delete_server(db, server_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )


@router.post("/reorder", status_code=status.HTTP_200_OK)
async def reorder_servers(
    reorder_data: ServerReorder,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[str, Depends(get_current_user)]
) -> dict:
    """Reorder servers (requires authentication)."""
    await server_service.reorder_servers(
        db, 
        [item.model_dump() for item in reorder_data.servers]
    )
    return {"message": "Servers reordered successfully"}


@router.post("/{server_id}/ping", response_model=UptimeRecordResponse)
async def ping_server_manually(
    server_id: int,
    current_user: Annotated[str, Depends(get_current_user)]
) -> UptimeRecordResponse:
    """Manually ping a server (requires authentication)."""
    record = await ping_server_now(server_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return record


# ============== Public Routes ==============

@router.get("", response_model=list[ServerWithStatus])
async def get_all_servers(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> list[ServerWithStatus]:
    """Get all servers with their current status (public)."""
    return await server_service.get_servers_with_status(db)


@router.get("/with-bars", response_model=list[ServerWithUptimeBars])
async def get_servers_with_uptime_bars(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 1
) -> list[ServerWithUptimeBars]:
    """Get all servers with uptime bar visualization data (public)."""
    return await server_service.get_servers_with_uptime_bars(db, days)


@router.get("/{server_id}", response_model=ServerWithStatus)
async def get_server(
    server_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ServerWithStatus:
    """Get a specific server with its current status (public)."""
    servers = await server_service.get_servers_with_status(db)
    
    for server in servers:
        if server.id == server_id:
            return server
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Server not found"
    )


@router.get("/{server_id}/history", response_model=list[UptimeRecordResponse])
async def get_server_history(
    server_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    hours: int = 24
) -> list[UptimeRecordResponse]:
    """Get uptime history for a server (public)."""
    # Verify server exists
    server = await server_service.get_server(db, server_id)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    records = await server_service.get_server_uptime_history(db, server_id, hours)
    return records


@router.get("/history/all", response_model=dict[int, list[UptimeRecordResponse]])
async def get_all_server_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    hours: int = 24
) -> dict[int, list[UptimeRecordResponse]]:
    """Get uptime history for all servers (public)."""
    return await server_service.get_all_servers_uptime_history(db, hours)


@router.get("/{server_id}/stats")
async def get_server_stats(
    server_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Get statistics for a server (public)."""
    stats = await server_service.get_server_stats(db, server_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return stats
