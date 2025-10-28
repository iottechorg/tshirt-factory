# System Overview

## 🎯 What Is This Platform?

A **universal JSON-based factory simulation platform** that generates complete IoT-enabled manufacturing simulations for **any industry** in minutes—no coding required.

---

## 📊 System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    USER LAYER                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Customer Frontends              Monitoring Dashboard        │
│  ├─ tshirt-customizer  (Angular) ├─ simple_factory_simulator│
│  └─ vehicle-customizer (HTML/JS) └─ (Flask + Tailwind CSS)  │
│                                                               │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼ HTTP/MQTT
┌──────────────────────────────────────────────────────────────┐
│                   API GATEWAY LAYER                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  simple_factory_simulator (Flask API)                        │
│  ├─ POST /production          (Place orders)                │
│  ├─ GET  /machines            (Machine status)              │
│  ├─ GET  /production          (Order queue)                 │
│  └─ WebSocket Bridge          (Real-time MQTT → Browser)   │
│                                                               │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼ MQTT
┌──────────────────────────────────────────────────────────────┐
│                 MQTT BROKER (Mosquitto)                      │
├──────────────────────────────────────────────────────────────┤
│  Topics (ISA-95 Compliant):                                  │
│  ├─ factory/{factory-id}/machines/{machine-id}/telemetry    │
│  ├─ factory/{factory-id}/machines/{machine-id}/status       │
│  ├─ factory/{factory-id}/production/request                 │
│  └─ factory/{factory-id}/production/status                  │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│              FACTORY SERVICES (Docker Containers)            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Generated Factory: {factory-id}                             │
│  ├─ Orchestrator          (Workflow coordinator)            │
│  ├─ Machine Services      (Individual machines)             │
│  │  ├─ cutting-01         (Publish telemetry, execute ops) │
│  │  ├─ sewing-01                                            │
│  │  ├─ qualitycheck-01                                      │
│  │  └─ packaging-01                                         │
│  ├─ PostgreSQL            (Production data, machine state)  │
│  └─ MQTT Broker           (Per-factory instance)            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Three-Layer System

### Layer 1: Configuration (JSON)

**Purpose**: Define factories without coding

**Components**:
- **Machine Templates** (`machine-templates/*.json`)
  - Reusable machine type definitions
  - Sensors, operations, failure modes
  - 7 pre-built templates (cutting, sewing, welding, PCB, etc.)

- **Factory Configurations** (`factory-configs/*.json`)
  - Complete factory definitions
  - Machine instances, workflows, production config
  - 5 pre-built factories (t-shirt, automotive, electronics, pharma, food)

**Example**:
```json
{
  "factory_id": "tshirt-factory-001",
  "machines": [...],
  "workflows": [...],
  "production_config": {...}
}
```

### Layer 2: Generation (Python Tool)

**Purpose**: Convert JSON configs into running code

**Tool**: `tools/factory_generator.py`

**Process**:
1. Load and validate JSON schemas
2. Generate Python machine classes
3. Generate workflow orchestrator
4. Generate docker-compose.yml
5. Generate documentation (README.md)

**Command**:
```bash
python3 tools/factory_generator.py factory-configs/tshirt-factory.json
```

**Output**: `generated-factories/tshirt-factory-001/`
- Complete Docker-based factory
- All services ready to run
- Includes databases, MQTT broker, machines

### Layer 3: Execution (Docker Services)

**Purpose**: Run the simulated factory

**Services per Factory**:
- **Orchestrator**: Manages production workflows
- **Machine Services**: Individual machine containers (1 per machine)
- **PostgreSQL**: Stores production orders, machine telemetry
- **MQTT Broker**: Pub/sub message bus (Mosquitto)

**Communication**:
- Machines → MQTT (publish telemetry every 5s)
- Orchestrator → MQTT (coordinate workflows)
- External → MQTT (send production requests)
- Machines → PostgreSQL (persist data)

**Command**:
```bash
cd generated-factories/tshirt-factory-001
docker compose up --build
```

---

## 🔄 Data Flow

### Production Order Flow

