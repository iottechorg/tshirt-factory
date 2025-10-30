#!/bin/bash
echo "🏭 Starting Factory: $(basename $(pwd))"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "Building and starting factory services..."
docker compose up --build -d

echo ""
echo "✅ Factory started successfully!"
echo ""
echo "📊 Monitoring:"
echo "   MQTT Messages: mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v"
echo "   Logs: docker compose logs -f"
echo ""
echo "🛑 To stop: docker compose down"
