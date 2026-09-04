"""Local development entry point."""

import uvicorn

from app.config import get_settings


def main() -> None:
    """Run the application using the configured host and port."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