```
Customer Frontend (tshirt-customizer)
    │
    ├─ User configures product
    │  (size, color, text)
    │
    └─ Click "Place Order"
         │
         ▼ HTTP POST
simple_factory_simulator API
    │
    ├─ Validate order
    ├─ Add to queue
    │
    └─ Publish to MQTT
         │
         ▼ MQTT: factory/{factory-id}/production/request
Orchestrator (Workflow Coordinator)
    │
    ├─ Parse workflow steps
    ├─ Assign to machines
    │
    └─ Coordinate execution
         │
         ▼ MQTT: factory/{factory-id}/machines/{machine-id}/operation
Machine Services (cutting → sewing → QC → packaging)
    │
    ├─ Execute operation
    ├─ Update sensors
    ├─ Check failure modes
    │
    └─ Publish telemetry & status
         │
         ▼ MQTT: factory/{factory-id}/machines/{machine-id}/telemetry
Database (PostgreSQL)
    │
    └─ Store: production_orders, machine_telemetry, workflows
```

### Real-Time Telemetry Flow

```
Machine Service
    │
    ├─ Update sensors (every 5s)
    │  - random_walk
    │  - sine_wave
    │  - conditional
    │
    └─ Publish telemetry
         │
         ▼ MQTT: factory/{factory-id}/machines/{machine-id}/telemetry
         │
         ├─────────────────┬──────────────────┐
         │                 │                  │
         ▼                 ▼                  ▼
  PostgreSQL      MQTT Subscribers    WebSocket Bridge
  (persist)       (monitoring)        (browser clients)
                                            │
                                            ▼
                                   Dashboard Updates
                                   (simple_factory_simulator)
```

---

## 📦 What's Generated

When you run `factory_generator.py`, you get:

### Directory Structure

```
generated-factories/{factory-id}/
├── docker-compose.yml          # Container orchestration
├── README.md                   # Factory-specific docs
├── machines/                   # Generated machine code
│   ├── cutting/
│   │   ├── machine.py         # Machine logic
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── sewing/
│   ├── qualitycheck/
│   └── packaging/
├── workflows/                  # Workflow definitions
│   ├── standard-tshirt-production.json
│   ├── premium-tshirt-production.json
│   └── custom-print-tshirt.json
└── database/
    └── init.sql               # Database schema
```

### Generated Code Features

**Machine Services**:
- Sensor simulation with configurable behaviors
- Operation execution with failure modes
- MQTT telemetry publishing
- Database persistence
- Health checks and monitoring

**Orchestrator**:
- Workflow parsing and execution
- Step coordination across machines
- Quality gates and conditional logic
- Retry mechanisms
- Progress tracking

**Docker Compose**:
- All services configured
- Network isolation per factory
- Volume mounts for persistence
- Port mapping (unique per factory)
- Health checks and dependencies

---

## 🎨 Frontend Integration

### Pattern: Configuration + Preview

All customer frontends follow this pattern:

```
┌─────────────────────────────────────────┐
│         Customer Frontend App            │
├──────────────────┬──────────────────────┤
│                  │                       │
│ Configuration    │   Preview Panel       │
│ Panel            │                       │
│                  │                       │
│ - Product type   │ - Visual preview      │
│ - Features       │ - Price calculation   │
│ - Options        │ - Configuration       │
│ - Customization  │   summary             │
│                  │ - Factory status      │
│ [Place Order] ───┼──→ [Monitor] ────────┤
│                  │                       │
└──────────────────┴───────────────────────┘
          │                       │
          ▼                       ▼
    POST /production      GET /machines
    (simple_factory_      (simple_factory_
     simulator API)        simulator API)
```

### Example Frontends

**tshirt-customizer** (Angular):
- Technology: Angular + Angular Material + Tailwind CSS
- Features: Size, color, custom text selection
- Workflows: Standard, Premium, Custom print
- Status: ✅ Production ready

**vehicle-customizer** (HTML/JS):
- Technology: Vanilla JavaScript + Tailwind CSS
- Features: Vehicle type, color, premium features
- Workflows: Sedan, SUV production
- Status: ✅ Production ready

### Creating New Frontends

See [FRONTEND_REPLICATION_GUIDE.md](FRONTEND_REPLICATION_GUIDE.md) for:
- Step-by-step instructions
- HTML/JavaScript template
- Angular template
- API integration patterns
- Examples for all factory types

