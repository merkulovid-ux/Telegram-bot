# ---- Build Stage ----
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip poetry

# Copy project files
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-root --no-dev

# ---- Final Stage ----
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Copy installed dependencies from the build stage
COPY --from=builder /app/.venv .venv

# Copy application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

# Change ownership of the app directory
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Default command
CMD ["python", "app.py"]
