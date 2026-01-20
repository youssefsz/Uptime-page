"""Server CRUD operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Server, StatusEnum, UptimeRecord
from app.schemas import ServerCreate, ServerUpdate, ServerWithStatus


async def get_servers(db: AsyncSession) -> list[Server]:
    """Get all servers ordered by display_order."""
    result = await db.execute(
        select(Server).order_by(Server.display_order.asc(), Server.created_at.desc())
    )
    return list(result.scalars().all())


async def get_server(db: AsyncSession, server_id: int) -> Server | None:
    """Get a server by ID."""
    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    return result.scalar_one_or_none()


async def create_server(db: AsyncSession, server_data: ServerCreate) -> Server:
    """Create a new server."""
    # If no display_order specified, put it at the end
    if server_data.display_order == 0:
        # Get max display_order
        result = await db.execute(
            select(Server).order_by(Server.display_order.desc()).limit(1)
        )
        last_server = result.scalar_one_or_none()
        new_order = (last_server.display_order + 1) if last_server else 0
        server_data_dict = server_data.model_dump()
        server_data_dict['display_order'] = new_order
        server = Server(**server_data_dict)
    else:
        server = Server(**server_data.model_dump())
    db.add(server)
    await db.flush()
    await db.refresh(server)
    return server


async def update_server(
    db: AsyncSession, 
    server_id: int, 
    server_data: ServerUpdate
) -> Server | None:
    """Update a server."""
    server = await get_server(db, server_id)
    
    if not server:
        return None
    
    update_data = server_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(server, field, value)
    
    await db.flush()
    await db.refresh(server)
    return server


async def delete_server(db: AsyncSession, server_id: int) -> bool:
    """Delete a server."""
    server = await get_server(db, server_id)
    
    if not server:
        return False
    
    await db.delete(server)
    await db.flush()
    return True


async def reorder_servers(
    db: AsyncSession, 
    reorder_data: list[dict]
) -> bool:
    """Reorder servers based on provided display_order values."""
    for item in reorder_data:
        server = await get_server(db, item['id'])
        if server:
            server.display_order = item['display_order']
    
    await db.flush()
    return True


async def get_servers_with_status(db: AsyncSession) -> list[ServerWithStatus]:
    """Get all servers with their current status."""
    servers = await get_servers(db)
    result = []
    
    for server in servers:
        # Get the latest uptime record for this server
        latest_record = await db.execute(
            select(UptimeRecord)
            .where(UptimeRecord.server_id == server.id)
            .order_by(desc(UptimeRecord.timestamp))
            .limit(1)
        )
        record = latest_record.scalar_one_or_none()
        
        server_with_status = ServerWithStatus(
            id=server.id,
            name=server.name,
            url=server.url,
            logo_url=server.logo_url,
            display_order=server.display_order,
            created_at=server.created_at,
            current_status=record.status if record else None,
            last_ping=record.timestamp if record else None,
            response_time_ms=record.response_time_ms if record else None
        )
        result.append(server_with_status)
    
    return result


async def get_server_uptime_history(
    db: AsyncSession, 
    server_id: int, 
    hours: int = 24
) -> list[UptimeRecord]:
    """Get uptime history for a server."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    result = await db.execute(
        select(UptimeRecord)
        .where(
            UptimeRecord.server_id == server_id,
            UptimeRecord.timestamp >= since
        )
        .order_by(UptimeRecord.timestamp)
    )
    
    return list(result.scalars().all())


