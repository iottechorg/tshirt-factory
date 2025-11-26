FROM python:3.9-slim

WORKDIR /app

# Copy shared modules (repo-root relative when build context is repo root)
COPY services/shared /app/shared

# Copy machine-specific files into the container
COPY services/machines/cutting /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Run the service
CMD ["python", "machine_service.py"]
