# Factory UI Simulator - MQTT-Driven Architecture

## Overview

The **Factory UI Simulator** is now a **stateless REST API + MQTT bridge** that:
- Serves a visual interface for factory monitoring and control
- Forwards all commands (production requests, sensor updates, test cases) to real factories via MQTT
- Reflects factory state (machines, sensors, production status) received via MQTT
- **NO longer** contains internal machine or production simulation code

This design allows multiple simulator instances to control multiple generated factories independently.

---

## Architecture Diagram

```
┌──────────────────────────┐
│   Factory UI (Browser)   │
│  (Angular/React app)     │
└────────────┬─────────────┘
             │ (REST calls)
             ▼
┌──────────────────────────────────────────┐
│  Factory UI Simulator (Flask REST API)   │
│                                          │
│  - GET /machines                         │
│  - PUT /machines/<id>/sensor/<name>      │
│  - POST /production                      │
│  - POST /test/run/<test_case>            │
│  - GET /production/status                │
│  - GET /health                           │
└────────────┬──────────────────────────────┘
             │ (MQTT commands)
             │ (MQTT status subscriptions)
             ▼
┌──────────────────────────────────────────┐
│    MQTT Broker                           │
│    (e.g., Mosquitto, EMQX)              │
└────────────┬──────────────────────────────┘
             │ (publishes machines/production)
             │ (listens for commands)
             ▼
┌──────────────────────────────────────────┐
│   Generated Factory (Docker Compose)     │
│                                          │
│  - Orchestrator (handles workflows)      │
│  - Machine services (execute steps)      │
│  - Database (tracks production)          │
│  - Monitoring service (publishes status) │
└──────────────────────────────────────────┘
```

---

## Key Components

### 1. **factory_state_manager.py**
Maintains in-memory view of factory state received via MQTT.

**Responsibilities:**
- Subscribes to `factory/{FACTORY_SITE_ID}/machines/status` → caches machine list
- Subscribes to `factory/{FACTORY_SITE_ID}/production/status` → caches production updates
- Provides query methods: `get_machines()`, `get_machine(id)`, `get_production_status()`
- Provides `update_sensor_cache()` for local feedback on UI

**Key Methods:**
```python
def get_machines() -> List[Dict]:                      # Return current machines
def get_machine(machine_id: str) -> Optional[Dict]:   # Get one machine
def get_production_status() -> Optional[Dict]:        # Get production status
def update_sensor_cache(machine_id, sensor, value):   # Local cache update (for UI feedback)
```

---

### 2. **managers.py** (Refactored)
Replaces old local simulation managers. Now provides:

**Classes:**
- `CommandManager` — Publishes commands to factory via MQTT
- `MachineManager` — Query/update machines (delegates to CommandManager for updates)
- `ProductionManager` — Submit production requests
- `TestManager` — Run test cases

**MQTT Topics Used:**
- **Commands (Published by simulator):**
  - `factory/{FACTORY_SITE_ID}/production/request` — submit production
  - `factory/{FACTORY_SITE_ID}/sensor/update` — update sensor value
  - `factory/{FACTORY_SITE_ID}/test/request` — run test case

- **Status (Subscribed by state manager):**
  - `factory/{FACTORY_SITE_ID}/machines/status` — machine list + sensor data
  - `factory/{FACTORY_SITE_ID}/production/status` — production progress/results

---

### 3. **app.py** (Refactored REST API)

#### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| **GET** | `/` | Serve HTML UI |
| **GET** | `/machines` | List all machines (from factory state) |
| **PUT** | `/machines/<machine_id>` | Update machine config (e.g., failure_rate) |
| **PUT** | `/machines/<machine_id>/sensor/<sensor_name>` | Update sensor value → publishes to factory |
| **POST** | `/production` | Submit production request → publishes to factory |
| **GET** | `/production/status` | Get current production status |
| **POST** | `/test/run/<test_case_name>` | Run named test case → publishes to factory |
| **GET** | `/test_cases.json` | Serve test case definitions |
| **GET** | `/factory-config` | Get factory configuration |
| **GET** | `/factory-config/generated/<factory_id>` | Get generated factory config JSON |
| **GET** | `/health` | Health check |

**Example: Update Sensor**
```bash
curl -X PUT http://localhost:5001/machines/cutting-01/sensor/blade_temperature \
  -H "Content-Type: application/json" \
  -d '{"value": 40}'
```
→ Publishes to `factory/tshirt-factory-001/sensor/update`:
```json
{
  "machine_id": "cutting-01",
  "sensor_name": "blade_temperature",
  "value": 40.0
}
```

---

### 4. **Test Cases** (`static/test_cases.json`)

Test cases are MQTT-driven and support:
- `update_sensor` — Set machine sensor value
- `production_request` — Submit production job
- `delay` — Wait N seconds (for sequential testing)

When user clicks "Run Test", the entire test case is published to:
```
factory/{FACTORY_SITE_ID}/test/request
```

---

## Configuration

**Environment Variables** (see `config.py`):

```bash
MQTT_BROKER=mqttbroker              # MQTT broker hostname
MQTT_PORT=1883                      # MQTT broker port
FACTORY_SITE_ID=tshirt-factory-001  # Target factory ID
WEBAPP_PORT=5001                    # Flask port
```

**MQTT Topics** (all derived from `FACTORY_SITE_ID`):
```
factory/tshirt-factory-001/machines/status         ← (subscribe)
factory/tshirt-factory-001/production/status       ← (subscribe)
factory/tshirt-factory-001/production/request      → (publish)
factory/tshirt-factory-001/sensor/update           → (publish)
factory/tshirt-factory-001/test/request            → (publish)
factory/tshirt-factory-001/config                  ← (subscribe, optional)
```

---

## Removed Components (archived)

The following components and earlier local simulation code were removed or replaced by generated factories (see archive for originals):
- `machine.py` — Local machine simulation
- `production.py` — Local production simulation
- Old `test_case_generator.py` scripts (migrated to template-driven generator)

---

This archived document preserves the UI-simulator-focused architecture notes.
