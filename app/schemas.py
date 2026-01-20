"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StatusEnum(str, Enum):
    """Server status enumeration."""
    UP = "UP"
    DOWN = "DOWN"


# ============== Token Schemas ==============

class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    username: str | None = None


# ============== Server Schemas ==============

class ServerBase(BaseModel):
    """Base server schema."""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=500)
    logo_url: str | None = Field(None, max_length=500)


class ServerCreate(ServerBase):
    """Schema for creating a new server."""
    display_order: int = Field(0, ge=0)


class ServerUpdate(BaseModel):
    """Schema for updating a server."""
    name: str | None = Field(None, min_length=1, max_length=255)
    url: str | None = Field(None, min_length=1, max_length=500)
    logo_url: str | None = Field(None, max_length=500)


class ServerResponse(ServerBase):
    """Server response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    display_order: int
    created_at: datetime


class ServerReorderItem(BaseModel):
    """Single item for reordering."""
    id: int
    display_order: int


class ServerReorder(BaseModel):
    """Schema for reordering servers."""
    servers: list[ServerReorderItem]


class ServerWithStatus(ServerResponse):
    """Server with current status."""
    current_status: StatusEnum | None = None
    last_ping: datetime | None = None
    response_time_ms: float | None = None


# ============== Uptime Record Schemas ==============

class UptimeRecordBase(BaseModel):
    """Base uptime record schema."""
    status: StatusEnum
    response_time_ms: float | None = None


class UptimeRecordCreate(UptimeRecordBase):
    """Schema for creating an uptime record."""
    server_id: int


class UptimeRecordResponse(UptimeRecordBase):
    """Uptime record response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    server_id: int
    timestamp: datetime


# ============== Statistics Schemas ==============

class ServerStats(BaseModel):
    """Server statistics schema."""
    server_id: int
    server_name: str
    total_checks: int
    uptime_percentage: float
    avg_response_time_ms: float | None
    last_24h_uptime: float


class UptimeHistory(BaseModel):
    """Uptime history for charts."""
    timestamps: list[datetime]
    statuses: list[StatusEnum]
    response_times: list[float | None]


class UptimeBarItem(BaseModel):
    """Single bar item for uptime visualization."""
    date: datetime
    status: str  # "up", "down", "partial", "unknown"
    uptime_percentage: float
    checks: int


class ServerWithUptimeBars(ServerResponse):
    """Server with uptime bar data for visualization."""
    current_status: StatusEnum | None = None
    last_ping: datetime | None = None
    response_time_ms: float | None = None
    uptime_percentage: float = 0.0
    uptime_bars: list[UptimeBarItem] = []


# ============== Login Schema ==============

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str
