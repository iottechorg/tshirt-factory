# Factory UI Simulator - Refactoring Summary

**Date:** January 7, 2026  
**Status:** ✅ Complete

---

## Executive Summary

The **Factory UI Simulator** has been completely refactored from a **local simulation system** to a **stateless MQTT-driven bridge** that connects the visual interface directly to real generated factories.

### Key Outcomes
✅ **Removed** all local machine/production simulation code  
✅ **Eliminated** REST complexity (no REST endpoints in generated factories needed)  
✅ **Centralized** all communication via MQTT  
✅ **Enabled** multi-factory support with single codebase  
✅ **Simplified** UI layer (just REST API + MQTT subscriptions)  

---

## What Was Changed

### 1. New Modules Created

| File | Purpose |
|------|---------|
| `factory_state_manager.py` | MQTT-based state cache for machines and production status |
| `ARCHITECTURE_MQTT.md` | Complete architecture and integration guide |
| `MIGRATION.md` | Developer migration guide |

### 2. Core Modules Refactored

| Module | Before | After |
|--------|--------|-------|
| **managers.py** | Spawned threads running local Machine/Production simulations | Lightweight command publishers + state queries (MQTT-based) |
| **app.py** | Called local managers directly; no real factory integration | REST endpoints publish to MQTT; subscribe to factory state |
| **config.py** | Hardcoded local simulation settings | Factory-centric MQTT topics |
| **util.py** | Old helper functions for local simulation | Minimal: only `resolve_address()` |
| **test_cases.json** | Used `machine_name` (type-based); local execution | Uses `machine_id` (instance-based); published to factory |

### 3. Files Removed (No Longer Used)

| File | Reason |
|------|--------|
| ❌ `machine.py` | Local dummy machines replaced by real factory instances |
| ❌ `production.py` | Local dummy production replaced by factory orchestrator |

---

## Architecture Overview

```
Browser UI (Angular/React)
    ↓ REST calls
Factory UI Simulator (Flask)
    ├─ GET /machines           → queries factory_state_manager
    ├─ PUT /machines/sensor    → publishes to MQTT, updates cache
    ├─ POST /production        → publishes to MQTT
    └─ POST /test/run/<case>   → publishes test to MQTT
    
    MQTT Subscriptions (via factory_state_manager):
    ├─ factory/{site}/machines/status    ← from factory
    └─ factory/{site}/production/status  ← from factory

MQTT Broker
    ↓
Generated Factory Instance
    ├─ Orchestrator (processes workflows)
    ├─ Machine Services (execute steps)
    ├─ Database (tracks state)
    └─ Monitoring Service (publishes status)
```

---

## MQTT Topics

### Commands (Published by Simulator → Received by Factory)

| Topic | Format | Example |
|-------|--------|---------|
| `factory/{site}/production/request` | `{product_name, product_details}` | Submit job |
| `factory/{site}/sensor/update` | `{machine_id, sensor_name, value}` | Set sensor |
| `factory/{site}/test/request` | Full test case object | Execute test |

### Status (Published by Factory → Subscribed by Simulator)

| Topic | Format | Example |
|-------|--------|---------|
| `factory/{site}/machines/status` | `[{id, machine_type, sensors...}]` | Machine list |
| `factory/{site}/production/status` | `{production_id, status, steps}` | Production progress |

---

## Key Features

### 1. ✅ Factory State Management
- `factory_state_manager.py` maintains in-memory cache of factory machines and production status
- Automatic MQTT subscriptions to factory status topics
- Thread-safe state access for REST endpoints

### 2. ✅ REST API Simplification
- No local simulation logic
- All REST endpoints either query state or publish MQTT commands
- Immediate feedback via local cache update (for UI responsiveness)

### 3. ✅ Test Case Execution
- Test cases defined in `static/test_cases.json`
- Supports steps: `update_sensor`, `production_request`, `delay`
- Published as-is to factory via MQTT
- Factory interprets and executes test steps

