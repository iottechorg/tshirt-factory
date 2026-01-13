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

**Example: Submit Production**
```bash
curl -X POST http://localhost:5001/production \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "T-Shirt",
    "product_details": {
      "material": "Cotton",
      "stitch_type": "Straight",
      "thread_color": "Blue"
    }
  }'
```
→ Publishes to `factory/tshirt-factory-001/production/request`:
```json
{
  "product_name": "T-Shirt",
  "product_details": {...}
}
```

---

### 4. **Test Cases** (`static/test_cases.json`)

Test cases are now MQTT-driven and support:
- `update_sensor` — Set machine sensor value
- `production_request` — Submit production job
- `delay` — Wait N seconds (for sequential testing)

**Format:**
```json
{
  "name": "high_temp_cutting",
  "description": "...",
  "steps": [
    {
      "action": "update_sensor",
      "machine_id": "cutting-01",
      "sensor_name": "blade_temperature",
      "value": 40
    },
    {
      "action": "production_request",
      "product_name": "T-Shirt",
      "product_details": {...}
    }
  ]
}
```

When user clicks "Run Test", the entire test case is published to:
```
factory/{FACTORY_SITE_ID}/test/request
```

The **factory** (via orchestrator or monitoring service) interprets and executes the test.

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

## Removed Components

The following are **NO LONGER USED**:
- ❌ `machine.py` — Local machine simulation
- ❌ `production.py` — Local production simulation
- ❌ Local `managers.py` thread pools (Machine/Production threads)
- ❌ `reload_machines_from_config()` local machine reloading
- ❌ Hardcoded `MACHINE_NAMES` list

These were replaced by **real factory instances** generated by `factory_generator.py`.

---

## Data Flow Examples

### Scenario 1: User Updates Sensor via UI

```
UI Browser
  ↓
PUT /machines/cutting-01/sensor/blade_temperature (value: 40)
  ↓
app.py: update_sensor_rest()
  ↓
machine_manager.update_machine_sensor(...)
  ├─ Updates local cache (factory_state_manager) for immediate UI feedback
  └─ Publishes to MQTT topic factory/tshirt-factory-001/sensor/update
       ↓
    MQTT Broker
       ↓
    Factory (listens to sensor/update topic)
       ↓
    Machine receives command and updates blade_temperature
       ↓
    Machine publishes updated state to factory/tshirt-factory-001/machines/status
       ↓
    UI State Manager receives update and refreshes UI
```

### Scenario 2: User Runs Test Case

```
UI: Click "Run Test: high_temp_cutting"
  ↓
POST /test/run/high_temp_cutting
  ↓
app.py: run_test_case()
  ├─ Loads test case from static/test_cases.json
  └─ Publishes entire test case to factory/tshirt-factory-001/test/request
       ↓
    MQTT Broker
       ↓
    Factory Orchestrator (listens to test/request)
       ↓
    Orchestrator executes test steps:
       - Set blade_temperature to 40 (update_sensor step)
       - Submit production (production_request step)
       ↓
    Publishes status updates to factory/tshirt-factory-001/machines/status 
    and factory/tshirt-factory-001/production/status
       ↓
    UI State Manager receives updates and displays progress
```

---

## Multi-Factory Support

To support multiple factories, change `FACTORY_SITE_ID` environment variable:

```bash
# Instance 1: tshirt factory
export FACTORY_SITE_ID=tshirt-factory-001
python app.py  # Listens on port 5001

# Instance 2: automotive factory (different terminal)
export FACTORY_SITE_ID=automotive-plant-001
export WEBAPP_PORT=5002
python app.py  # Listens on port 5002
```

Each instance independently subscribes to its factory's MQTT topics and publishes commands to that factory only.

---

## Integration with Generated Factories

The factory generated by `factory_generator.py` must:

1. **Publish machine state** to `factory/{site_id}/machines/status` periodically
   ```json
   [
     {
       "id": "cutting-01",
       "machine_id": "cutting-01",
       "machine_type": "cutting",
       "instance_name": "Fabric Cutting Machine #1",
       "is_running": true,
       "runtime_state": "busy",
       "sensor_data": {
         "blade_temperature": 28.5,
         "blade_pressure": 1.2,
         ...
       },
       "process_data": {...}
     },
     ...
   ]
   ```

2. **Listen to production request** on `factory/{site_id}/production/request`
   ```json
   {
     "product_name": "T-Shirt",
     "product_details": {...}
   }
   ```

3. **Publish production updates** to `factory/{site_id}/production/status`
   ```json
   {
     "production_id": "uuid",
     "product_name": "T-Shirt",
     "status": "running" | "completed" | "failed",
     "steps": [...]
   }
   ```

4. **Listen to sensor updates** on `factory/{site_id}/sensor/update` and apply them

5. **Listen to test requests** on `factory/{site_id}/test/request` and execute test steps

---

## Testing Checklist

- [ ] MQTT broker running and accessible
- [ ] Factory instance running (from `generated-factories/tshirt-factory-001`)
- [ ] Factory publishes machines status to MQTT
- [ ] UI Simulator starts and connects to MQTT
- [ ] GET `/machines` returns factory machines
- [ ] PUT `/machines/<id>/sensor/<name>` updates sensor in factory
- [ ] POST `/production` submits job to factory
- [ ] POST `/test/run/<name>` publishes test case to factory
- [ ] MQTT message traces confirm commands reach factory
- [ ] Factory publishes updated state after each command
- [ ] UI reflects all state changes in real-time

---

## Summary

**Old Approach:** Simulator had dummy machines and local production logic that didn't connect to real factories.

**New Approach:** Simulator is a REST/MQTT bridge connecting UI to real generated factory instances via MQTT. All simulation logic is in the factory, not the UI simulator.

**Benefits:**
✅ Single source of truth (factory state)  
✅ Scales to multiple factories  
✅ UI remains simple and stateless  
✅ Factories are independent and reusable  
✅ Test cases can be defined by users or factory templates  
✅ All communication via MQTT (no REST complexity in factories)