---

## 🔧 Configuration Capabilities

### Machine Templates

Define machine behaviors via JSON:

```json
{
  "machine_type": "cutting",
  "sensors": [
    {
      "name": "blade_temperature",
      "type": "float",
      "range": {"min": 20.0, "max": 45.0},
      "update_behavior": {
        "type": "random_walk",
        "parameters": {"variation": 0.5}
      },
      "alert_conditions": [
        {
          "condition": "value > 40",
          "severity": "warning",
          "message": "High blade temperature"
        }
      ]
    }
  ],
  "operations": [
    {
      "name": "cut_fabric",
      "duration": {"type": "fixed", "value": 5.0},
      "failure_modes": [
        {"type": "random", "probability": 0.02},
        {
          "type": "conditional",
          "probability": 0.15,
          "condition": "blade_temperature > 40"
        }
      ]
    }
  ]
}
```

**Sensor Update Behaviors**:
- `random_walk`: Gradual random changes (realistic drift)
- `sine_wave`: Periodic oscillation (temperature cycles)
- `step`: Discrete state changes (label depletion)
- `conditional`: Value changes based on conditions

**Failure Modes**:
- `random`: Fixed probability failures
- `conditional`: Sensor-dependent failures
- Multiple failure modes per operation

### Factory Configurations

Define complete factories:

```json
{
  "factory_id": "tshirt-factory-001",
  "factory_name": "Smart T-Shirt Manufacturing Plant",
  "machines": [
    {
      "machine_id": "cutting-01",
      "machine_type": "cutting",
      "template_file": "machine-templates/cutting-machine.json"
    }
  ],
  "workflows": [
    {
      "workflow_id": "standard-tshirt-production",
      "steps": [
        {"machine_type": "cutting", "operation": "cut_fabric"},
        {"machine_type": "sewing", "operation": "sew_pieces"},
        {"machine_type": "quality_check", "operation": "inspect_quality"},
        {"machine_type": "packaging", "operation": "package_tshirt"}
      ]
    }
  ],
  "production_config": {
    "mode": "on-demand",
    "target_rate": {"value": 100, "unit": "tshirts_per_day"}
  }
}
```

**Workflow Features**:
- Sequential steps
- Parallel execution (automotive welding)
- Conditional steps (quality gates)
- Retry logic
- Multiple workflows per factory

**Production Modes**:
- `continuous`: Non-stop production
- `batch`: Fixed-size batches
- `on-demand`: Customer orders
- `scheduled`: Time-based production

---

## 🏭 Pre-Built Factories

### 1. T-Shirt Factory

**Industry**: Textile Manufacturing
**Machines**: 4 (Cutting, Sewing, Quality Check, Packaging)
**Workflows**: 3 (Standard, Premium, Custom Print)
**Production**: On-demand, 100 tshirts/day
**Frontend**: ✅ Angular customer app (tshirt-customizer)
**MQTT Port**: 1883
**Config**: `factory-configs/tshirt-factory.json`

### 2. Automotive Assembly Plant

**Industry**: Automotive Manufacturing
**Machines**: 6 (Stamping, Welding×2, Painting, Assembly, Inspection)
**Workflows**: 2 (Sedan, SUV)
**Production**: Continuous, 50 vehicles/day, 3 shifts
**Frontend**: ✅ HTML/JS vehicle customizer
**MQTT Port**: 31883
**Config**: `factory-configs/automotive-assembly-plant.json`

### 3. Electronics Factory

**Industry**: Electronics Manufacturing
**Machines**: 6 (PCB Assembly×2, Soldering, Testing×2, Packaging)
**Workflows**: 2 (Smartphone PCB, IoT Sensor)
**Production**: Continuous, 500 units/hour
**Frontend**: ❌ (Create using guide)
**MQTT Port**: 32883
**Config**: `factory-configs/electronics-factory.json`

### 4. Pharmaceutical Plant

**Industry**: Pharmaceutical Manufacturing
**Machines**: 7 (Blending, Granulation, Drying, Tablet Press, Coating, Inspection, Packaging)
**Workflows**: 2 (Standard Coated, Immediate Release)
**Production**: Batch, 8 batches/day, GMP-compliant
**Frontend**: ❌ (Create using guide)
**MQTT Port**: 33883
**Config**: `factory-configs/pharmaceutical-plant.json`