async def get_all_servers_uptime_history(
    db: AsyncSession,
    hours: int = 24
) -> dict[int, list[UptimeRecord]]:
    """Get uptime history for all servers."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    result = await db.execute(
        select(UptimeRecord)
        .where(UptimeRecord.timestamp >= since)
        .order_by(UptimeRecord.timestamp)
    )
    
    records = list(result.scalars().all())
    
    # Group by server_id
    from collections import defaultdict
    history = defaultdict(list)
    for record in records:
        history[record.server_id].append(record)
        
    return history


async def get_server_stats(db: AsyncSession, server_id: int) -> dict:
    """Get statistics for a server."""
    server = await get_server(db, server_id)
    
    if not server:
        return None
    
    # Get all records for this server
    all_records = await db.execute(
        select(UptimeRecord).where(UptimeRecord.server_id == server_id)
    )
    records = list(all_records.scalars().all())
    
    if not records:
        return {
            "server_id": server_id,
            "server_name": server.name,
            "total_checks": 0,
            "uptime_percentage": 0.0,
            "avg_response_time_ms": None,
            "last_24h_uptime": 0.0
        }
    
    # Calculate overall stats
    total_checks = len(records)
    up_checks = sum(1 for r in records if r.status == StatusEnum.UP)
    uptime_percentage = (up_checks / total_checks) * 100 if total_checks > 0 else 0
    
    # Calculate average response time
    response_times = [r.response_time_ms for r in records if r.response_time_ms is not None]
    avg_response_time = sum(response_times) / len(response_times) if response_times else None
    
    # Calculate last 24h uptime
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_records = [r for r in records if r.timestamp >= since_24h]
    recent_up = sum(1 for r in recent_records if r.status == StatusEnum.UP)
    last_24h_uptime = (recent_up / len(recent_records)) * 100 if recent_records else 0
    
    return {
        "server_id": server_id,
        "server_name": server.name,
        "total_checks": total_checks,
        "uptime_percentage": round(uptime_percentage, 2),
        "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else None,
        "last_24h_uptime": round(last_24h_uptime, 2)
    }


async def cleanup_old_records(db: AsyncSession, days: int = 30) -> int:
    """Delete uptime records older than specified days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = await db.execute(
        delete(UptimeRecord).where(UptimeRecord.timestamp < cutoff)
    )
    
    await db.flush()
    return result.rowcount


async def get_uptime_bars(
    db: AsyncSession, 
    server_id: int, 
    days: int = 30
) -> list[dict]:
    """Get aggregated uptime data for bar visualization."""
    from collections import defaultdict
    
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = await db.execute(
        select(UptimeRecord)
        .where(
            UptimeRecord.server_id == server_id,
            UptimeRecord.timestamp >= since
        )
        .order_by(UptimeRecord.timestamp)
    )
    
    records = list(result.scalars().all())
    
    # Group records by day
    daily_data = defaultdict(lambda: {"up": 0, "down": 0, "total": 0})
    
    for record in records:
        day_key = record.timestamp.date()
        daily_data[day_key]["total"] += 1
        if record.status == StatusEnum.UP:
            daily_data[day_key]["up"] += 1
        else:
            daily_data[day_key]["down"] += 1
    
    # Generate bars for each day in the range
    bars = []
    current_date = (datetime.now(timezone.utc) - timedelta(days=days - 1)).date()
    end_date = datetime.now(timezone.utc).date()
    
    while current_date <= end_date:
        if current_date in daily_data:
            data = daily_data[current_date]
            total = data["total"]
            uptime_pct = (data["up"] / total * 100) if total > 0 else 0
            
            # Determine status: up (100%), partial (50-99%), down (<50%), unknown (no data)
            if uptime_pct >= 100:
                status = "up"
            elif uptime_pct >= 50:
                status = "partial"
            elif total > 0:
                status = "down"
            else:
                status = "unknown"
            
            bars.append({
                "date": datetime.combine(current_date, datetime.min.time()),
                "status": status,
                "uptime_percentage": round(uptime_pct, 2),
                "checks": total
            })
        else:
            bars.append({
                "date": datetime.combine(current_date, datetime.min.time()),
                "status": "unknown",
                "uptime_percentage": 0,
                "checks": 0
            })
        
        current_date += timedelta(days=1)
    
    return bars


async def get_servers_with_uptime_bars(
    db: AsyncSession,
    days: int = 30
) -> list[dict]:
    """Get all servers with their uptime bar data."""
    servers = await get_servers(db)
    result = []
    
    for server in servers:
        # Get the latest uptime record for this server
        latest_record = await db.execute(
            select(UptimeRecord)
            .where(UptimeRecord.server_id == server.id)
            .order_by(desc(UptimeRecord.timestamp))
            .limit(1)
        )
        record = latest_record.scalar_one_or_none()
        
        # Get uptime bars
        bars = await get_uptime_bars(db, server.id, days)
        
        # Calculate overall uptime percentage from bars
        total_checks = sum(b["checks"] for b in bars)
        if total_checks > 0:
            weighted_uptime = sum(
                b["uptime_percentage"] * b["checks"] for b in bars
            ) / total_checks
        else:
            weighted_uptime = 0
        
        server_data = {
            "id": server.id,
            "name": server.name,
            "url": server.url,
            "logo_url": server.logo_url,
            "display_order": server.display_order,
            "created_at": server.created_at,
            "current_status": record.status if record else None,
            "last_ping": record.timestamp if record else None,
            "response_time_ms": record.response_time_ms if record else None,
            "uptime_percentage": round(weighted_uptime, 3),
            "uptime_bars": bars
        }
        result.append(server_data)
    
    return result

