# Development Dockerfile for FastAPI Hello World
# This Dockerfile is optimized for development with hot reload capabilities.
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install Uv (a modern Python package manager)
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync
# this installs all dependencies including dev dependencies from uv.lock
RUN uv sync --frozen

# Copy application code
COPY main.py test_main.py pytest.ini ./

# Expose port 80000
EXPOSE 8000

# Set environment variables for development
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

LABEL NAME="My FastAPI App" \
    VERSION="1.0.0" \
    DESCRIPTION="A sample FastAPI application running in Docker" \
    AUTHOR="Amir Waheed"

# Run with auto-reload for development using UV's run command
# The --host 0.0.0.0 makes it accessible from outsidethe container
# The --reload flag enables hot reloading when code changes
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