### 5. Food Processing Plant

**Industry**: Food Manufacturing
**Machines**: 6 (Mixing, Baking, Cooling, Quality Check, Packaging, Labeling)
**Workflows**: 2 (Cookies, Bread)
**Production**: Batch, 20 batches/day
**Frontend**: ❌ (Create using guide)
**MQTT Port**: 34883
**Config**: `factory-configs/food-processing-plant.json`

---

## 📚 Documentation Map

### Getting Started
1. **[README.md](README.md)** - Start here (main entry point)
2. **[QUICK_START_GENERIC_FACTORY.md](QUICK_START_GENERIC_FACTORY.md)** - Create factory in 15 min
3. **[FRONTEND_REPLICATION_GUIDE.md](FRONTEND_REPLICATION_GUIDE.md)** - Create customer apps

### Platform Details
4. **[GENERIC_FACTORY_SYSTEM.md](GENERIC_FACTORY_SYSTEM.md)** - Complete platform docs
5. **[MIGRATION_TO_JSON_BASED.md](MIGRATION_TO_JSON_BASED.md)** - Migration history
6. **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** - This file (architecture overview)

### Component Documentation
7. **[simple_factory_simulator/README.md](simple_factory_simulator/README.md)** - API gateway docs
8. **[tshirt-customizer/README.md](tshirt-customizer/README.md)** - Angular frontend
9. **[vehicle-customizer/README.md](vehicle-customizer/README.md)** - HTML/JS frontend

### Schemas
10. **[schemas/machine-template-schema.json](schemas/machine-template-schema.json)** - Machine validation
11. **[schemas/factory-config-schema.json](schemas/factory-config-schema.json)** - Factory validation

---

## 🚀 Complete Usage Example

### Step 1: Generate T-Shirt Factory

```bash
# Generate from JSON config
python3 tools/factory_generator.py factory-configs/tshirt-factory.json

# Result: generated-factories/tshirt-factory-001/
```

### Step 2: Start Factory Services

```bash
# Navigate to generated factory
cd generated-factories/tshirt-factory-001

# Start all containers
docker compose up --build

# Verify services are running
docker ps
```

### Step 3: Start API Gateway

```bash
# In new terminal
cd simple_factory_simulator

# Configure for t-shirt factory
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export MQTT_WS_PORT=9001

# Start API
python3 app.py

# API available at: http://localhost:5001
```

### Step 4: Start Customer Frontend

```bash
# In new terminal
cd tshirt-customizer

# Install dependencies (first time only)
npm install

# Start development server
ng serve

# Open: http://localhost:4200
```

### Step 5: Place Order from Frontend

1. Open http://localhost:4200 in browser
2. Select size: M
3. Select color: Blue
4. Enter custom text: "Hello World"
5. Click "Place Order"
6. Order flows: Frontend → API → MQTT → Orchestrator → Machines

### Step 6: Monitor Production

```bash
# Watch MQTT messages
mosquitto_sub -h localhost -p 1883 -t "factory/#" -v

# Monitor API dashboard
open http://localhost:5001

# Check database
docker exec -it tshirt-factory-001-postgres psql -U factory_user -d tshirt_factory
SELECT * FROM production_orders;
```

---

## 🔍 Key Concepts

### ISA-95 Topics

MQTT topics follow industrial automation standards:

```
factory/{factory-id}/machines/{machine-id}/telemetry
factory/{factory-id}/machines/{machine-id}/status
factory/{factory-id}/machines/{machine-id}/alerts
factory/{factory-id}/production/request
factory/{factory-id}/production/status
factory/{factory-id}/workflows/{workflow-id}/status
```

### Sensor Simulation

Realistic sensor behaviors:

- **random_walk**: Gradual drift (e.g., temperature rising slowly)
- **sine_wave**: Periodic patterns (e.g., cooling cycles)
- **step**: Discrete changes (e.g., on/off states)
- **conditional**: Event-based changes (e.g., speed increases during operation)

### Failure Simulation

Two types of failures:

