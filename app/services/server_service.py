"""Server CRUD operations."""

from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import delete, desc, select, func, case
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


async def _calculate_bars(
    db: AsyncSession,
    server_id: int,
    now: datetime,
    count: int,
    resolution: str = "day"
) -> list[dict]:
    """Helper to calculate bars for a given resolution and count."""
    
    if resolution == "day":
        since = now - timedelta(days=count)
        trunc_interval = "day"
    else:  # hour
        since = now - timedelta(hours=count)
        trunc_interval = "hour"
        
    # SQL Aggregation for performance
    time_bucket = func.date_trunc(trunc_interval, UptimeRecord.timestamp).label("bucket")
    
    stmt = (
        select(
            time_bucket,
            func.count().label("total"),
            func.sum(case((UptimeRecord.status == StatusEnum.UP, 1), else_=0)).label("up_count"),
            func.sum(case((UptimeRecord.status == StatusEnum.DOWN, 1), else_=0)).label("down_count"),
            func.avg(UptimeRecord.response_time_ms).label("avg_latency")
        )
        .where(
            UptimeRecord.server_id == server_id,
            UptimeRecord.timestamp >= since
        )
        .group_by(time_bucket)
        .order_by(time_bucket)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Convert rows to dict for easy lookup
    grouped_data = {}
    for row in rows:
        bucket = row.bucket
        # Ensure we match the key format used in the generation loop
        if isinstance(bucket, datetime):
             if resolution == "day":
                 key = bucket.date()
             else:
                 key = bucket.replace(minute=0, second=0, microsecond=0)
        else:
            # Fallback if driver returns something else (unlikely with asyncpg)
            key = bucket
            
        grouped_data[key] = {
            "total": row.total,
            "up": row.up_count or 0,
            "down": row.down_count or 0,
            "response_time_sum": 0, # Not needed as we have avg
            "response_time_count": 0, # Not needed as we have avg
            "avg_latency": row.avg_latency or 0
        }
            
    bars = []
    
    # Generate points
    if resolution == "day":
        current = (now - timedelta(days=count - 1)).date()
        end = now.date()
    else:
        current = (now - timedelta(hours=count - 1)).replace(minute=0, second=0, microsecond=0)
        end = now.replace(minute=0, second=0, microsecond=0)
        
    loop_count = count
    for i in range(loop_count):
        if resolution == "day":
            key = current
        else:
            key = current
            
        data = grouped_data.get(key, {"total": 0, "up": 0, "down": 0, "avg_latency": 0})
        total = data["total"]
        
        # Calculate uptime percentage
        uptime_pct = (data["up"] / total * 100) if total > 0 else 0
        avg_latency = data["avg_latency"]
        
        # Professional Status Logic:
        # - Up (Green): 100% Up and < 1000ms latency
        # - Degraded (Yellow): 100% Up but >= 1000ms latency
        # - Partial (Orange): 50% - 99.9% Up
        # - Down (Red): < 50% Up
        # - Unknown (Gray): No data
        
        if total == 0:
            status = "unknown"
        elif uptime_pct < 50:
            status = "down"
        elif uptime_pct < 100:
            status = "partial"
        elif avg_latency >= 1000: # Threshold for degraded performance
            status = "degraded"
        else:
            status = "up"
            
        bars.append({
            "date": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc) if resolution == "day" else current,
            "status": status,
            "uptime_percentage": round(uptime_pct, 2),
            "checks": total,
            "avg_response_time_ms": round(avg_latency, 2) if total > 0 else None
        })
        
        if resolution == "day":
            current += timedelta(days=1)
        else:
            current += timedelta(hours=1)
            
    return bars


