# Factory UI Simulator - Quick Reference

## Quick Start

```bash
# 1. Set environment
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export FACTORY_SITE_ID=tshirt-factory-001

# 2. Run simulator
cd factory_ui_simulator
python app.py

# 3. Access UI
open http://localhost:5001
```

---

## REST Endpoints

### Status Queries
```bash
GET /health                    # Health check
GET /machines                  # List all machines
GET /production/status         # Get production status
```

### Commands (Published to Factory via MQTT)
```bash
PUT  /machines/<id>            # Update machine config
PUT  /machines/<id>/sensor/<name>  # Update sensor
POST /production               # Submit production job
POST /test/run/<case_name>     # Run test case
```

### Configuration
```bash
GET /factory-config            # Get current factory config
GET /factory-config/generated/<factory_id>  # Get generated factory config
GET /test_cases.json           # Get test case definitions
```

---

## MQTT Topics

**Simulator → Factory (Published)**
```
factory/{site}/production/request    # {"product_name": "...", "product_details": {...}}
factory/{site}/sensor/update         # {"machine_id": "...", "sensor_name": "...", "value": ...}
factory/{site}/test/request          # {full test case object}
```

**Factory → Simulator (Subscribed)**
```
factory/{site}/machines/status       # [list of machine objects]
factory/{site}/production/status     # {production_id, status, steps}
```

---

## Test a Complete Flow

```bash
# 1. Check machines are available
curl http://localhost:5001/machines

# 2. Update a sensor
curl -X PUT http://localhost:5001/machines/cutting-01/sensor/blade_temperature \
  -H "Content-Type: application/json" \
  -d '{"value": 40}'

# 3. Submit production
curl -X POST http://localhost:5001/production \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "T-Shirt",
    "product_details": {
      "material": "Cotton",
      "stitch_type": "Straight"
    }
  }'

# 4. Check production status
curl http://localhost:5001/production/status

# 5. Run a test case
curl -X POST http://localhost:5001/test/run/normal_production

# 6. Monitor MQTT
mosquitto_sub -h localhost -t "factory/tshirt-factory-001/#" -v
```

---

## Environment Variables

```bash
MQTT_BROKER=localhost              # MQTT broker address
MQTT_PORT=1883                     # MQTT broker port
FACTORY_SITE_ID=tshirt-factory-001 # Factory to control
WEBAPP_PORT=5001                   # Flask server port
```

---

## Architecture

```
┌─────────────────────┐
│   Browser UI        │
│  (static files)     │
└──────────┬──────────┘
           │ (HTTP)
           ▼
┌─────────────────────────────────────┐
│   Flask REST API (app.py)           │
│                                     │
│   - Query endpoints ←─────────────┐ │
│   - Command endpoints ────────┐   │ │
└──────────────┬────────────────┼───┼─┘
               │ (MQTT pub)     │   │
               │ (MQTT sub)     │   │
               ▼                │   │
         MQTT Broker            │   │
               ▲                │   │
               │ ───────────────┘   │
               │ (MQTT pub: status) │
               │                    │
               └────────────────────┘
                      │
                      ▼
         Generated Factory Instance
         (Orchestrator, machines, DB)
```

---

## Key Classes

### factory_state_manager.py
```python
state_mgr = FactoryStateManager(broker, port, site_id)
state_mgr.connect()
machines = state_mgr.get_machines()
production = state_mgr.get_production_status()
```

### managers.py
```python
# All created automatically by initialize_managers()
initialize_managers()  # Start all managers

machine_manager.update_machine_sensor(id, name, value)
production_manager.request_production(name, details)
test_manager.run_test_case(test_case_dict)
```

### app.py
```python
# All endpoints return JSON
GET /machines       → [machines from state]
POST /production    → publish to MQTT, return 202
PUT /sensor         → publish to MQTT, return machine
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Machine not found" | Factory not publishing to MQTT, or wrong FACTORY_SITE_ID |
| "MQTT connection failed" | Broker not running, check MQTT_BROKER/PORT |
| "Empty machines list" | Factory not started, or not publishing machines/status topic |
| "Test case not found" | Check test_cases.json exists and has the test name |
| "No response from sensor update" | Factory not subscribed to sensor/update topic |

---

## Files Changed

✅ **Created:**
- `factory_state_manager.py` — MQTT state manager
- `ARCHITECTURE_MQTT.md` — Architecture guide
- `MIGRATION.md` — Migration guide
- `REFACTORING_SUMMARY.md` — Summary of changes
- `QUICK_REFERENCE.md` — This file

✅ **Refactored:**
- `managers.py` — Now MQTT-based
- `app.py` — Now uses MQTT + state manager
- `config.py` — Updated MQTT topics
- `util.py` — Simplified
- `static/test_cases.json` — Updated format

✅ **Removed:**
- ❌ `machine.py` (no longer needed)
- ❌ `production.py` (no longer needed)

---

## Next Steps

1. **Integrate with Factory:**
   - Ensure factory publishes `machines/status` and `production/status`
   - Ensure factory listens to command topics

2. **Test Integration:**
   ```bash
   # Monitor MQTT while running tests
   mosquitto_sub -h localhost -t "factory/#" -v
   ```

3. **Customize Test Cases:**
   - Edit `static/test_cases.json`
   - Add new test scenarios
   - Publish via REST endpoint

4. **Scale to Multiple Factories:**
   - Run simulator instances with different FACTORY_SITE_ID values
   - Each controls independent factory

---

## Reference Docs

- [ARCHITECTURE_MQTT.md](./ARCHITECTURE_MQTT.md) — Full architecture details
- [MIGRATION.md](./MIGRATION.md) — Detailed migration guide
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) — Complete refactoring details
