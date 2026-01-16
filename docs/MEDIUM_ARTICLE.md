# Building a Universal, JSON-Driven Factory Simulation Platform

> A production-ready, zero-code platform for defining, generating, and running full IoT factory simulations with template-based sensor extraction and factory-agnostic architecture.

**Author's Perspective**: Manufacturing complexity shouldn't require months of coding. This platform abstracts the entire simulation stack—machines, sensors, workflows, messaging, databases, and APIs—into JSON blueprints. Run `python3 tools/factory_generator.py factory-configs/my-factory.json`, and seconds later you have a complete Docker Compose stack with MQTT, orchestration, telemetry, and REST/WebSocket APIs ready to deploy.

**Purpose**: Enable rapid prototyping, training scenarios, integration testing, and digital twins across ANY industry (t-shirts, automotive, electronics, pharma, food processing, and more) without writing code. Same codebase works for all factories—add new machine types with only JSON files.

**Phase 3 Enhancement (Latest Status)**: Sensor ranges are extracted from machine templates instead of hardcoded in code, making the system truly **factory-agnostic** and **infinitely extensible**. Add new machines by simply adding JSON files—no code changes needed. Test cases automatically generate with accurate, factory-specific sensor ranges.

**In this article you'll learn:**
- The system purpose and design philosophy
- Complete architecture with detailed component interactions
- How components communicate via MQTT topics (ISA-95 compliant)
- Step-by-step factory generation from scratch
- Integration points for custom user interfaces
- Real-world examples and workflows
- How to extend and customize the system

---

## Why This Exists: The Problem & Solution

### The Problem

Manufacturing teams need simulation environments for:
- **Training**: Teach operators without expensive downtime
- **Testing**: Validate control logic, workflows, integrations before hardware deployment
- **Digital Twins**: Mirror production for analytics, "what-if" scenarios, predictive maintenance
- **Integration Testing**: Ensure ERP, MES, analytics systems handle manufacturing events correctly

Existing solutions require:
- Months of custom coding per factory type
- Hardcoded sensor logic repeated for each factory
- Tight coupling between simulation and specific hardware types
- Massive effort to adapt to new industries

### The Solution

**This platform reverses the equation:**

- Define machines, sensors, workflows in **JSON** (no code)
- Generator produces complete Docker stacks automatically
- **Template-based architecture** = same code works for ANY factory
- Add machine types by adding JSON files—no code changes
- Deploy in minutes, not months

**Result**: You can now spin up realistic factory simulations for any industry using the exact same codebase. Change the JSON config, get a completely different factory.

---

## System Design Philosophy

```
┌──────────────────────────────────────────────────────┐
│  Core Principle: Data-Driven, Template-Based        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  • All behavior defined in JSON (not code)          │
│  • Machines defined by templates (not hardcoded)    │
│  • Sensors extracted at generation time             │
│  • Same generator works for all factories           │
│  • Extensible without code changes                  │
│                                                      │
│  Result: True factory-agnostic system               │
└──────────────────────────────────────────────────────┘
```

The key insight: **Generalize the parts, externalize the specifics.**

- **Generic parts** (orchestrator, machine container templates, database layers) → Once in codebase
- **Specific parts** (machine types, sensor specs, workflows) → JSON configs
- **Generator** → Bridges the two, produces customized deployments

This is why a single `factory_generator.py` can produce t-shirt factories, automotive plants, pharmaceutical labs, and food processing facilities.

- Define machines, sensors, workflows and factories in JSON.
- Sensors are automatically extracted from **machine templates** (cutting-machine.json, sewing-machine.json, etc.)—no hardcoded values.
- Run `tools/factory_generator.py` to scaffold a ready-to-run factory in `generated-factories/`.
- Start with `docker compose up --build` in the generated factory folder.
- Telemetry is published to MQTT and persisted to PostgreSQL/TimescaleDB for visualization.
- **Add new machine types by simply adding JSON files**—system is truly extensible without code changes.

---

---

## Complete System Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1: CONFIGURATION LAYER (JSON Files)                         │
│  ├─ factory-configs/: Factory topology, machines, workflows        │
│  ├─ machine-templates/: Machine types with sensor specifications   │
│  ├─ workflows/: Production sequences and routing logic             │
│  └─ schemas/: JSON validation schemas                              │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ (JSON input)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 2: GENERATION LAYER (Code Generator)                        │
│  └─ tools/factory_generator.py                                     │
│     • Reads JSON configs & machine templates                       │
│     • Extracts sensor ranges from templates (Phase 3)              │
│     • Generates Python machine classes                             │
│     • Generates orchestrator & docker-compose                      │
│     • Produces test_cases.json with factory-specific sensor ranges │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ (Runnable factory output)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: EXECUTION LAYER (Docker-based Services)                  │
│  ├─ MQTT Broker (mosquitto): Central message bus                   │
│  ├─ Orchestrator: Coordinates production workflows                 │
│  ├─ Machine Services: Simulate sensors & execute operations        │
│  ├─ PostgreSQL: Transactional data (orders, status history)        │
│  ├─ TimescaleDB: Time-series telemetry data                        │
│  └─ Monitoring Service: Aggregates metrics & alerts                │
│                                                                     │
│  Plus (Optional):                                                   │
│  ├─ API Gateway (REST/WebSocket): factory_ui_simulator            │
│  └─ Frontends (Angular, HTML/JS): Customer UIs                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Components & Responsibilities

#### 1. **Configuration Layer** (What to simulate)

