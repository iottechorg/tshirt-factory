# How to Use the Factory Simulation Platform

**Complete guide to defining, generating, and running factory simulations**

---

## Quick Start (5 minutes)

```bash
# 1. Generate a factory from existing config
python3 tools/factory_generator.py factory-configs/tshirt-factory.json

# 2. Start the generated factory
cd generated-factories/tshirt-factory-001
docker compose up --build

# 3. Place an order (from another terminal)
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{"product_type":"tshirt-standard","quantity":5}'

# 4. View telemetry
docker compose logs factory-simulator | grep -i telemetry
```

---

## System Architecture Overview

```
┌─ Configuration Layer (JSON) ──────────────────┐
│ factory-configs/           [Factory definitions]
│ machine-templates/         [Machine specs + sensors]
│ workflows/                 [Production sequences]
│ schemas/                   [JSON validation]
└──────────────────────────────────────────────┘
                      ↓
┌─ Generation Layer (Python) ───────────────────┐
│ tools/factory_generator.py [Code generator]
│ Creates: Docker Compose + Services + Configs
└──────────────────────────────────────────────┘
                      ↓
┌─ Running Factory (Docker) ────────────────────┐
│ generated-factories/{id}/   [Ready-to-run stack]
│ ├─ mosquitto                [MQTT broker]
│ ├─ postgres                 [Data storage]
│ ├─ orchestrator             [Workflow coordinator]
│ ├─ machines/                [Machine simulators]
│ └─ factory_ui_simulator     [REST API + WebSocket]
└──────────────────────────────────────────────┘
                      ↓
┌─ Visualization Layer ─────────────────────────┐
│ Web UI (Angular)           [Order placement + dashboard]
│ MQTT Explorer              [Raw telemetry monitoring]
│ PostgreSQL/Grafana         [Time-series analytics]
└──────────────────────────────────────────────┘
```

---

## Step 1: Choose or Create a Factory Configuration

### Option A: Use Existing Factory

Five pre-built factories are ready to use:

```bash
# T-Shirt Manufacturing
factory-configs/tshirt-factory.json

# Automotive Assembly
factory-configs/automotive-assembly-plant.json

# Electronics Manufacturing
factory-configs/electronics-factory.json

# Pharmaceutical Production
factory-configs/pharmaceutical-plant.json

# Food Processing
factory-configs/food-processing-plant.json
```

### Option B: Create Custom Factory

1. **Copy a template**:
   ```bash
   cp factory-configs/tshirt-factory.json factory-configs/my-factory.json
   ```

2. **Edit factory definition** (see [How to Define a Factory](./FACTORY_DEFINITION_GUIDE.md))

3. **Validate JSON**:
   ```bash
   python3 -c "import json; json.load(open('factory-configs/my-factory.json'))"
   # Should exit silently (no error = valid)
   ```

---

## Step 2: Generate the Factory

```bash
# Generate from existing config
python3 tools/factory_generator.py factory-configs/tshirt-factory.json

# Output appears in:
# generated-factories/tshirt-factory-001/
```

### What Gets Generated

```
generated-factories/tshirt-factory-001/
├── docker-compose.yml           # Services definition
├── machines/                     # Machine simulators
│   ├── cutting/
│   ├── sewing/
│   ├── quality-check/
│   └── packaging/
├── config.json                   # Runtime config
├── test_cases.json              # Auto-generated tests
├── automation_config.json       # Automation sequences
└── README.md                    # Generated documentation
```

---

## Step 3: Start the Factory

```bash
# Navigate to generated factory
cd generated-factories/tshirt-factory-001

# Start all services
docker compose up --build

# Should see output like:
# mosquitto    | mosquitto version 2.0...
# postgres     | ready to accept connections
# orchestrator | Connected to MQTT broker
# machines     | Starting machine simulators...
# factory_ui   | Running on http://0.0.0.0:5000
```

### Verify Services Are Running

```bash
# In another terminal
docker compose ps

# Should show all services with status "Up"
```

---

## Step 4: Place an Order

### Via REST API

```bash
# Place order
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{
    "product_type": "tshirt-standard",
    "quantity": 10,
    "customer": "Acme Corp"
  }'

# Response:
# {"order_id": "ORDER-12345", "status": "processing"}
```

### Check Order Status

```bash
curl http://localhost:5000/production/ORDER-12345
```

---

## Step 5: Monitor Telemetry

### Option 1: Docker Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f orchestrator
docker compose logs -f machines
```

### Option 2: MQTT Direct

```bash
# Subscribe to all telemetry
mosquitto_sub -h localhost -t "factory/+/machines/+/telemetry"

# Subscribe to specific machine
mosquitto_sub -h localhost -t "factory/+/machines/cutting/telemetry"
```

### Option 3: REST API

```bash
# Get current machine statuses
curl http://localhost:5000/machines

# Get telemetry for time range
curl "http://localhost:5000/telemetry/cutting?duration=300s"
```

### Option 4: Query Database

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U factory -d factory_db

# Query telemetry
SELECT timestamp, machine_id, sensor_name, sensor_value 
FROM telemetry 
WHERE machine_id = 'cutting-01' 
ORDER BY timestamp DESC 
LIMIT 20;
```

---

## Monitoring & Troubleshooting

### Check Service Health

