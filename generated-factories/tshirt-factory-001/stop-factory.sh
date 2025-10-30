#!/bin/bash
echo "🛑 Stopping Factory: $(basename $(pwd))"
docker compose down
echo "✅ Factory stopped"
