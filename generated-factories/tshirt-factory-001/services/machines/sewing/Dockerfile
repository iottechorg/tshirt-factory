FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/shared/requirements.txt /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/shared-requirements.txt

# Copy shared module
COPY services/shared /app/shared

# Copy machine code
COPY services/machines/sewing /app/machine

WORKDIR /app/machine

# Run machine service
CMD ["python3", "machine_service.py"]
