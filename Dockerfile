# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install the exact dependency versions tested and committed in uv.lock.
# Keeping this layer ahead of the source copy preserves Docker's dependency cache.
COPY pyproject.toml uv.lock README.md ./
RUN pip install --no-cache-dir uv==0.9.26 && \
    uv sync --frozen --no-dev --no-install-project

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
