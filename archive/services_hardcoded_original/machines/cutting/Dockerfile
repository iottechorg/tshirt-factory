FROM python:3.9-slim

WORKDIR /app

# Copy shared modules
COPY ../../shared /app/shared

# Copy machine-specific files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Run the service
CMD ["python", "machine_service.py"]