1. **Random Failures**: Fixed probability (e.g., 2% chance per operation)
2. **Conditional Failures**: Sensor-triggered (e.g., 15% chance if temperature > 40°C)

### Quality Gates

Workflows can include quality checks:

```json
{
  "step_id": "qc-check",
  "machine_type": "quality_check",
  "operation": "inspect_quality",
  "conditions": {
    "quality_threshold": 85,
    "on_pass": "continue",
    "on_fail": "retry_previous_step"
  }
}
```

---

## 🎯 Use Cases

| Use Case | Target Audience | Example |
|----------|----------------|---------|
| **IoT Education** | Students, developers | Learn MQTT, time-series DB, microservices |
| **Platform Testing** | IoT platform vendors | Test dashboards with realistic data |
| **Customer Demos** | Sales engineers | Show end-to-end IoT solutions |
| **Research** | Academics | Study manufacturing optimization |
| **Prototyping** | Product teams | Build digital twin proofs-of-concept |
| **Training** | Industrial engineers | Understand Industry 4.0 concepts |

---

## 🌟 What Makes This Unique

1. **Zero-Code Factory Creation** - Pure JSON, no programming
2. **Universal** - Works for ANY manufacturing domain
3. **Rapid Development** - 15-30 minutes per factory
4. **Production-Ready** - Docker, databases, MQTT built-in
5. **Realistic Simulation** - Authentic sensor behaviors and failures
6. **Frontend Pattern** - Replicable customer app architecture
7. **Scalable** - 1 machine to 100s, 1 factory to dozens
8. **IoT Standards** - ISA-95 MQTT topics, cloud-ready
9. **Open Source** - MIT licensed, fully extensible
10. **Well-Documented** - Comprehensive guides and examples

---

## 🔄 Version History

- **v1.0** (Phase 1.0): Hardcoded t-shirt factory
- **v1.5** (Phase 1.5): Flexible JSON workflows
- **v1.6** (Phase 1.6): Machine template generator
- **v1.7** (Phase 1.7): Multi-factory support
- **v2.0** (Phase 2.0): **Universal JSON-based platform** ← Current

---

## 🛠️ Technology Stack

### Backend
- **Python 3.9+**: Machine logic, orchestrator
- **MQTT (Mosquitto)**: Pub/sub messaging
- **PostgreSQL 13+**: Transactional data
- **Docker & Docker Compose**: Container orchestration

### Frontend
- **Angular 16+**: tshirt-customizer (full framework)
- **Vanilla JavaScript**: vehicle-customizer (no build step)
- **Flask**: simple_factory_simulator (API gateway)
- **Tailwind CSS**: Modern styling across all UIs

### IoT & Cloud
- **ISA-95**: Topic naming standards
- **AWS IoT Core**: Cloud integration ready
- **Azure IoT Hub**: Cloud integration ready
- **WebSocket**: Real-time browser updates

---

## 📊 Performance Characteristics

### Per Factory
- **Machines**: 1-100+ supported
- **Telemetry Rate**: 1-60 seconds per machine
- **MQTT Messages**: ~10-1000 msg/sec depending on machine count
- **Database Writes**: ~5-50 writes/sec
- **Memory**: ~100-500 MB per factory
- **CPU**: Minimal (< 5% on modern hardware)

### Scalability
- **Multiple Factories**: Run 10+ factories simultaneously
- **Long Running**: Tested for 24+ hours continuous operation
- **Data Volume**: Handles millions of telemetry records
- **Network**: Local or distributed deployment supported

---

## 🎓 Learning Path

1. **Beginner**: Start with tshirt-factory
   - Run pre-generated factory
   - Use tshirt-customizer frontend
   - Monitor MQTT messages

2. **Intermediate**: Create automotive factory
   - Generate from JSON
   - Build vehicle-customizer frontend
   - Customize workflows

3. **Advanced**: Design custom factory
   - Create new machine templates
   - Define complex workflows
   - Build custom frontend
   - Integrate with cloud IoT

---

## 📞 Support & Resources

- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: This repository's docs folder
- **Examples**: `factory-configs/` and `machine-templates/`
- **Discussions**: GitHub Discussions for Q&A

---

**Version 2.0** - Universal JSON-Based Factory Platform
**Last Updated**: October 2025
