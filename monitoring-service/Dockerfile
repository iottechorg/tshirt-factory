FROM python:3.11-slim

WORKDIR /app

# Copy shared modules
COPY ../shared /app/shared

# Copy orchestrator files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Run the service
CMD ["python", "monitoring.py"]