async def _calculate_bars_bulk(
    db: AsyncSession,
    server_ids: list[int],
    now: datetime,
    count: int,
    resolution: str = "day"
) -> dict[int, list[dict]]:
    """Helper to calculate bars for multiple servers efficiently."""
    
    if not server_ids:
        return {}

    if resolution == "day":
        since = now - timedelta(days=count)
        trunc_interval = "day"
    else:  # hour
        since = now - timedelta(hours=count)
        trunc_interval = "hour"
        
    # SQL Aggregation for performance
    time_bucket = func.date_trunc(trunc_interval, UptimeRecord.timestamp).label("bucket")
    
    stmt = (
        select(
            UptimeRecord.server_id,
            time_bucket,
            func.count().label("total"),
            func.sum(case((UptimeRecord.status == StatusEnum.UP, 1), else_=0)).label("up_count"),
            func.sum(case((UptimeRecord.status == StatusEnum.DOWN, 1), else_=0)).label("down_count"),
            func.avg(UptimeRecord.response_time_ms).label("avg_latency")
        )
        .where(
            UptimeRecord.server_id.in_(server_ids),
            UptimeRecord.timestamp >= since
        )
        .group_by(UptimeRecord.server_id, time_bucket)
        .order_by(UptimeRecord.server_id, time_bucket)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Organize data by server_id -> time_key -> data
    server_groups = defaultdict(dict)
    
    for row in rows:
        bucket = row.bucket
        if isinstance(bucket, datetime):
             if resolution == "day":
                 key = bucket.date()
             else:
                 key = bucket.replace(minute=0, second=0, microsecond=0)
        else:
            key = bucket
            
        server_groups[row.server_id][key] = {
            "total": row.total,
            "up": row.up_count or 0,
            "down": row.down_count or 0,
            "avg_latency": row.avg_latency or 0
        }
            
    # Generate points for all servers
    final_results = {}
    
    if resolution == "day":
        start_current = (now - timedelta(days=count - 1)).date()
    else:
        start_current = (now - timedelta(hours=count - 1)).replace(minute=0, second=0, microsecond=0)
        
    for sid in server_ids:
        bars = []
        if resolution == "day":
            current = start_current
        else:
            current = start_current
            
        server_data = server_groups.get(sid, {})
        
        for _ in range(count):
            if resolution == "day":
                key = current
            else:
                key = current
                
            data = server_data.get(key, {"total": 0, "up": 0, "down": 0, "avg_latency": 0})
            total = data["total"]
            
            # Calculate uptime percentage
            uptime_pct = (data["up"] / total * 100) if total > 0 else 0
            avg_latency = data["avg_latency"]
            
            if total == 0:
                status = "unknown"
            elif uptime_pct < 50:
                status = "down"
            elif uptime_pct < 100:
                status = "partial"
            elif avg_latency >= 1000:
                status = "degraded"
            else:
                status = "up"
                
            bars.append({
                "date": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc) if resolution == "day" else current,
                "status": status,
                "uptime_percentage": round(uptime_pct, 2),
                "checks": total,
                "avg_response_time_ms": round(avg_latency, 2) if total > 0 else None
            })
            
            if resolution == "day":
                current += timedelta(days=1)
            else:
                current += timedelta(hours=1)
        
        final_results[sid] = bars
        
    return final_results


async def get_uptime_bars(
    db: AsyncSession, 
    server: Server,
    requested_days: int = 30
) -> list[dict]:
    """Get aggregated uptime data for bar visualization with dynamic resolution."""
    now = datetime.now(timezone.utc)
    
    # FORCE 24 HOURS ONLY - As explicitly requested
    # We ignore the requested_days and server age
    return await _calculate_bars(db, server.id, now, count=24, resolution="hour")


async def get_servers_with_uptime_bars(
    db: AsyncSession,
    days: int = 30
) -> list[dict]:
    """Get all servers with their uptime bar data."""
    servers = await get_servers(db)
    
    if not servers:
        return []
        
    server_ids = [s.id for s in servers]
    
    # 1. Bulk fetch latest records
    subq = (
        select(
            UptimeRecord.server_id,
            func.max(UptimeRecord.timestamp).label("max_ts")
        )
        .where(UptimeRecord.server_id.in_(server_ids))
        .group_by(UptimeRecord.server_id)
        .subquery()
    )
    
    stmt = (
        select(UptimeRecord)
        .join(
            subq,
            (UptimeRecord.server_id == subq.c.server_id) & 
            (UptimeRecord.timestamp == subq.c.max_ts)
        )
    )
    
    latest_records_result = await db.execute(stmt)
    latest_records = {r.server_id: r for r in latest_records_result.scalars().all()}
    
    # 2. Bulk fetch uptime bars
    # FORCE 24 HOURS ONLY - As explicitly requested (matching previous logic)
    now = datetime.now(timezone.utc)
    bars_map = await _calculate_bars_bulk(db, server_ids, now, count=24, resolution="hour")
    
    result = []
    
    for server in servers:
        record = latest_records.get(server.id)
        bars = bars_map.get(server.id, [])
        
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