### 4. ✅ Multi-Factory Support
- Single `FACTORY_SITE_ID` environment variable selects which factory to control
- Run multiple simulator instances (different ports) for multiple factories
- Each instance independently manages its factory

### 5. ✅ MQTT-Only Communication
- No REST endpoints exposed by factory (reduces coupling)
- All commands and status flow through MQTT
- Simplifies factory scaling and deployment

---

## Files Changed (Details)

### managers.py
**Old:** 
```python
class MachineManager(threading.Thread):
    def __init__(self, all_machines, publisher):
        # ... runs async loop with local Machine objects
    def run(self):
        # ... machine_tasks = [loop.create_task(machine.run()) ...]
```

**New:**
```python
class MachineManager:
    def __init__(self, state_manager, command_mgr):
        # ... queries factory_state_manager
    def get_machines(self):
        return self.state_manager.get_machines()  # From MQTT cache
    def update_machine_sensor(self, machine_id, sensor_name, value):
        # Update cache + publish to MQTT
        self.command_mgr.update_sensor(machine_id, sensor_name, value)
```

### app.py
**Old:**
```python
@app.route("/machines", methods=["GET"])
def get_machines():
    return create_response([json.loads(machine.to_json()) for machine in machines])
    # ^ Calls local Machine objects (imported from machine.py)
```

**New:**
```python
@app.route("/machines", methods=["GET"])
def get_machines():
    machines = machine_manager.get_machines()  # From MQTT state
    return create_response(machines)
```

### config.py
**Old:**
```python
MQTT_TOPIC_MACHINE = "machine/data"
MQTT_TOPIC_PRODUCTION = "production/data"
MACHINE_NAMES = ["cutting", "sewing", "ironing", "printing"]
```

**New:**
```python
MQTT_TOPIC_MACHINES_STATUS = f"factory/{FACTORY_SITE_ID}/machines/status"
MQTT_TOPIC_PRODUCTION_STATUS = f"factory/{FACTORY_SITE_ID}/production/status"
MQTT_TOPIC_PRODUCTION_REQUEST = f"factory/{FACTORY_SITE_ID}/production/request"
MQTT_TOPIC_TEST_REQUEST = f"factory/{FACTORY_SITE_ID}/test/request"
```

### test_cases.json
**Old:**
```json
{
  "action": "update_sensor",
  "machine_name": "cutting",  // Type-based
  "sensor_name": "blade_temperature",
  "value": 40
}
```

**New:**
```json
{
  "action": "update_sensor",
  "machine_id": "cutting-01",  // Instance-based
  "sensor_name": "blade_temperature",
  "value": 40
}
```

---

## Environment Variables

| Variable | Old Value | New Value | Purpose |
|----------|-----------|-----------|---------|
| `MQTT_BROKER` | ✓ Used | ✓ Used (critical) | MQTT broker address |
| `MQTT_PORT` | ✓ Used | ✓ Used (critical) | MQTT broker port |
| `FACTORY_SITE_ID` | Default: "site-01" | Default: "tshirt-factory-001" | Target factory ID |
| `PRODUCTION_SUCCESS_RATE` | ✓ Used (local sim) | ❌ Not used | Moved to factory config |
| `MACHINE_NAMES` | ✓ Used (hardcoded) | ❌ Not used | Received from factory |
| `PRODUCTION_LOOP_INTERVAL` | ✓ Used (local loop) | ❌ Not used | Managed by factory |

---

## Integration Checklist

When integrating with a **generated factory**, ensure the factory:

- [ ] Publishes `factory/{site_id}/machines/status` periodically with current machine list and sensor values
- [ ] Publishes `factory/{site_id}/production/status` on production events (started, completed, failed)
- [ ] Listens to `factory/{site_id}/production/request` and processes production jobs
- [ ] Listens to `factory/{site_id}/sensor/update` and updates machine sensors
- [ ] Listens to `factory/{site_id}/test/request` and executes test case steps
- [ ] Uses MQTT QoS 1 or higher for reliability
- [ ] Retries MQTT connections with backoff

