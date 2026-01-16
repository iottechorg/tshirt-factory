# System Architecture

***
Consolidated Architecture (Canonical)
===================================

This file is the canonical architecture reference. It consolidates the previous UI-focused and template-driven architecture notes into a single source of truth. Original, unmerged files have been archived under `docs/archive/`.

Overview
--------

The platform has three layers:

- Configuration layer: `factory-configs/`, `machine-templates/`, `workflows/`.
- Generation layer: `tools/factory_generator.py` (canonical generator: `shared/template_driven_test_generator.py`).
- Execution layer: generated Docker Compose stacks per factory instance.

Core Components
---------------

- MQTT Broker (Mosquitto): message bus (1883, WS 9001).
- Orchestrator: subscribes to production requests and issues machine commands via MQTT.
- Machine services: per-machine containers publishing telemetry and accepting commands.
- Monitoring service: subscribes to telemetry and writes to PostgreSQL/TimescaleDB.
- Factory UI Simulator: stateless REST → MQTT bridge used by browser UIs.

Standard MQTT Topics
---------------------

```
factory/{factory-id}/machines/{machine-id}/telemetry
factory/{factory-id}/machines/{machine-id}/status
factory/{factory-id}/machines/{machine-id}/command
factory/{factory-id}/production/request
factory/{factory-id}/production/status
factory/{factory-id}/sensor/update
factory/{factory-id}/test/request
```

Generator & Test Case Notes
---------------------------

- Canonical generator: `shared/template_driven_test_generator.py`. It extracts sensor ranges and metadata from `machine-templates/*.json` and generates `test_cases.json` containing sensor-extreme and production scenarios.
- Legacy generators (e.g., `shared/test_case_generator.py`) are deprecated and archived. The canonical implementation is `shared/template_driven_test_generator.py`.

UI Simulator (MQTT bridge)
-------------------------

The Factory UI Simulator is a stateless REST → MQTT bridge. It translates browser actions into MQTT topics and reflects factory state received over MQTT. The simulator does not implement machine simulation; generated factories provide simulation logic and publish status/telemetry to MQTT.

Key behaviors:
- Forwards production requests, sensor updates and test requests to `factory/{factory_id}/...` topics.
- Subscribes to factory topics to maintain UI state and provide REST responses.

Template-driven Test Generation
------------------------------

Test cases and automation are generated from `machine-templates/*.json` and `factory-configs/*.json`. The canonical generator (`shared/template_driven_test_generator.py`) extracts sensor ranges and produces `test_cases.json` containing sensor-extreme and production scenarios. This makes tests factory-agnostic and automatically covers newly added sensors or machine templates.

Factory UI Simulator
--------------------

The simulator exposes REST endpoints that translate to MQTT topics and maintains a small in-memory state derived from MQTT subscriptions. It does not simulate machines locally; generated factories provide simulation logic.

Common REST endpoints:

- `GET /machines`
- `PUT /machines/<id>/sensor/<name>`
- `POST /production`
- `POST /test/run/<name>`

Networking Considerations
-------------------------

- Generated factories are Docker Compose stacks. For cross-stack access the supported approaches are:
  - Publish ports to host and use `host.docker.internal` (macOS) from UI containers.
  - Attach UI/service containers to one or more factory networks (service joins multiple networks).
  - Run an `edge-proxy` container that joins multiple networks and proxies HTTP/WS/MQTT.

Migration & Next Steps
---------------------

- One-off scripts will be moved into `tests/` (pytest) or archived.
- Placeholders were added for missing guides under `docs/` so links are resolvable; full guide content should be authored and linked here.

See also
--------

- `docs/HOW_TO_USE.md`
- `docs/EXTENDING.md`
- `docs/MEDIUM_ARTICLE.md`

  ↓
Initialize sensors (random within ranges)
  ↓
