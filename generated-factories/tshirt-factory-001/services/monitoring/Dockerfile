FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/shared/requirements.txt /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/shared-requirements.txt

# Copy shared module
COPY services/shared /app/shared

# Copy monitoring code
COPY services/monitoring /app/monitoring

WORKDIR /app/monitoring

# Run monitoring service
CMD ["python3", "monitoring_service.py"]
