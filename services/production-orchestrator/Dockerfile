FROM python:3.9-slim

WORKDIR /app

# Copy shared modules (repo-root relative)
COPY services/shared /app/shared

# Copy orchestrator files into the container
COPY services/production-orchestrator /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Run the orchestrator
CMD ["python", "orchestrator.py"]