Loop:
  ├─ Every 2s: Update sensor values
  ├─ Every 5s: Publish telemetry to MQTT
  ├─ Listen for commands on machines/{machine-id}/command
  └─ Execute commands (start operation, stop, etc.)
```

**MQTT Publish Pattern**:
```python
# Every 5 seconds
publish(f"factory/{factory_id}/machines/{machine_id}/status", {
    "machine_id": machine_id,
    "runtime_state": "idle|busy|error",
    "total_operations": 5,
    "failed_operations": 0,
    "is_running": true
})

publish(f"factory/{factory_id}/machines/{machine_id}/telemetry", {
    "machine_id": machine_id,
    "sensor_data": {
        "blade_temperature": 35.2,
        "blade_pressure": 1.8,
        "cut_speed": 0.95
    },
    "runtime_state": "busy",
    "timestamp": 1700000000
})
```

### 3. Orchestrator Service

**Role**: Coordinates production workflows

**Responsibilities**:
1. Subscribe to production requests
2. Create workflow instances from templates
3. Send machine commands via MQTT
4. Track workflow progress
5. Update status in PostgreSQL

**Workflow Execution**:
```
Production Request: "cut 100 shirts"
  ↓
Load workflow template: tshirt-standard.json
  ↓
Create workflow instance with parameters
  ↓
For each step in workflow:
  ├─ Send START command to machine
  ├─ Wait for status READY or COMPLETE
  ├─ Record timestamps
  └─ Move to next step
  ↓
Mark production as COMPLETE
```

**Commands Sent**:
```json
Topic: factory/{factory_id}/machines/{machine_id}/command
Message: {
    "command": "start|stop|set_failure_rate",
    "parameters": { "operation": "cut_fabric", "duration": 20 }
}
```

### 4. Monitoring Service

**Role**: Listens to all machines and persists data

**Responsibilities**:
1. Subscribe to ALL machine telemetry
2. Store data in PostgreSQL & TimescaleDB
3. Monitor for machine errors
4. Provide health check endpoint

**Wildcard Subscription**:
```python
mqtt_client.subscribe("factory/tshirt-factory-001/machines/+/+", callback)
# Matches both:
# - factory/tshirt-factory-001/machines/cutting-01/status
# - factory/tshirt-factory-001/machines/cutting-01/telemetry
```

**Data Persistence**:
```sql
-- PostgreSQL
INSERT INTO machine_status_log (machine_id, runtime_state, total_operations)
VALUES ('cutting-01', 'busy', 5);

