# System Architecture

**Complete technical reference for the Universal Factory Simulation Platform**

---

## Table of Contents
1. [Three-Layer Design](#three-layer-design)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Service Communication](#service-communication)
5. [Database Schema](#database-schema)
6. [MQTT Protocol](#mqtt-protocol)
7. [Extension Points](#extension-points)

---

## Three-Layer Design

### Layer 1: Configuration (JSON)

The entire system is driven by configuration, not code.

**Machine Templates** (`machine-templates/*.json`)
- Reusable definitions: sensors, operations, failure modes
- 7 pre-built: cutting, sewing, packaging, quality-check, welding, pcb-assembly, tablet-press
- Validated against `schemas/machine-template-schema.json`

Example machine template:
```json
{
  "name": "Cutting Machine",
  "machine_id_template": "cutting-{number}",
  "type": "cutting",
  "sensors": {
    "blade_temperature": { "min": 20, "max": 50, "unit": "°C" },
    "blade_pressure": { "min": 0.5, "max": 2.5, "unit": "bar" }
  },
  "operations": [
    {
      "name": "cut_fabric",
      "duration_seconds": 20,
      "required_sensors": ["blade_temperature", "blade_pressure"]
    }
  ]
}
```

**Factory Configurations** (`factory-configs/*.json`)
- Complete factory definitions
- 5 pre-built: tshirt, automotive, electronics, pharma, food
- Validated against `schemas/factory-config-schema.json`

Example factory config:
```json
{
  "factory_id": "tshirt-factory-001",
  "factory_name": "Smart T-Shirt Manufacturing Plant",
  "machines": [
    { "id": "cutting-01", "template": "cutting-machine.json", "count": 1 },
    { "id": "sewing-01", "template": "sewing-machine.json", "count": 1 },
    { "id": "qualitycheck-01", "template": "quality-check-machine.json", "count": 1 },
    { "id": "packaging-01", "template": "packaging-machine.json", "count": 1 }
  ],
  "workflows": [
    { "file": "tshirt-standard.json" },
    { "file": "premium-tshirt.json" }
  ],
  "production_config": {
    "default_success_rate": 0.99,
    "default_failure_rate": 0.01
  }
}
```

### Layer 2: Generation (Python Tool)

`tools/factory_generator.py` converts JSON into running code.

**Process**:
```
Load JSON Config
    ↓
Validate Against Schemas
    ↓
Generate Machine Classes (Python)
    ↓
Generate Orchestrator Service
    ↓
Generate Docker Compose Configuration
    ↓
Generate Documentation
    ↓
Output: generated-factories/{factory-id}/
```

**Input & Output**:
- **Input**: `factory-configs/tshirt-factory.json`
- **Output**: `generated-factories/tshirt-factory-001/`
  - `docker-compose.yml` (9 services)
  - `services/machines/{type}/machine_service.py` (1 per machine)
  - `services/orchestrator/orchestrator.py`
  - `services/monitoring/monitoring_service.py`
  - `database/init-*.sql` (schema initialization)
  - `mqtt/mosquitto.conf`
  - `README.md` (generated documentation)

### Layer 3: Execution (Docker Services)

Generated factory runs as Docker services.

**Service Stack**:
```
9 Services Total:
├─ MQTT Broker        (Mosquitto, port 31883)
├─ PostgreSQL         (Port 5432)
├─ TimescaleDB        (Port 5433)
├─ Orchestrator       (Workflow coordinator)
├─ Monitoring Service (MQTT listener & data persistence)
├─ Machine 1          (Cutting, type-specific container)
├─ Machine 2          (Sewing, type-specific container)
├─ Machine 3          (Quality Check)
└─ Machine 4          (Packaging)
```

---

## Core Components

### 1. MQTT Broker (Mosquitto)

**Role**: Central message bus for all inter-service communication

**Configuration**: `mqtt/mosquitto.conf`
```
listener 1883 0.0.0.0              # Native MQTT
listener 9001 0.0.0.0              # WebSocket for browsers
protocol mqtt
allow_anonymous true
```

**Features**:
- Publish/subscribe messaging
- Wildcard subscriptions (`+`, `#`)
- QoS 0 (at most once) for telemetry
- QoS 1 (at least once) for commands

### 2. Machine Services

Each machine is an independent container running `machine_service.py`

**Responsibilities**:
- Update sensor values (simulated)
- Publish status and telemetry to MQTT
- Execute operations from orchestrator
- Track operational state (idle, busy, error)

**Lifecycle**:
```
Start
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

**End of Architecture Documentation**

See [../EXTENDING.md](EXTENDING.md) for customization guide.