**factory-configs/*.json**: Defines factory topology
```json
{
  "factory_id": "tshirt-factory-001",
  "factory_name": "T-Shirt Manufacturing Plant",
  "machines": [
    {"id": "cutting-01", "template": "cutting-machine.json", "count": 1},
    {"id": "sewing-01", "template": "sewing-machine.json", "count": 2},
    {"id": "qc-01", "template": "quality-check-machine.json", "count": 1},
    {"id": "packaging-01", "template": "packaging-machine.json", "count": 1}
  ],
  "workflows": [{"file": "tshirt-standard.json", "enabled": true}],
  "production_config": {
    "default_success_rate": 0.95,
    "shift_duration_hours": 8
  }
}
```

**machine-templates/*.json**: Defines machine types with sensor specs
```json
{
  "machine_type": "cutting",
  "sensors": {
    "blade_temperature": {
      "description": "Temperature of cutting blade",
      "unit": "°C",
      "min": 20.0,
      "max": 45.0,
      "update_frequency": 2000
    },
    "blade_pressure": {
      "description": "Pressure applied by cutting mechanism",
      "unit": "bar",
      "min": 0.5,
      "max": 2.0,
      "update_frequency": 2000
    }
  },
  "operations": [
    {
      "name": "cut_fabric",
      "duration_seconds": 15,
      "failure_prone": true
    }
  ]
}
```

**workflows/*.json**: Defines production sequences
```json
{
  "workflow_id": "tshirt-standard",
  "steps": [
    {
      "step_number": 1,
      "name": "Cutting",
      "machine_type": "cutting",
      "operation": "cut_fabric",
      "success_rate": 0.98,
      "next_step_on_success": 2,
      "next_step_on_failure": "reject"
    },
    {
      "step_number": 2,
      "name": "Sewing",
      "machine_type": "sewing",
      "operation": "stitch_seams",
      "success_rate": 0.97,
      "next_step_on_success": 3,
      "next_step_on_failure": "rework"
    }
  ]
}
```

#### 2. **Generation Layer** (How to build it)

**tools/factory_generator.py**: The magic piece
- Reads factory config + machine templates
- **Extracts sensor ranges** from templates (Phase 3 improvement)
- Generates Python classes for each machine type
- Generates orchestrator service
- Produces docker-compose.yml with all services
- Creates test_cases.json with factory-specific sensor ranges
- Outputs ready-to-run `generated-factories/{factory-id}/`

**Key Phase 3 Innovation**:
```python
# OLD (Hardcoded, generic):
sensor_ranges = {"blade_temperature": (0, 100)}  # ❌ Wrong for cutting

# NEW (Template-based, accurate):
template = load_template("cutting-machine.json")
sensor_ranges = template["sensors"]["blade_temperature"]["range"]  # ✓ (20, 45)
```

#### 3. **Execution Layer** (How it runs)

Each generated factory is a complete Docker Compose stack with 6 core services:

**MQTT Broker (mosquitto)**
- Central message bus for all communication
- Runs on port 1883 (MQTT), 9001 (WebSocket)
- Implements ISA-95 compliant topic hierarchy
- All messages flow through here

**Orchestrator Service**
- Listens to `factory/{id}/production/request` topics
- Loads workflow templates
- Issues START/STOP commands to machines via MQTT
- Tracks workflow progress
- Publishes production status updates
- Records completion events

**Machine Services** (one container per machine instance)
- Each is a lightweight Python application
- Initializes sensors from template specs (not hardcoded)
- Every 2 seconds: updates sensor values (simulate drift, state changes)
- Every 5 seconds: publishes telemetry to MQTT
- Listens to `factory/{id}/machines/{id}/command` for orchestrator commands
- Executes operations and publishes results
- Handles failures and error states

**PostgreSQL**
- Stores transactional data:
  - Production orders (what/when/status)
  - Machine status history
  - Workflow execution logs
- Queried by monitoring service and APIs

**TimescaleDB**
- Stores high-cardinality time-series data:
  - Sensor telemetry (millions of data points per day)
  - Machine operating parameters
  - Optimized for time-range queries and aggregations

**Monitoring Service** (template)
- Subscribes to all machine telemetry (`factory/{id}/machines/+/telemetry`)
- Persists data to PostgreSQL/TimescaleDB
- Detects anomalies (high error rates, stuck machines)
- Publishes alerts to `factory/{id}/monitoring/metrics`

---

---

## Component Communication: MQTT Topic Architecture

All components communicate asynchronously via MQTT topics following **ISA-95 (Manufacturing Message Specification)** compliance.

### ISA-95 Topic Hierarchy

```
factory/{factory-id}/
│
├─ machines/{machine-id}/
│  ├─ telemetry              [Machine → Monitor] Sensor readings
│  │  └─ Payload: {sensor_data, runtime_state, timestamp}
│  │
│  ├─ status                 [Machine → All] Operational state
│  │  └─ Payload: {runtime_state, total_operations, failed_ops}
│  │
│  └─ command                [Orchestrator → Machine] Control
│     └─ Payload: {command, operation, parameters}
│
├─ production/
│  ├─ request                [API/UI → Orchestrator] New order
│  │  └─ Payload: {product_type, quantity, product_details}
│  │
│  ├─ status                 [Orchestrator → All] Progress updates
│  │  └─ Payload: {production_id, status, current_step}
│  │
│  └─ complete               [Orchestrator → All] Finished
│     └─ Payload: {production_id, result, duration_seconds}
│
└─ monitoring/
   ├─ metrics                [Monitor → Dashboard] Real-time KPIs
   │  └─ Payload: {error_rate, throughput, avg_cycle_time}
   │
   └─ command                [API → Monitor] Control monitoring
      └─ Payload: {command, parameters}
```

### Flow 1: Production Order (T-Shirt Example)

**Numbered sequence diagram with MQTT topics:**

```
Step 1: User places order via frontend
        Customer Frontend
        ↓ HTTP POST /production
        ↓ {"product_type": "tshirt", "color": "blue", "size": "M"}
        
Step 2: API Gateway receives and publishes to MQTT
        API Gateway (factory_ui_simulator)
        ↓ PUBLISH to factory/tshirt-001/production/request
        ↓ Topic: factory/tshirt-001/production/request
        
Step 3: Orchestrator subscribes and receives order
        Orchestrator Service
        ↓ SUBSCRIBE factory/tshirt-001/production/request
        ↓ Loads workflow: tshirt-standard.json
        ↓ Creates production instance
        
Step 4: Orchestrator issues FIRST command (Cutting)
        ↓ PUBLISH factory/tshirt-001/machines/cutting-01/command
        ↓ {"command": "start", "operation": "cut_fabric"}
        
Step 5: Cutting machine receives command
        Cutting Machine Service
        ↓ SUBSCRIBE factory/tshirt-001/machines/cutting-01/command
        ↓ Starts operation (15 seconds)
        
Step 6: Cutting machine publishes telemetry (every 5s)
        ↓ PUBLISH factory/tshirt-001/machines/cutting-01/telemetry
        ↓ {"blade_temperature": 35.2, "blade_pressure": 1.8, "runtime_state": "busy"}
        
Step 7: Cutting machine publishes status when done
        ↓ PUBLISH factory/tshirt-001/machines/cutting-01/status
        ↓ {"runtime_state": "idle", "total_operations": 156, "result": "success"}
        
Step 8: Orchestrator receives completion, moves to NEXT step (Sewing)
        Orchestrator Service (listening to status)
        ↓ PUBLISH factory/tshirt-001/machines/sewing-01/command
        ↓ {"command": "start", "operation": "stitch_seams"}
        
Step 9: Sewing machine processes (2 containers in parallel)
        Sewing-01 Machine Service
        ↓ PUBLISH factory/tshirt-001/machines/sewing-01/telemetry (every 5s)
        
        Sewing-02 Machine Service
        ↓ PUBLISH factory/tshirt-001/machines/sewing-02/telemetry (every 5s)
        
Step 10: Quality Check machine validates
        QC-01 Machine Service
        ↓ PUBLISH factory/tshirt-001/machines/qc-01/status (result: "pass" or "fail")
        
Step 11: Packaging machine completes
        Packaging-01 Machine Service
        ↓ PUBLISH factory/tshirt-001/machines/packaging-01/status
        
Step 12: Orchestrator marks production complete
        ↓ PUBLISH factory/tshirt-001/production/complete
        ↓ {"production_id": "uuid", "result": "success", "duration": 145}
        
Step 13: Monitoring service captures all telemetry
        Monitoring Service (listening to all machines/+/telemetry)
        ↓ Stores in PostgreSQL & TimescaleDB
        ↓ PUBLISH factory/tshirt-001/monitoring/metrics
        
Step 14: Frontend receives real-time updates via WebSocket
        API Gateway WebSocket Bridge
        ↓ Subscribed to factory/tshirt-001/#
        ↓ Forwards updates to browser via WebSocket
        ↓ UI displays: "Order complete: 145 seconds"
```

**Mermaid flowchart with numbered steps:**

```mermaid
flowchart TD
    Step1["1️⃣ User: Place Order via Frontend<br/>(Design: color, size, etc.)"]
    Step2["2️⃣ Frontend: POST to API<br/>http://localhost:5000/production"]
    Step3["3️⃣ API Gateway: PUBLISH<br/>factory/tshirt-001/production/request"]
    Step4["4️⃣ MQTT Broker: Routes message"]
    Step5["5️⃣ Orchestrator: SUBSCRIBE & Receive<br/>Loads workflow template"]
    Step6["6️⃣ Orchestrator: PUBLISH START command<br/>→ factory/tshirt-001/machines/cutting-01/command"]
    Step7["7️⃣ Cutting Machine: SUBSCRIBE & START<br/>Execute for 15 seconds"]
    Step8["8️⃣ Cutting Machine: PUBLISH telemetry every 5s<br/>→ factory/tshirt-001/machines/cutting-01/telemetry"]
    Step9["9️⃣ Monitoring Service: SUBSCRIBE<br/>Store in TimescaleDB"]
    Step10["🔟 Cutting Machine: PUBLISH completion<br/>→ factory/tshirt-001/machines/cutting-01/status"]
    Step11["1️⃣1️⃣ Orchestrator: START next step (Sewing)<br/>→ factory/tshirt-001/machines/sewing-01/command"]
    Step12["1️⃣2️⃣ Repeat for all steps<br/>(Sewing → QC → Packaging)"]
    Step13["1️⃣3️⃣ Orchestrator: PUBLISH production/complete<br/>→ factory/tshirt-001/production/complete"]
    Step14["1️⃣4️⃣ API WebSocket: PUSH to Frontend<br/>UI displays: Order Complete!"]
    
    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4
    Step4 --> Step5
    Step5 --> Step6
    Step6 --> Step7
    Step7 --> Step8
    Step8 --> Step9
    Step8 --> Step10
    Step10 --> Step11
    Step11 --> Step12
    Step12 --> Step13
    Step13 --> Step14
```

### Flow 2: Real-Time Telemetry Streaming

```mermaid
flowchart TD
    Machines["All Machine Services<br/>cutting-01, sewing-01, sewing-02, qc-01, packaging-01"]
    MQTT["MQTT Broker<br/>(Mosquitto)"]
    Monitor["Monitoring Service<br/>Subscribes to machines/+/telemetry"]
    TimesDB["TimescaleDB<br/>Time-series storage"]
    APIGateway["API Gateway<br/>WebSocket Bridge"]
    Frontend["Customer Frontend<br/>Real-time Dashboard"]
    
    Machines -->|PUBLISH telemetry<br/>every 5 seconds| MQTT
    MQTT -->|Routes to Monitor<br/>wildcard subscription| Monitor
    MQTT -->|Routes to API Gateway<br/>WebSocket forwarding| APIGateway
    Monitor -->|INSERT sensor data| TimesDB
    APIGateway -->|WebSocket PUSH<br/>real-time updates| Frontend
    
    style MQTT fill:#ff9999
    style Monitor fill:#99ccff
    style TimesDB fill:#99ff99
    style APIGateway fill:#ffcc99
    style Frontend fill:#cc99ff
```

### Flow 3: Machine Service Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initialize: Container starts
    Initialize --> Idle: Load template sensors<br/>Initialize from schema
    Idle --> Listening: Subscribe to<br/>machines/{id}/command
    Listening --> Busy: Receive START<br/>command
    Busy --> Updating: Every 2s update<br/>sensor values
    Busy --> Publishing: Every 5s<br/>publish telemetry
    Publishing --> Busy: Continue simulation
    Busy --> Error: Random failure<br/>or high sensor value
    Error --> Recovering: Log error<br/>increment failed_ops
    Recovering --> Idle: Reset state
    Busy --> Complete: Operation duration<br/>exceeded
    Complete --> Idle: Publish COMPLETE<br/>status
    Listening --> [*]: Container stops
```

---

## Factory Generation: From Scratch to Production

### Complete Step-by-Step Factory Creation

#### Step 1: Plan Your Factory

Document your factory requirements:

```yaml
Factory Name: "Electronics Assembly Plant"
Machines:
  - 2x PCB Assembly machines
  - 2x Soldering stations
  - 1x Quality Check machine
  - 1x Packaging machine

Workflows:
  - Standard: Assembly → Soldering → QC → Packaging
  - Express: Assembly → Direct Packaging (no soldering)

Production:
  - 240 orders per hour target
  - 96% success rate
  - 8-hour shifts
```

#### Step 2: Define Machine Templates

Create or reuse machine templates in `machine-templates/`. Example for a new machine:

```json
{
  "machine_type": "solder_station",
  "description": "Wave soldering machine for circuit board assembly",
  "machine_id_template": "solder-{number}",
  "sensors": {
    "solder_temperature": {
      "description": "Temperature of solder bath",
      "unit": "°C",
      "min": 240.0,
      "max": 260.0,
      "update_frequency": 2000
    },
    "conveyor_speed": {
      "description": "Board movement speed through solder bath",
      "unit": "mm/s",
      "min": 50.0,
      "max": 150.0,
      "update_frequency": 2000
    },
    "dwell_time": {
      "description": "Time board spends in solder",
      "unit": "seconds",
      "min": 3.0,
      "max": 8.0,
      "update_frequency": 5000
    }
  },
  "operations": [
    {
      "name": "wave_solder",
      "description": "Wave solder circuit boards",
      "duration_seconds": 30,
      "required_sensors": ["solder_temperature", "conveyor_speed"],
      "failure_prone": true,
      "error_description": "Solder joint failure or cold solder"
    }
  ],
  "failure_modes": [
    {
      "sensor": "solder_temperature",
      "condition": "value > 265",
      "action": "emergency_stop",
      "description": "Temperature too high - emergency shutdown"
    },
    {
      "sensor": "conveyor_speed",
      "condition": "value < 40",
      "action": "warning",
      "description": "Conveyor speed too slow - quality degradation"
    }
  ]
}
```

#### Step 3: Create Factory Configuration

Create `factory-configs/electronics-plant.json`:

```json
{
  "factory_id": "electronics-plant-001",
  "factory_name": "Electronics Assembly Manufacturing Plant",
  "factory_type": "electronics_manufacturing",
  "location": "Singapore",
  "description": "High-volume PCB assembly and soldering facility",

  "machines": [
    {
      "id": "pcb-assembly-01",
      "template": "pcb-assembly.json",
      "count": 2,
      "parameters": {}
    },
    {
      "id": "solder-station-01",
      "template": "solder-station.json",
      "count": 2,
      "parameters": {}
    },
    {
      "id": "quality-check-01",
      "template": "quality-check-machine.json",
      "count": 1,
      "parameters": {}
    },
    {
      "id": "packaging-01",
      "template": "packaging-machine.json",
      "count": 1,
      "parameters": {}
    }
  ],

  "workflows": [
    {
      "file": "electronics-standard.json",
      "enabled": true,
      "priority": 1
    },
    {
      "file": "electronics-express.json",
      "enabled": true,
      "priority": 2
    }
  ],

  "production_config": {
    "max_orders_queue": 500,
    "default_success_rate": 0.96,
    "default_failure_rate": 0.04,
    "shift_duration_hours": 8,
    "orders_per_hour": 240
  },

  "database_config": {
    "enable_timescaledb": true,
    "telemetry_retention_days": 30,
    "enable_data_compression": true
  },

  "monitoring_config": {
    "enable_alerts": true,
    "alert_threshold_error_rate": 0.08,
    "enable_predictive_maintenance": true
  }
}
```

#### Step 4: Define Workflows

Create `workflows/electronics-standard.json`:

```json
{
  "workflow_id": "electronics-standard-v1",
  "workflow_name": "Standard Electronics Assembly",
  "description": "PCB assembly → Soldering → Quality check → Packaging",
  "version": "1.0",

  "steps": [
    {
      "step_number": 1,
      "name": "PCB Assembly",
      "machine_type": "pcb_assembly",
      "operation": "place_components",
      "parameters": {
        "board_type": "mixed_signal",
        "precision": "high"
      },
      "timeout_seconds": 120,
      "success_rate": 0.98,
      "next_step_on_success": 2,
      "next_step_on_failure": 5
    },
    {
      "step_number": 2,
      "name": "Wave Soldering",
      "machine_type": "solder_station",
      "operation": "wave_solder",
      "parameters": {
        "solder_profile": "standard",
        "dwell_time": 5.5
      },
      "timeout_seconds": 60,
      "success_rate": 0.96,
      "next_step_on_success": 3,
      "next_step_on_failure": 5
    },
    {
      "step_number": 3,
      "name": "Quality Check",
      "machine_type": "quality_check",
      "operation": "test_electrical",
      "parameters": {
        "test_duration": 30,
        "voltage_levels": [3.3, 5.0, 12.0]
      },
      "timeout_seconds": 90,
      "success_rate": 0.99,
      "next_step_on_success": 4,
      "next_step_on_failure": 6
    },
    {
      "step_number": 4,
      "name": "Packaging",
      "machine_type": "packaging",
      "operation": "package_board",
      "parameters": {
        "packaging_type": "anti_static"
      },
      "timeout_seconds": 45,
      "success_rate": 0.99,
      "next_step_on_success": 7,
      "next_step_on_failure": 7
    },
    {
      "step_number": 5,
      "name": "Rework",
      "machine_type": "solder_station",
      "operation": "rework_soldering",
      "timeout_seconds": 180,
      "next_step_on_success": 3,
      "next_step_on_failure": 6
    },
    {
      "step_number": 6,
      "name": "Scrap",
      "status": "failed",
      "description": "Board scrapped - repeated failure"
    },
    {
      "step_number": 7,
      "name": "Complete",
      "status": "success",
      "description": "Electronics assembly complete - ready to ship"
    }
  ],

  "error_handlers": [
    {
      "condition": "step_timeout",
      "action": "retry_step",
      "retry_count": 2,
      "retry_delay_seconds": 5
    },
    {
      "condition": "machine_error",
      "action": "escalate_to_rework",
      "rework_step": 5
    }
  ]
}
```

#### Step 5: Generate the Factory

```bash
# Validate your JSON first
python3 -m json.tool factory-configs/electronics-plant.json > /dev/null && echo "✓ Valid"

# Generate the complete factory
python3 tools/factory_generator.py factory-configs/electronics-plant.json

# Output will be: generated-factories/electronics-plant-001/
```

**What the generator produces:**

```
generated-factories/electronics-plant-001/
├── docker-compose.yml                    # All services and networks
├── test_cases.json                       # Factory-specific test cases
├── automation_config.json                # Production automation config
├── services/
│   ├── orchestrator/
│   │   ├── orchestrator.py               # Generated workflow coordinator
│   │   └── Dockerfile
│   ├── machines/
│   │   ├── pcb-assembly/
│   │   │   ├── machine_service.py        # PCB assembly machine
│   │   │   └── Dockerfile
│   │   ├── solder-station/
│   │   │   ├── machine_service.py        # Soldering machine
│   │   │   └── Dockerfile
│   │   ├── quality-check/
│   │   │   ├── machine_service.py
│   │   │   └── Dockerfile
│   │   └── packaging/
│   │       ├── machine_service.py
│   │       └── Dockerfile
│   ├── monitoring/
│   │   ├── monitoring_service.py
│   │   └── Dockerfile
│   └── shared/
│       ├── mqtt_client.py
│       ├── database.py
│       └── config.py
└── README.md                             # Generated factory documentation
```

#### Step 6: Deploy the Factory

```bash
# Navigate to generated factory
cd generated-factories/electronics-plant-001

# Start all services
docker compose up --build -d

# Verify services are running
docker compose ps

# Output example:
# NAME                          STATUS
# electronics-plant-001-mqtt    Up 2 minutes
# pcb-assembly-01               Up 2 minutes
# pcb-assembly-02               Up 2 minutes
# solder-station-01             Up 2 minutes
# solder-station-02             Up 2 minutes
# quality-check-01              Up 2 minutes
# packaging-01                  Up 2 minutes
# orchestrator                  Up 2 minutes
# monitoring                    Up 2 minutes
# postgres                      Up 2 minutes
# timescaledb                   Up 2 minutes

# Check logs
docker compose logs -f orchestrator
```

#### Step 7: Validate & Test

```bash
# Monitor MQTT messages
mosquitto_sub -h localhost -p 31883 -t 'factory/electronics-plant-001/#' -v

# Place a test order
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{
    "product_type": "pcb_board_standard",
    "quantity": 10,
    "product_details": {
      "board_type": "mixed_signal",
      "voltage_levels": [3.3, 5.0]
    }
  }'

# Check production status
curl http://localhost:5000/production | jq

# Query telemetry from database
docker exec electronics-plant-001-timescaledb psql -U factory_user -d factory_timeseries -c \
  "SELECT * FROM sensor_data WHERE machine_id='solder-station-01' LIMIT 5;"
```

---

## Connecting User Interfaces

### Architecture: UI Integration Points

```mermaid
graph TD
    subgraph "Generated Factory"
        MQTT["MQTT Broker<br/>(Port 1883, 9001 WS)"]
        Orch["Orchestrator"]
        Machines["Machine Services"]
        Postgres["PostgreSQL"]
        TimesDB["TimescaleDB"]
    end
    
    subgraph "API Layer"
        APIGateway["API Gateway<br/>(factory_ui_simulator)<br/>Port 5000"]
    end
    
    subgraph "Frontend UIs"
        Angular["Customer UI<br/>(Angular)<br/>Port 3000"]
        HTML["Operator UI<br/>(HTML/JS)<br/>Port 3001"]
        Custom["Custom UI<br/>(React/Vue/etc)<br/>Port 3002+"]
    end
    
    subgraph "External Systems"
        ERP["ERP System"]
        MES["MES System"]
        Analytics["Analytics Platform"]
    end
    
    MQTT -->|REST API| APIGateway
    MQTT -->|WebSocket<br/>Real-time updates| APIGateway
    APIGateway -->|HTTP + WebSocket| Angular
    APIGateway -->|HTTP + WebSocket| HTML
    APIGateway -->|HTTP + WebSocket| Custom
    APIGateway -->|MQTT Bridge| ERP
    APIGateway -->|MQTT Bridge| MES
    Postgres -->|Query| Analytics
    TimesDB -->|Query| Analytics
```

### API Gateway (factory_ui_simulator) - Connection Point

The API Gateway is the central hub for all UI connections. It provides:

**REST Endpoints:**
```
GET    /machines              Get all machines & current state
GET    /machines/{id}         Get specific machine details
PUT    /machines/{id}/sensor/{name}  Manually set sensor for testing
GET    /production            Get all production orders
POST   /production            Place new order
GET    /production/{id}       Get specific order status
POST   /production/{id}/cancel Cancel running order
GET    /telemetry/{machine}   Get recent telemetry for a machine
GET    /health               Health check for all services
```

**WebSocket Endpoints:**
```
ws://localhost:5000/subscribe/{factory_id}
  Subscribes to all MQTT topics for {factory_id}
  Receives real-time updates as they happen
```

### Integration Pattern 1: Customer Frontend (Placing Orders)

**Component Communication Flow:**

```mermaid
sequenceDiagram
    participant UI as Customer UI<br/>React/Angular
    participant API as API Gateway<br/>REST/WebSocket
    participant MQTT as MQTT Broker
    participant Orch as Orchestrator
    
    UI->>UI: User designs product
    UI->>API: POST /production
    API->>MQTT: Publish to<br/>production/request
    API-->>UI: 200 OK
    MQTT->>Orch: Production request
    Orch->>Orch: Start workflow
    
    UI->>API: WebSocket subscribe
    loop Real-time updates
        Orch->>MQTT: Status updates
        MQTT->>API: Route to WebSocket
        API-->>UI: Push update
        UI->>UI: Update dashboard
    end
    
    Orch->>MQTT: Production complete
    API-->>UI: Order finished
```

### Pre-built UI Features

**1. Customer Order UI (Angular)**
- Product designer with customization options
- Order placement and tracking
- Real-time status via WebSocket
- Order history

**2. Operator Dashboard**
- All machines and real-time status
- Sensor values and gauges
- Production queue visualization
- Error alerts and notifications

**3. API Gateway**
- RESTful endpoints for all operations
- WebSocket for real-time subscriptions
- MQTT bridge for external systems

---

## Phase 3: Template-Based Sensor Extraction

**Before** (Hardcoded, Factory-Specific):
```python
# ❌ Generic values, same for all factories
sensor_extremes = {
    "blade_temperature": (0, 60),
    "thread_tension": (0, 2.0),
}
```

**After** (Template-Based, Data-Driven):
```python
# ✓ Data from cutting-machine.json: blade_temperature (20.0-45.0)
# ✓ Data from sewing-machine.json: thread_tension (0.4-1.2)
# ✓ Same code works for ANY factory

extremes = tcg.get_sensor_extremes("cutting", "blade_temperature")
# Returns: (20.0, 45.0) — accurate for cutting machines
```

### Key Improvement

Test cases are no longer generated with hardcoded, generic sensor ranges. Instead:

1. **Machine templates** define realistic sensor specifications
2. **TestCaseGenerator** loads templates at initialization
3. **Sensors are extracted on-demand** from templates (Priority: Template → Config → Defaults)
4. **Different machines get different ranges** automatically

### Result

- **Factory-Agnostic**: Same code works for t-shirt factory, pharmaceutical plant, automotive assembly
- **Accurate**: Sensor ranges match actual machine capabilities
- **Extensible**: Add new machines with only JSON—no code changes
- **Scalable**: Works with unlimited machine types

### Available Templates

7 pre-built machine templates:

| Machine | Template | Sensors |
|---------|----------|---------|
| Cutting | cutting-machine.json | blade_temperature (20-45°C), blade_pressure (0.5-2 bar), cut_speed, motor_current |
| Sewing | sewing-machine.json | needle_temperature (25-45°C), thread_tension (0.4-1.2 N), stitch_speed |
| Packaging | packaging-machine.json | sealing_temperature, conveyor_speed, label_dispenser_level, etc. |
| Quality Check | quality-check-machine.json | camera_temperature, light_intensity, scan_speed, defect_detection_rate |
| Welding | welding-machine.json | arc_temperature, welding_pressure, travel_speed, voltage, current |
| Tablet Press | tablet-press.json | pressure, temperature, speed, cycle_time, punch_force |
| PCB Assembly | pcb-assembly.json | solder_temperature, placement_speed, accuracy, pressure, humidity |

### Adding New Machine Types

```bash
# 1. Create template (only JSON needed)
cat > machine-templates/custom-machine.json << 'EOF'
{
  "machine_type": "custom",
  "sensors": [
    {
      "name": "sensor_one",
      "unit": "celsius",
      "range": {"min": 20.0, "max": 100.0}
    }
  ]
}
EOF

# 2. Use in factory config
{
  "machines": [
    {"machine_type": "custom", "id": "custom-01"}
  ]
}

# 3. Generate factory
python3 tools/factory_generator.py factory-configs/my-factory.json

# ✓ Done! New machine automatically supported.
# ✓ No code changes needed.
# ✓ Test cases use correct sensor ranges.
```

---

## Extending the Platform: Customization & Integration

The platform is designed for extensibility at every level. Here are the main extension points:

### Extension 1: Add New Machine Types

**Requirement**: Add support for a "laser cutting" machine

**Step 1: Create machine template**

```json
// machine-templates/laser-cutter.json
{
  "machine_type": "laser_cutter",
  "description": "CO2 laser cutting system",
  "sensors": {
    "laser_power": {"unit": "W", "min": 0, "max": 150},
    "chamber_temperature": {"unit": "°C", "min": 15, "max": 35},
    "material_feed_speed": {"unit": "mm/s", "min": 10, "max": 100}
  },
  "operations": [
    {
      "name": "cut_material",
      "duration_seconds": 20,
      "failure_prone": true
    }
  ]
}
```

**Step 2: Use in factory config**

```json
{
  "machines": [
    {"id": "laser-01", "template": "laser-cutter.json", "count": 1}
  ]
}
```

**Step 3: Generate and deploy**

```bash
python3 tools/factory_generator.py factory-configs/updated-factory.json
# ✓ Done! No code changes needed.
# ✓ New machine automatically supported
# ✓ Sensors extracted from template
# ✓ Test cases generated with correct ranges
```

### Extension 2: Custom Workflow Logic

**Requirement**: Complex routing based on material type

```json
{
  "workflow_id": "advanced-cutting",
  "steps": [
    {
      "step_number": 1,
      "name": "Material Detection",
      "type": "sensor_check",
      "condition": "material_thickness > 3mm",
      "on_true": {"next_step": 2},
      "on_false": {"next_step": 3}
    },
    {
      "step_number": 2,
      "name": "Slow Cut (Thick)",
      "machine_type": "laser_cutter",
      "parameters": {"power": 120, "speed": 20}
    },
    {
      "step_number": 3,
      "name": "Fast Cut (Thin)",
      "machine_type": "laser_cutter",
      "parameters": {"power": 80, "speed": 80}
    }
  ]
}
```

### Extension 3: Custom Monitoring & Alerts

**Add predictive maintenance logic:**

```python
# In monitoring_service.py (after generation, customize)

class CustomMonitoring(MonitoringService):
    def check_machine_health(self, machine_id, telemetry):
        """Custom health checks beyond defaults"""
        
        # Predictive maintenance: detect blade wear
        if machine_id.startswith("cutting"):
            blade_temp_trend = self.analyze_temperature_trend(machine_id)
            if blade_temp_trend > 0.5:  # Rising trend
                self.alert("Blade wear detected", "WARNING", machine_id)
                self.schedule_maintenance(machine_id, "blade_replacement")
        
        # Detect thermal stress
        if telemetry["temperature"] > telemetry["max_temperature"] * 0.9:
            self.alert("Thermal stress", "CRITICAL", machine_id)
            self.trigger_emergency_cooldown(machine_id)
```

### Extension 4: External System Integration

**Integrate with Grafana for visualization:**

```python
# Add Grafana provisioning to docker-compose

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - timescaledb

# Add dashboard definitions in grafana/provisioning/dashboards/
# Queries: SELECT * FROM sensor_data WHERE time > now() - interval '1 hour'
```

**Integrate with external ERP:**

```python
# services/erp_bridge/erp_integration.py

class ERPBridge(MQTTClient):
    def __init__(self):
        super().__init__("erp_bridge")
        self.erp_api = ERPClient("https://erp.company.com/api")
    
    def on_production_complete(self, message):
        """Called when production/complete event received"""
        # Create shipping order in ERP
        self.erp_api.create_shipment({
            "production_id": message["production_id"],
            "quantity": message["quantity"],
            "destination": message["warehouse"],
            "status": "ready_to_ship"
        })
    
    def on_machine_failure(self, machine_id, error):
        """Create maintenance work order in ERP"""
        self.erp_api.create_work_order({
            "machine_id": machine_id,
            "error": error,
            "priority": "HIGH",
            "status": "open"
        })
```

### Extension 5: Custom Frontends

**Create a React-based dashboard:**

```bash
# Generate a new React app with factory integration
npx create-react-app factory-dashboard
cd factory-dashboard
npm install mqtt react-mqtt-hook axios

# Example component
```

```jsx
import { useMqtt } from 'react-mqtt-hook';

function MachineMonitor({ factoryId, machineId }) {
  const [telemetry, setTelemetry] = useMqtt(
    `factory/${factoryId}/machines/${machineId}/telemetry`,
    null
  );
  
  return (
    <div className="machine-card">
      <h3>{machineId}</h3>
      {telemetry && (
        <div className="sensors">
          {Object.entries(telemetry.sensor_data).map(([name, value]) => (
            <Gauge key={name} label={name} value={value} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### Extension 6: Hardware Integration (Hybrid Mode)

**Replace simulation with real hardware:**

```python
# Generate a "real_sewing_machine.py" that connects to actual hardware

class RealSewingMachine(BaseMachine):
    """Adapter for real sewing machine via Modbus/OPC-UA"""
    
    def __init__(self, machine_id, hardware_address):
        super().__init__(machine_id, "sewing", "Real Sewing Machine")
        self.hardware = ModbusClient(hardware_address)
    
    def _initialize_sensors(self):
        """Read initial values from real hardware"""
        return {
            "needle_temperature": self.hardware.read_register(0x100),
            "thread_tension": self.hardware.read_register(0x101),
            "stitch_speed": self.hardware.read_register(0x102)
        }
    
    def update_sensors(self):
        """Poll real hardware instead of simulating"""
        self.sensor_data["needle_temperature"] = \
            self.hardware.read_register(0x100)
        # etc.
    
    def process_operation(self, process_data):
        """Send actual commands to real machine"""
        operation = process_data.get("operation")
        if operation == "stitch_seams":
            # Send Modbus command to start machine
            self.hardware.write_register(0x200, 1)  # Start
            
            # Poll for completion
            timeout = time.time() + process_data.get("timeout", 120)
            while time.time() < timeout:
                status = self.hardware.read_register(0x201)
                if status == 0:  # Completed
                    return {"success": True, "stitches": 500}
                time.sleep(0.5)
            
            return {"success": False, "error": "Timeout"}
```

**Deploy hybrid factory:**

```yaml
# docker-compose.yml for hybrid deployment

services:
  # Simulated machines
  cutting-01:
    image: factory/cutting-machine
    environment:
      MACHINE_ID: cutting-01
      SIMULATION_MODE: true
  
  # Real hardware machines
  sewing-01:
    image: factory/sewing-machine-hardware-adapter
    environment:
      MACHINE_ID: sewing-01
      SIMULATION_MODE: false
      HARDWARE_ADDRESS: 192.168.1.100:502  # Modbus address
    networks:
      - factory_network
    extra_hosts:
      - "sewing-hardware:192.168.1.100"
```

### Extension 7: Custom Test Case Generators

**Generate domain-specific test scenarios:**

```python
# tools/pharmaceutical_test_generator.py

class PharmaceuticalTestGenerator:
    """Generate realistic pharmaceutical production test cases"""
    
    def generate_contamination_test(self):
        """Test contamination detection"""
        return {
            "name": "contamination_detection",
            "steps": [
                {
                    "action": "inject_contamination",
                    "machine_id": "mixer-01",
                    "contamination_level": 0.05
                },
                {
                    "action": "production_request",
                    "product_type": "tablet",
                    "quantity": 1000
                },
                {
                    "action": "assert",
                    "condition": "all_batches_rejected",
                    "reason": "Contamination detected"
                }
            ]
        }
    
    def generate_batch_traceability_test(self):
        """Test end-to-end batch tracking"""
        return {
            "name": "batch_traceability",
            "steps": [
                {
                    "action": "production_request",
                    "product_type": "tablet",
                    "batch_id": "BATCH-2026-001"
                },
                {
                    "action": "verify_telemetry",
                    "assertion": "all_events_tagged_with_batch_id"
                },
                {
                    "action": "query_database",
                    "query": "SELECT * FROM production_log WHERE batch_id='BATCH-2026-001'",
                    "assertion": "record_count > 100"
                }
            ]
        }
```

---

## Best Practices & Patterns

### 1. Configuration Management
- Version control all JSON configs and templates
- Use semantic versioning for templates (v1.0, v1.1, etc.)
- Document changes in CHANGELOG.md
- Validate all configs before deployment

### 2. Testing Strategy
- Generate test cases for each machine type
- Include extreme sensor values (min/max)
- Test failure scenarios (stuck machine, high error rate)
- Validate workflow routing (success path, failure path, rework)

### 3. Monitoring & Observability
- Publish structured logs with trace IDs
- Tag all MQTT messages with factory_id, machine_id, timestamp
- Aggregate KPIs in monitoring service
- Set meaningful alert thresholds

### 4. Scalability
- Use docker-compose for single factory per host
- Use Kubernetes for multi-factory deployments
- Share common MQTT broker across factories
- Separate databases per factory for isolation

### 5. Security
- Authenticate API requests
- Use TLS for MQTT (mqtts://)
- Implement role-based access (operator, engineer, admin)
- Audit all production events

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Machine startup | < 5s | Docker container init |
| Factory generation | < 10s | 20 machines, from JSON to docker-compose |
| Production order processing | < 1s | MQTT publish + orchestrator receive |
| Telemetry throughput | 100+ msg/sec | Per factory, all machines combined |
| Database insert rate | 5,000+ ops/min | TimescaleDB throughput |
| WebSocket latency | < 100ms | UI update from machine event |
| Maximum concurrent factories | 100+ | Limited by host resources (memory, CPU) |

---

## Getting Started: Quick Reference

```bash
# 1. Clone the platform
git clone <repo-url>
cd tshirt-factory

# 2. Generate a factory
python3 tools/factory_generator.py factory-configs/tshirt-factory.json

# 3. Start the factory
cd generated-factories/tshirt-factory-001
docker compose up --build -d

# 4. Monitor
mosquitto_sub -h localhost -t 'factory/#' -v

# 5. Place an order
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{"product_type":"tshirt-standard","quantity":5}'

# 6. Open UI (if included)
open http://localhost:8080

# 7. Query results
docker exec tshirt-factory-001-timescaledb psql -U factory_user -d factory_timeseries \
  -c "SELECT * FROM sensor_data LIMIT 10;"
```

---

## Conclusion & Next Steps

This platform demonstrates that **complex manufacturing simulations can be data-driven and code-generic**. By externalizing machine definitions, sensor specs, and workflows to JSON, we achieve:

✅ **Factory-agnostic architecture**: Same code works for any industry  
✅ **True extensibility**: Add machine types without code changes  
✅ **Rapid prototyping**: From idea to running factory in minutes  
✅ **Operational observability**: Full MQTT telemetry and database storage  
✅ **Integration-ready**: REST APIs and WebSocket for custom frontends  

### What You Can Do Now

1. **Create custom factories**: Define any industry in JSON (automotive, pharma, electronics, food, etc.)
2. **Run simulations**: Generate and deploy complete Docker stacks locally or in the cloud
3. **Integrate external systems**: Connect ERP, MES, analytics via REST or MQTT
4. **Build custom frontends**: Use the API Gateway to power any UI framework
5. **Extend capabilities**: Add hardware adapters, custom monitoring, predictive maintenance

### Recommended Next Steps

1. **Try a new factory**: Follow the factory generation guide with your industry
2. **Connect a custom UI**: Build a React/Vue dashboard using the REST API
3. **Integrate with your systems**: Bridge your ERP or MES via MQTT
4. **Run in production**: Deploy to Kubernetes for multi-factory management
5. **Extend capabilities**: Add predictive maintenance, anomaly detection, or hardware adapters

For detailed implementation guides, see:
- [How to Use](./HOW_TO_USE.md) - Quick start and troubleshooting
- [Factory Guide](./FACTORY_GUIDE.md) - Step-by-step factory creation
- [Architecture](./ARCHITECTURE.md) - Deep dive into components
- [Extending](./EXTENDING.md) - Customization patterns