```bash
# Verify orchestrator is running
docker compose logs orchestrator | tail -20

# Check MQTT connectivity
docker compose logs machines | head -50

# Check database
docker compose exec postgres psql -U factory -d factory_db -c "SELECT COUNT(*) FROM telemetry;"
```

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| MQTT not connecting | "Connection refused" in logs | Verify mosquitto service is running: `docker compose ps` |
| Database errors | "PostgreSQL connection failed" | Ensure postgres service is healthy: `docker compose logs postgres` |
| No telemetry data | Empty telemetry tables | Check if machines are actually running and publishing |
| Order processing stuck | Order status "processing" indefinitely | Check orchestrator logs for errors |

### Reset and Restart

```bash
# Stop all services
docker compose down

# Remove volumes (CLEARS DATABASE)
docker compose down -v

# Restart fresh
docker compose up --build
```

---

## Testing the Factory

### Run Built-in Test Cases

Test cases are auto-generated during factory generation:

```bash
# View generated test cases
cat generated-factories/tshirt-factory-001/test_cases.json | jq '.[0]'

# Run tests programmatically
python3 << 'EOF'
import json
from shared.test_case_generator import TestCaseGenerator

with open('factory-configs/tshirt-factory.json') as f:
    config = json.load(f)

tcg = TestCaseGenerator(config)
test_cases = tcg.generate_batch_test_cases(count=5)

for tc in test_cases:
    print(f"Test: {tc['name']}")
    print(f"  Steps: {len(tc.get('steps', []))}")
EOF
```

### Simulate Sensor Failures

```bash
# Send extreme sensor values
curl -X POST http://localhost:5000/machines/cutting-01/sensor \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_name": "blade_temperature",
    "value": 100.0,
    "trigger_alarm": true
  }'

# Watch orchestrator respond to failure
docker compose logs orchestrator -f
```

---

## Integration Points

### MQTT Topics Reference

**Machine Status**:
```
factory/{factory_id}/machines/{machine_id}/status
```

**Telemetry**:
```
factory/{factory_id}/machines/{machine_id}/telemetry
```

**Commands**:
```
factory/{factory_id}/machines/{machine_id}/command
```

**Production**:
```
factory/{factory_id}/production/request
factory/{factory_id}/production/complete
```

### REST API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/machines` | GET | List all machines |
| `/machines/{id}` | GET | Get machine details |
| `/machines/{id}/sensor` | POST | Update sensor value |
| `/production` | POST | Place order |
| `/production/{id}` | GET | Get order status |
| `/telemetry/{machine}` | GET | Get telemetry data |
| `/health` | GET | Health check |

---

## Advanced Usage

### Custom Automation Sequences

```bash
# Automation config is generated automatically
cat generated-factories/tshirt-factory-001/automation_config.json

# Edit sequences and restart
docker compose restart orchestrator
```

### Run Specific Workflows

```bash
# List available workflows
curl http://localhost:5000/workflows

# Run specific workflow
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": "premium-tshirt",
    "quantity": 5
  }'
```

### Scale Machines

```bash
# Add more instances in docker-compose.yml
# Example: 2 cutting machines instead of 1

# Regenerate to update config
python3 tools/factory_generator.py factory-configs/tshirt-factory.json
```

---

## Performance Tuning

### For High-Volume Simulation

1. **Increase MQTT buffer**:
   ```yaml
   # In docker-compose.yml
   mosquitto:
     command: mosquitto -c /mosquitto/config/mosquitto.conf -p 1883 -m
   ```

2. **Enable PostgreSQL indexes**:
   ```sql
   CREATE INDEX idx_telemetry_machine ON telemetry(machine_id, timestamp);
   ```

3. **Configure retention**:
   ```sql
   DELETE FROM telemetry WHERE timestamp < NOW() - INTERVAL '7 days';
   ```

---

## Cleanup

### Stop Running Factory

```bash
cd generated-factories/tshirt-factory-001
docker compose down
```

### Remove Generated Factory

```bash
rm -rf generated-factories/tshirt-factory-001
```

### Clean Docker Resources

```bash
docker compose down -v              # Remove volumes
docker image prune -a              # Remove unused images
docker system prune                # Full cleanup
```

---

## Next Steps

- [How to Define a Factory](./FACTORY_DEFINITION_GUIDE.md) - Create custom factories
- [Creating New Factories](./CREATE_NEW_FACTORY.md) - Step-by-step guide with examples
- [Machine Templates](../machine-templates/) - Explore available machine types
- [Architecture Documentation](./ARCHITECTURE.md) - Deep dive into system design

---

## Support & Troubleshooting

### Enable Debug Logging

```bash
# Set LOG_LEVEL for services
docker compose environment:
  LOG_LEVEL: DEBUG

# View with:
docker compose logs -f orchestrator | grep DEBUG
```

### View Generation Output

```bash
# Re-run generator with verbose output
python3 tools/factory_generator.py \
  factory-configs/tshirt-factory.json \
  --verbose
```

### Validate Generated Factory

```bash
cd generated-factories/tshirt-factory-001

# Check docker-compose validity
docker-compose config

# Verify JSON configs
python3 -m json.tool config.json > /dev/null
python3 -m json.tool test_cases.json > /dev/null
```

---

**Questions?** Check [Architecture Documentation](./ARCHITECTURE.md) or review [example factory configs](../factory-configs/).