-- TimescaleDB (time-series)
INSERT INTO sensor_telemetry (machine_id, sensor_name, sensor_value, time)
VALUES ('cutting-01', 'blade_temperature', 35.2, NOW());
```

### 5. PostgreSQL Database

**Purpose**: Transactional data for production orders, machine state

**Schema**:
```sql
-- Production orders
CREATE TABLE production_orders (
    order_id SERIAL PRIMARY KEY,
    factory_id VARCHAR(100),
    product_type VARCHAR(100),
    quantity INT,
    parameters JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Machine status history
CREATE TABLE machine_status_log (
    log_id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100),
    runtime_state VARCHAR(50),
    total_operations INT,
    failed_operations INT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Telemetry data
CREATE TABLE machine_telemetry (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100),
    machine_type VARCHAR(100),
    sensor_data JSONB,
    runtime_state VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6. TimescaleDB

**Purpose**: Time-series data for sensor metrics and analytics

**Hypertable**:
```sql
CREATE TABLE sensor_data (
    machine_id VARCHAR(100),
    machine_type VARCHAR(100),
    sensor_name VARCHAR(100),
    sensor_value FLOAT,
    runtime_state VARCHAR(50),
    time TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (machine_id, time)
);

SELECT create_hypertable('sensor_data', 'time');
```

**Queries**:
```sql
-- Average temperature over 1 minute
SELECT
    machine_id,
    time_bucket('1 minute', time) as bucket,
    AVG(sensor_value) as avg_temp
FROM sensor_data
WHERE sensor_name = 'blade_temperature' AND machine_id = 'cutting-01'
GROUP BY machine_id, bucket
ORDER BY bucket DESC;
```

---

## Data Flow

### 1. Production Order Flow

```
┌─ Customer Places Order ─────────────────────┐
│                                             │
│  Frontend (tshirt-customizer)              │
│  POST /production                          │
│  {"size": "M", "color": "blue", ...}       │
│                                             │
└──────────────┬──────────────────────────────┘
               │ HTTP
               ▼
┌─ API Gateway (simple_factory_simulator) ──┐
│                                            │
│  app.py: @app.route('/production')        │
│  ├─ Create order in PostgreSQL            │
│  └─ Publish to MQTT                       │
│     factory/{factory_id}/production/      │
│     request                                │
│                                            │
└──────────────┬───────────────────────────────┘
               │ MQTT
               ▼
┌─ MQTT Broker ──────────────────────────────┐
│                                            │
│  Topic: factory/.../production/request    │
│                                            │
└──────────────┬───────────────────────────────┘
               │ MQTT
               ▼
┌─ Orchestrator ─────────────────────────────┐
│                                            │
│  Subscribes to production/request         │
│  ├─ Parse order details                   │
│  ├─ Load workflow template                │
│  └─ Publish start command to machine      │
│     factory/.../machines/cutting-01/      │
│     command                                │
│                                            │
└──────────────┬───────────────────────────────┘
               │ MQTT
               ▼
┌─ Machine: Cutting-01 ──────────────────────┐
│                                            │
│  Receives command START                   │
│  ├─ Update state: BUSY                    │
│  ├─ Execute operation (20 seconds)        │
│  ├─ Publish telemetry every 5s            │
│  └─ Publish COMPLETE status               │
│     factory/.../machines/cutting-01/      │
│     status                                 │
│                                            │
└──────────────┬───────────────────────────────┘
               │ MQTT
               ▼
┌─ Monitoring Service ───────────────────────┐
│                                            │
│  Receives all machine statuses            │
│  ├─ Store in PostgreSQL                   │
│  ├─ Store telemetry in TimescaleDB        │
│  └─ Alert on errors                       │
│                                            │
└────────────────────────────────────────────┘
```

### 2. Real-Time Telemetry Flow

```
Machine Services (Every 5 seconds)
    │
    ├─ Update sensor values (simulated)
    ├─ Calculate current state
    └─ Publish to MQTT
        │
        ├─ factory/{factory_id}/machines/cutting-01/status
        └─ factory/{factory_id}/machines/cutting-01/telemetry
            │
            ├─ MQTT Broker
            │   │
            │   ├─ Monitoring Service
            │   │   └─ Store in PostgreSQL/TimescaleDB
            │   │
            │   ├─ API Gateway
            │   │   └─ WebSocket to Browsers
            │   │
            │   └─ Orchestrator
            │       └─ Check for error states
            │
            └─ Frontend (WebSocket)
                └─ Real-time dashboard update
```

---

## Service Communication

### MQTT Topics Structure (ISA-95 Compliant)

```
factory/{factory-id}/
│
├─ machines/{machine-id}/
│  ├─ telemetry       (Machine → Monitor: Sensor readings)
│  ├─ status          (Machine → Orchestrator: Operational state)
│  └─ command         (Orchestrator → Machine: Start/Stop)
│
├─ production/
│  ├─ request         (API → Orchestrator: New order)
│  ├─ status          (Orchestrator → All: Production state)
│  └─ complete        (Orchestrator → All: Order finished)
│
└─ monitoring/
   ├─ metrics         (Monitor → Dashboard: KPIs)
   └─ command         (API → Monitor: Control)
```

### Message Formats

**Machine Status** (Published every 5s)
```json
{
  "machine_id": "cutting-01",
  "machine_type": "cutting",
  "machine_name": "Cutting Machine 01",
  "runtime_state": "idle|busy|error|maintenance",
  "is_running": true,
  "failure_rate": 0.01,
  "total_operations": 156,
  "failed_operations": 2,
  "uptime_seconds": 3600,
  "timestamp": 1700000000.123
}
```

**Machine Telemetry** (Published every 5s)
```json
{
  "machine_id": "cutting-01",
  "machine_type": "cutting",
  "sensor_data": {
    "blade_temperature": 35.2,
    "blade_pressure": 1.8,
    "cut_speed": 0.95,
    "motor_current": 4.2
  },
  "process_data": {
    "current_fabric": "cotton",
    "cut_length": 0.5
  },
  "runtime_state": "busy",
  "timestamp": 1700000000.123
}
```

**Production Request** (API → Orchestrator)
```json
{
  "product_type": "tshirt",
  "quantity": 10,
  "parameters": {
    "size": "M",
    "color": "blue",
    "text": "Hello World",
    "print_type": "screen"
  }
}
```

**Machine Command** (Orchestrator → Machine)
```json
{
  "command": "start|stop|pause|set_failure_rate",
  "operation": "cut_fabric",
  "parameters": {
    "duration": 20,
    "speed": 0.95,
    "material": "cotton"
  }
}
```

---

## Database Schema

### Production Database (PostgreSQL)

```sql
-- Machines Registry
CREATE TABLE machines (
    machine_id VARCHAR(100) PRIMARY KEY,
    machine_type VARCHAR(50) NOT NULL,
    machine_name VARCHAR(255),
    factory_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Production Orders
CREATE TABLE production_orders (
    order_id SERIAL PRIMARY KEY,
    factory_id VARCHAR(100),
    product_type VARCHAR(100),
    quantity INT,
    parameters JSONB,  -- {"size": "M", "color": "blue", ...}
    status VARCHAR(50),  -- pending, in_progress, complete, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (factory_id) REFERENCES machines(factory_id)
);

-- Status History
CREATE TABLE machine_status_log (
    log_id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100),
    runtime_state VARCHAR(50),
    total_operations INT,
    failed_operations INT,
    timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

-- Telemetry Data
CREATE TABLE machine_telemetry (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100),
    machine_type VARCHAR(100),
    sensor_data JSONB,
    runtime_state VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);
```

### Time-Series Database (TimescaleDB)

```sql
-- Sensor Readings (Hypertable)
CREATE TABLE sensor_data (
    machine_id VARCHAR(100) NOT NULL,
    machine_type VARCHAR(100),
    sensor_name VARCHAR(100),
    sensor_value FLOAT NOT NULL,
    runtime_state VARCHAR(50),
    time TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (machine_id, time)
);

-- Convert to hypertable for compression
SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX ON sensor_data (machine_id, time DESC);
CREATE INDEX ON sensor_data (sensor_name, time DESC);

-- Enable compression for old data
ALTER TABLE sensor_data SET (timescaledb.compress = true);
SELECT add_compression_policy('sensor_data', INTERVAL '1 day');
```

**Query Examples**:
```sql
-- Average temperature per minute for last hour
SELECT 
    machine_id,
    time_bucket('1 minute', time) as minute,
    AVG(sensor_value) as avg_temp,
    MAX(sensor_value) as max_temp,
    MIN(sensor_value) as min_temp
FROM sensor_data
WHERE machine_id = 'cutting-01'
  AND sensor_name = 'blade_temperature'
  AND time > NOW() - INTERVAL '1 hour'
GROUP BY machine_id, minute
ORDER BY minute DESC;

-- Anomaly detection: abnormal readings
SELECT machine_id, sensor_name, sensor_value, time
FROM sensor_data
WHERE (sensor_name = 'blade_temperature' AND (sensor_value < 15 OR sensor_value > 60))
  OR (sensor_name = 'blade_pressure' AND (sensor_value < 0.2 OR sensor_value > 3.0))
ORDER BY time DESC
LIMIT 100;
```

---

## MQTT Protocol Details

### Wildcard Subscriptions

**Single Level Wildcard** (`+`)
```
Subscribe: factory/+/machines/+/telemetry
Matches:   factory/tshirt-factory-001/machines/cutting-01/telemetry
           factory/tshirt-factory-001/machines/sewing-01/telemetry
           factory/automotive-plant-001/machines/welding-01/telemetry
```

**Multi-Level Wildcard** (`#`)
```
Subscribe: factory/tshirt-factory-001/#
Matches:   factory/tshirt-factory-001/machines/cutting-01/status
           factory/tshirt-factory-001/machines/cutting-01/telemetry
           factory/tshirt-factory-001/production/request
           factory/tshirt-factory-001/monitoring/metrics
```

### Implementation (Python Paho-MQTT)

```python
from mqtt_client import MQTTClientWrapper

# Create client
client = MQTTClientWrapper(
    client_id="monitoring-service",
    broker="mqttbroker",
    port=1883
)

# Connect to broker
client.connect()

# Subscribe with wildcard pattern
client.subscribe(
    topic="factory/tshirt-factory-001/machines/+/+",
    callback=handle_machine_message,
    qos=0
)

# Start background loop
client.loop_start()

# Callback receives all matching messages
def handle_machine_message(topic, payload):
    # topic: "factory/tshirt-factory-001/machines/cutting-01/telemetry"
    # payload: JSON string
    data = json.loads(payload)
    # Process message
```

### Quality of Service (QoS)

| QoS | Behavior | Use Case |
|-----|----------|----------|
| 0 | At most once | Telemetry (loss acceptable) |
| 1 | At least once | Commands (delivery critical) |
| 2 | Exactly once | (Not used in this system) |

---

## Extension Points

### Adding a New Machine Type

1. **Create machine template** (`machine-templates/my-machine.json`)
```json
{
  "name": "My Machine",
  "machine_id_template": "mymachine-{number}",
  "type": "mymachine",
  "sensors": { ... },
  "operations": [ ... ]
}
```

2. **Update factory config** (`factory-configs/my-factory.json`)
```json
{
  "machines": [
    { "template": "my-machine.json", "count": 2 }
  ]
}
```

3. **Run generator**
```bash
python3 tools/factory_generator.py factory-configs/my-factory.json
```

4. **Start factory**
```bash
cd generated-factories/my-factory-001
docker compose up --build
```

### Adding Custom MQTT Listener

```python
# In monitoring service or custom subscriber
import json
from mqtt_client import MQTTClientWrapper

client = MQTTClientWrapper(
    client_id="custom-listener",
    broker="mqttbroker"
)

def my_callback(topic, payload):
    data = json.loads(payload)
    # Custom processing
    print(f"Machine {data['machine_id']} is {data['runtime_state']}")

client.subscribe("factory/+/machines/+/status", my_callback)
client.connect()
client.loop_start()
```

### Modifying Workflows

Edit workflow template (`workflows/*.json`) then regenerate factory.

---

## Test Case Generation (Factory-Specific & Template-Based)

### Overview

The `TestCaseGenerator` (`shared/template_driven_test_generator.py`) automatically generates factory-specific test cases based on:
- Actual machines in the factory (from config)
- Machine sensor specifications (from templates)
- Factory workflows and product types
- Extreme condition categories

**Key Feature**: Sensor extremes are extracted from machine templates, not hardcoded. This makes test generation completely factory-agnostic and extensible.

### How Sensor Ranges Work

**Before** (Hardcoded, Factory-Specific):
```python
# ❌ PROBLEMS:
# - Generic ranges don't match real machines
# - Different factories have same ranges (not factory-specific)
# - Adding new machine types requires code changes
sensor_extremes = {
    "blade_temperature": (0, 60),      # Too generic
    "thread_tension": (0, 2.0),        # Wrong for sewing machine
}
```

**After** (Template-Based, Data-Driven):
```python
# ✓ BENEFITS:
# - Ranges from cutting-machine.json: blade_temperature (20.0-45.0)
# - Ranges from sewing-machine.json: thread_tension (0.4-1.2)
# - New machine types just need JSON file, no code changes

# Cutting machine gets real specs
extremes = tcg.get_sensor_extremes("cutting", "blade_temperature")
# Returns: (20.0, 45.0)  ✓ From cutting-machine.json template

# Sewing machine gets real specs
extremes = tcg.get_sensor_extremes("sewing", "thread_tension")
# Returns: (0.4, 1.2)  ✓ From sewing-machine.json template
```

### Data Flow

```
Factory Config
    ↓
TestCaseGenerator.__init__()
    ├─ Load all machine templates from machine-templates/*.json
    ├─ Build machines_by_type mapping
    └─ Extract product types from workflows
    ↓
get_machine_sensors(machine_type)
    ├─ Check template for sensor definitions (PRIMARY)
    ├─ Fall back to factory config if needed
    └─ Return list of sensor names
    ↓
get_sensor_extremes(machine_type, sensor_name)
    ├─ Priority 1: Check machine template (EXACT SOURCE)
    ├─ Priority 2: Check factory config
    ├─ Priority 3: Check sensor_defaults dictionary
    └─ Priority 4: Return generic (0.0, 100.0)
    ↓
Generate Test Cases
    └─ Use extracted sensor ranges for realistic test data
```

### Machine Templates & Sensor Specifications

Each machine template defines sensors with precise ranges:

**cutting-machine.json**:
```json
{
  "machine_type": "cutting",
  "sensors": [
    {
      "name": "blade_temperature",
      "type": "float",
      "unit": "celsius",
      "range": {"min": 20.0, "max": 45.0}
    },
    {
      "name": "blade_pressure",
      "type": "float",
      "unit": "bar",
      "range": {"min": 0.5, "max": 2.0}
    }
  ]
}
```

**sewing-machine.json**:
```json
{
  "machine_type": "sewing",
  "sensors": [
    {
      "name": "needle_temperature",
      "type": "float",
      "unit": "celsius",
      "range": {"min": 25.0, "max": 45.0}
    },
    {
      "name": "thread_tension",
      "type": "float",
      "unit": "newton",
      "range": {"min": 0.4, "max": 1.2}
    }
  ]
}
```

### Available Machine Templates

| Template | Machine Type | Sensors | File |
|---|---|---|---|
| Cutting | cutting | 4 | cutting-machine.json |
| Sewing | sewing | 4 | sewing-machine.json |
| Packaging | packaging | 5 | packaging-machine.json |
| Welding | welding | 7 | welding-machine.json |
| Tablet Press | tabletpress | 6 | tablet-press.json |
| Quality Check | qualitycheck | 5 | quality-check-machine.json |
| PCB Assembly | pcbassembly | 5 | pcb-assembly.json |

### Integration with Factory Generation

When `tools/factory_generator.py` generates a factory:

1. Loads factory configuration (`factory-configs/tshirt-factory.json`)
2. Creates `TestCaseGenerator` with config
3. Generator automatically loads all 7 machine templates
4. Test cases generated with template-derived sensor ranges
5. Test cases saved to generated factory's test directory

```python
# In factory_generator.py
from shared.test_case_generator import TestCaseGenerator

# Load factory config
with open(factory_config_path) as f:
    config = json.load(f)

# Create generator (automatically loads templates)
tcg = TestCaseGenerator(config)

# Generate test cases using template-based sensor ranges
test_cases = tcg.generate_batch_test_cases(count=50)

# Save to factory
save_test_cases(test_cases, output_dir)
```

### Example: T-Shirt Factory Test Cases

For T-shirt factory with cutting and sewing machines:

```python
tcg = TestCaseGenerator(tshirt_factory_config)

# Cutting machine test cases use cutting-machine.json specs
test_cases = tcg.generate_for_machine_type("cutting")
# → blade_temperature tests use (20.0-45.0) range
# → blade_pressure tests use (0.5-2.0) range

# Sewing machine test cases use sewing-machine.json specs
test_cases = tcg.generate_for_machine_type("sewing")
# → needle_temperature tests use (25.0-45.0) range
# → thread_tension tests use (0.4-1.2) range
```

### Test Case Structure

Each generated test case includes:

```json
{
  "name": "auto_high_temperature_6048",
  "category": "auto_generated",
  "description": "Test cutting machine behavior at high temperature",
  "preconditions": ["Machine initialized", "Sensors operational"],
  "steps": [
    {
      "action": "update_sensor",
      "machine_type": "cutting",
      "sensor": "blade_temperature",
      "value": 43.5,
      "expected_behavior": "Machine continues normal operation"
    }
  ],
  "expected_outcome": "Machine operates correctly at high temperature",
  "validation": ["No alarms triggered", "Performance nominal"]
}
```

### Extreme Condition Categories

Test cases cover multiple condition types:

| Category | Weight | Purpose |
|---|---|---|
| normal | 20% | Baseline operation |
| high_temperature | 15% | High temperature extremes |
| low_temperature | 15% | Low temperature extremes |
| high_pressure | 15% | High pressure/tension |
| low_pressure | 15% | Low pressure/tension |
| sensor_failure | 10% | Sensor reading extremes |
| mixed_extreme | 10% | Multiple conditions simultaneously |

### Adding New Machine Types

To add a new machine type with automatic test case support:

1. **Create machine template** (`machine-templates/my-machine.json`):
```json
{
  "machine_type": "my_machine",
  "name": "My Custom Machine",
  "sensors": [
    {
      "name": "critical_sensor",
      "type": "float",
      "unit": "units",
      "range": {"min": 10.0, "max": 50.0}
    }
  ]
}
```

2. **Update factory config** to include the machine:
```json
{
  "machines": [
    {"template": "my-machine.json", "count": 1}
  ]
}
```

3. **Regenerate factory** - TestCaseGenerator automatically:
   - Discovers new machine template
   - Extracts sensor specifications
   - Generates test cases using correct sensor ranges

No code changes needed! The system is entirely data-driven.

### Fallback Behavior

If sensor not found in template:

1. Check factory config for embedded sensor definitions
2. Check sensor_defaults dictionary (generic values)
3. Return (0.0, 100.0) with warning log

This ensures backward compatibility while encouraging template-based definitions.

### Testing the System

```bash
# Test template loading and sensor extraction
cd /workspace/tshirt-factory

python3 << 'EOF'
from shared.test_case_generator import TestCaseGenerator
import json

# Load factory
with open('factory-configs/tshirt-factory.json') as f:
    config = json.load(f)

tcg = TestCaseGenerator(config)

# Verify templates loaded
print(f"Templates loaded: {len(tcg.machine_templates)}")
for machine_type in tcg.machine_templates:
    print(f"  - {machine_type}")

# Test sensor extraction
extremes = tcg.get_sensor_extremes("cutting", "blade_temperature")
print(f"\nCutting blade_temperature range: {extremes}")
EOF
```

**Output**:
```
Templates loaded: 7
  - cutting
  - sewing
  - packaging
  - qualitycheck
  - tabletpress
  - welding
  - pcbassembly

Cutting blade_temperature range: (20.0, 45.0)
```

### See Also

- [Template-Based Sensor Extraction Guide](./TEMPLATE_BASED_SENSOR_EXTRACTION.md) - Detailed explanation
- [TestCaseGenerator Source](../shared/template_driven_test_generator.py) - Implementation details
- [Machine Template Schema](../schemas/machine-template-schema.json) - Template structure

---

**End of Architecture Documentation**

See [../EXTENDING.md](EXTENDING.md) for customization guide.
