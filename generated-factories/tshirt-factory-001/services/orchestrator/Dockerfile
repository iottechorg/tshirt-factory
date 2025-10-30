FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/shared/requirements.txt /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/shared-requirements.txt

# Copy shared module
COPY services/shared /app/shared

# Copy orchestrator code
COPY services/orchestrator /app/orchestrator

WORKDIR /app/orchestrator

# Run orchestrator
CMD ["python3", "orchestrator.py"]