---

## Testing Approach

### 1. Unit Tests (Recommended)
```python
# Test factory_state_manager receives and caches MQTT messages
# Test managers publish correct MQTT format
# Test app.py endpoints call correct manager methods
```

### 2. Integration Tests (Manual)
```bash
# 1. Start MQTT broker
docker run -it -p 1883:1883 eclipse-mosquitto

# 2. Start generated factory
cd generated-factories/tshirt-factory-001
docker-compose up

# 3. Start simulator
cd factory_ui_simulator
python app.py

# 4. Test endpoints
curl http://localhost:5001/machines
curl -X POST http://localhost:5001/production -d '{"product_name":"T-Shirt",...}'

# 5. Monitor MQTT
mosquitto_sub -h localhost -t "factory/tshirt-factory-001/#"
```

---

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Coupling** | Tight (simulator tied to specific machine types) | Loose (any factory via MQTT) |
| **Scalability** | Single factory hardcoded | Multiple factories independent |
| **Testability** | Complex (need to mock local objects) | Simple (just mock MQTT) |
| **Maintainability** | High (simulation logic in simulator) | Low (logic in factory, UI is clean) |
| **Reusability** | Low (simulator specific) | High (any factory can use) |
| **Communication** | REST + internal code | MQTT only |
| **Factory Integration** | Required custom REST endpoints | Just MQTT topics |

---

## Migration Path

### For Existing Code

1. **Replace environment variables** in docker-compose or deployment configs
   ```diff
   - MACHINE_NAMES=cutting,sewing,ironing,printing
   + FACTORY_SITE_ID=tshirt-factory-001
   ```

2. **Update UI code** to use new REST endpoints
   ```diff
   - GET /machines → [local_machines]
   + GET /machines → [factory_machines from MQTT]
   ```

3. **Ensure MQTT broker is accessible** from both simulator and factory

4. **Update test automation** to call new endpoints
   ```diff
   - POST /test/<hardcoded_test>
   + POST /test/run/<test_name_from_json>
   ```

### For Custom Extensions

- **Custom machines:** Define in factory-configs, not simulator
- **Custom sensors:** Add to machine templates, factory publishes via MQTT
- **Custom test cases:** Add to `test_cases.json` with supported actions
- **Custom workflows:** Define in factory config, orchestrator executes

---

## Known Limitations & Future Work

### Current Limitations
- Factory must publish status (simulator is passive)
- Test case execution feedback limited to MQTT status updates
- No built-in test result aggregation

### Future Enhancements
- [ ] Add test case editor UI for user-defined cases
- [ ] Implement test result tracking (pass/fail summaries)
- [ ] Add factory discovery (auto-detect available factories)
- [ ] Implement production history/analytics dashboard
- [ ] Add sensor alert thresholds (UI-configurable via MQTT)
- [ ] Support for conditional test steps (branch on production status)

---

## Documentation

Comprehensive guides available:
- **[ARCHITECTURE_MQTT.md](./ARCHITECTURE_MQTT.md)** — Detailed system architecture and data flows
- **[MIGRATION.md](./MIGRATION.md)** — Developer migration and setup guide
- **[README.md](./README.md)** — Quick start (to be updated)

---

## Conclusion

The Factory UI Simulator is now a **lightweight, stateless REST API + MQTT bridge** that cleanly separates the visual interface layer from the factory execution logic. This enables:

✅ **Direct connection to generated factories** via MQTT  
✅ **Multi-factory support** with single codebase  
✅ **Simplified architecture** (no local simulation)  
✅ **Better testability** (MQTT mocking is simple)  
✅ **Improved maintainability** (clear responsibilities)  

All simulation and production logic now lives in **real generated factory instances**, making the system more scalable, reusable, and enterprise-ready.

---

**Implementation Date:** January 7, 2026  
**Status:** ✅ Ready for Integration Testing
