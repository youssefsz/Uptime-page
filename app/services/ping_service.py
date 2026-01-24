"""Ping service for monitoring server uptime."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session_maker
from app.models import Server, StatusEnum, UptimeRecord
from app.services.server_service import get_servers

settings = get_settings()
logger = logging.getLogger(__name__)

# Global flag to control the ping loop
_ping_task: asyncio.Task | None = None
_running = False
_http_client: httpx.AsyncClient | None = None


async def init_http_client() -> None:
    """Initialize the global HTTP client."""
    global _http_client
    if _http_client is None:
        # Increase limits for better concurrency handling
        limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
        _http_client = httpx.AsyncClient(
            limits=limits,
            timeout=settings.ping_timeout_seconds,
            follow_redirects=True
        )
        logger.info("Global HTTP client initialized")


async def close_http_client() -> None:
    """Close the global HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
        logger.info("Global HTTP client closed")


async def ping_server(url: str, timeout: int = 10) -> tuple[StatusEnum, float | None]:
    """
    Ping a server and return its status and response time.
    
    Args:
        url: The URL to ping
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (status, response_time_ms)
    """
    global _http_client
    
    # Ensure client is initialized
    if _http_client is None:
        await init_http_client()
        
    try:
        start_time = time.perf_counter()
        
        # Use the persistent client
        # Note: We pass timeout here to override client default if needed, 
        # though usually it matches settings.ping_timeout_seconds
        response = await _http_client.get(url, timeout=timeout)
            
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        
        # Consider 2xx and 3xx as UP
        if response.status_code < 400:
            return StatusEnum.UP, round(response_time_ms, 2)
        else:
            logger.warning(f"Server {url} returned status {response.status_code}")
            return StatusEnum.DOWN, round(response_time_ms, 2)
                
    except httpx.TimeoutException:
        logger.warning(f"Server {url} timed out")
        return StatusEnum.DOWN, None
    except httpx.RequestError as e:
        logger.warning(f"Server {url} request error: {e}")
        return StatusEnum.DOWN, None
    except Exception as e:
        logger.error(f"Unexpected error pinging {url}: {e}")
        return StatusEnum.DOWN, None


async def ping_all_servers() -> None:
    """Ping all servers and store results."""
    async with async_session_maker() as db:
        try:
            servers = await get_servers(db)
            
            if not servers:
                logger.debug("No servers to ping")
                return
            
            # Use a semaphore to limit concurrent pings to avoid saturating resources on VPS
            # This helps smooth out the "spiky" latency behavior
            sem = asyncio.Semaphore(10)
            
            async def bounded_ping(server: Server):
                async with sem:
                    await ping_and_record(db, server)
            
            # Ping all servers concurrently with limited concurrency
            tasks = []
            for server in servers:
                tasks.append(bounded_ping(server))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await db.commit()
            
            logger.info(f"Pinged {len(servers)} servers")
            
        except Exception as e:
            logger.error(f"Error in ping_all_servers: {e}")
            await db.rollback()


async def ping_and_record(db: AsyncSession, server: Server) -> None:
    """Ping a single server and record the result."""
    try:
        status, response_time = await ping_server(
            server.url, 
            timeout=settings.ping_timeout_seconds
        )
        
        record = UptimeRecord(
            server_id=server.id,
            status=status,
            response_time_ms=response_time
        )
        
        db.add(record)
        logger.debug(f"Server {server.name}: {status.value} ({response_time}ms)")
        
    except Exception as e:
        logger.error(f"Error recording ping for {server.name}: {e}")
        
        # Still record as DOWN if we couldn't ping
        record = UptimeRecord(
            server_id=server.id,
            status=StatusEnum.DOWN,
            response_time_ms=None
        )
        db.add(record)


async def ping_loop() -> None:
    """Main ping loop that runs continuously."""
    global _running
    
    logger.info(f"Starting ping loop with interval of {settings.ping_interval_seconds}s")
    
    while _running:
        try:
            await ping_all_servers()
        except Exception as e:
            logger.error(f"Error in ping loop: {e}")
        
        # Wait for the configured interval
        await asyncio.sleep(settings.ping_interval_seconds)


def start_ping_scheduler() -> None:
    """Start the background ping scheduler."""
    global _ping_task, _running
    
    if _ping_task is not None and not _ping_task.done():
        logger.warning("Ping scheduler already running")
        return
    
    _running = True
    _ping_task = asyncio.create_task(ping_loop())
    logger.info("Ping scheduler started")


async def stop_ping_scheduler() -> None:
    """Stop the background ping scheduler."""
    global _ping_task, _running
    
    _running = False
    
    if _ping_task is not None:
        _ping_task.cancel()
        try:
            await _ping_task
        except asyncio.CancelledError:
            pass
        _ping_task = None
        
    logger.info("Ping scheduler stopped")


async def ping_server_now(server_id: int) -> UptimeRecord | None:
    """Manually ping a specific server immediately."""
    async with async_session_maker() as db:
        from app.services.server_service import get_server
        
        server = await get_server(db, server_id)
        
        if not server:
            return None
        
        status, response_time = await ping_server(
            server.url,
            timeout=settings.ping_timeout_seconds
        )
        
        record = UptimeRecord(
            server_id=server.id,
            status=status,
            response_time_ms=response_time
        )
        
        db.add(record)
        await db.commit()
        await db.refresh(record)
        
        return record
