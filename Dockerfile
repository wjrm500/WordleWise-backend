# Use Python 3.11 slim image
FROM python:3.11-slim-bookworm

# Install uv by copying from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy only dependency files first to leverage Docker caching
COPY pyproject.toml uv.lock /app/

# Install dependencies (but not the project) using the lockfile
# This creates a separate layer for dependencies that won't change often
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Now copy the rest of the application
COPY main.py /app/
COPY config/ /app/config/
COPY database/ /app/database/
COPY routes/ /app/routes/
COPY utils/ /app/utils/

# Install the project itself
RUN uv sync --frozen

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Run the application
CMD ["uv", "run", "main.py"]