"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import close_db, init_db
from app.routers import auth, servers
from app.services.ping_service import (
    start_ping_scheduler, 
    stop_ping_scheduler,
    init_http_client,
    close_http_client
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Uptime Monitor...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize HTTP client
    await init_http_client()
    
    # Start ping scheduler
    start_ping_scheduler()
    logger.info("Ping scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Uptime Monitor...")
    
    # Stop ping scheduler
    await stop_ping_scheduler()
    logger.info("Ping scheduler stopped")
    
    # Close HTTP client
    await close_http_client()
    
    # Close database connections
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="Uptime Monitor",
    description="A lightweight uptime monitoring system",
    version="1.0.0",
    lifespan=lifespan
)

# Setup Rate Limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = BASE_DIR / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(servers.router, prefix="/api")


# ============== Page Routes ==============

@app.get("/", response_class=HTMLResponse)
async def public_status_page(request: Request):
    """Serve the public status page."""
    return templates.TemplateResponse("public.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the admin dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page."""
    return templates.TemplateResponse("login.html", {"request": request})


# ============== Health Check ==============

@app.get("/health")
@limiter.exempt
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "uptime-monitor"}


# ============== API Info ==============

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Uptime Monitor API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "servers": "/api/servers"
        }
    }
