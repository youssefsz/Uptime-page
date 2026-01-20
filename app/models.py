"""Database models for uptime monitoring."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatusEnum(str, PyEnum):
    """Server status enumeration."""
    UP = "UP"
    DOWN = "DOWN"


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"



class Server(Base):
    """Server model for storing monitored servers."""
    
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationship to uptime records
    uptime_records: Mapped[list["UptimeRecord"]] = relationship(
        "UptimeRecord",
        back_populates="server",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Server(id={self.id}, name={self.name}, url={self.url})>"


class UptimeRecord(Base):
    """Uptime record model for storing ping results."""
    
    __tablename__ = "uptime_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum),
        nullable=False
    )
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship to server
    server: Mapped["Server"] = relationship(
        "Server",
        back_populates="uptime_records"
    )

    def __repr__(self) -> str:
        return f"<UptimeRecord(id={self.id}, server_id={self.server_id}, status={self.status})>"
