# Universal Factory Simulation Platform

_Last updated: 2026-01-13_

> **Generate ANY factory type (t-shirts, automotive, electronics, pharma, food) through JSON configuration. No coding required. 15-minute setup.**

---

## 🚀 What This Is

A **zero-code, JSON-driven IoT manufacturing simulation platform** that:

- ✅ Defines machines, sensors, and operations in JSON
- ✅ Generates complete Python + Docker factory simulations automatically
- ✅ Runs realistic IoT workflows with MQTT message flows
- ✅ Provides REST APIs and customer-facing frontends
- ✅ Persists telemetry data to PostgreSQL/TimescaleDB

**Supports**: T-shirt manufacturing, automotive assembly, electronics production, pharmaceutical processing, food processing — or **ANY industry** you define.

---

## 📚 Documentation

**Read in order:**

1. **[How to Use](./docs/HOW_TO_USE.md)** - Quick start, run, monitor, troubleshoot
2. **[Factory Guide](./docs/FACTORY_GUIDE.md)** - Create custom factories step-by-step
3. **[Architecture](./docs/ARCHITECTURE.md)** - System design, data flow, components
4. **[Extending](./docs/EXTENDING.md)** - Add machines, services, or frontends
5. **[Medium Article](./docs/MEDIUM_ARTICLE.md)** - High-level overview and rationale

**Resources:**
- [machine-templates/](./machine-templates/) - 7 pre-built machine types with sensor specs
- [factory-configs/](./factory-configs/) - 5 example factories ready to use
- [workflows/](./workflows/) - Production sequences and routing logic
- [schemas/](./schemas/) - JSON validation schemas

---

## ⚡ Essential Commands

### Generate Factory
```bash
python3 tools/factory_generator.py factory-configs/tshirt-factory.json
```

### Start & Stop
```bash
# Start
cd generated-factories/tshirt-factory-001
docker compose up --build -d

# Stop
docker compose down
```

### Place Order
```bash
curl -X POST http://localhost:5000/production \
  -H "Content-Type: application/json" \
  -d '{"product_type":"tshirt-standard","quantity":5}'
```

### Monitor
```bash
# View all logs
docker compose logs -f

# Monitor MQTT messages
mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v

# Check service status
docker compose ps

# View orchestrator logs
docker compose logs -f orchestrator
```

### Database Queries
```bash
# Connect to PostgreSQL
docker exec -it tshirt-factory-001-postgres psql -U factory_user -d tshirt_factory

# Query recent machine status
SELECT * FROM machine_status_log ORDER BY timestamp DESC LIMIT 10;
```

### Validation
```bash
# Validate JSON config
python3 -m json.tool factory-configs/your-factory.json

# Check generated test cases
jq '.test_cases | length' generated-factories/tshirt-factory-001/test_cases.json
```

---

## 🔍 Key MQTT Topics

```
factory/{factory-id}/
├─ machines/{machine-id}/
│  ├─ telemetry          # Sensor data (published every 5s)
│  ├─ status             # Machine state (idle/busy/error)
│  └─ command            # Control commands (start/stop)
├─ production/
│  ├─ request            # New orders
│  ├─ status             # Production progress
│  └─ complete           # Finished orders
└─ monitoring/
   ├─ metrics            # Real-time KPIs
   └─ command            # Monitoring control
```

---

## 🎯 Key Innovation: Template-Based Sensor Extraction

**Before**: Sensor ranges were hardcoded in test generation code (generic, factory-specific).

**After (Phase 3)**: Sensor ranges are extracted from machine templates (accurate, factory-agnostic, infinite extensibility).

```
Machine Templates (JSON)        → Define: blade_temperature (20-45°C), etc.
                                    ↓
Generator loads templates    → Extract sensor specs from JSON
                                    ↓
Test cases use real ranges    → Tests are accurate for each factory
                                    ↓
Same code works everywhere    → Add machines with only JSON files
```

**Result**: 
- ✅ **Factory-Agnostic** - Same code for t-shirt, auto, pharma, etc.
- ✅ **Accurate** - Sensor ranges match actual capabilities
- ✅ **Extensible** - Add machine types without code changes
- ✅ **Production-Ready** - Fully tested and documented

---

## ⚡ 5-Minute Quick Start

### Option 1: T-Shirt Factory (Recommended First)

```bash
# 1. Generate factory from configuration
python3 tools/factory_generator.py factory-configs/tshirt-factory.json

# 2. Start all services (MQTT, machines, databases, orchestrator)
cd generated-factories/tshirt-factory-001
docker compose up --build

# 3. Start API gateway (in another terminal)
cd factory_ui_simulator
python3 app.py

# 4. Open customer frontend
open http://localhost:8080  # (Docker frontend, runs automatically with factory-simulator)
```

### Option 2: Other Factories

```bash
# Generate any factory
python3 tools/factory_generator.py factory-configs/automotive-assembly-plant.json
python3 tools/factory_generator.py factory-configs/electronics-factory.json

# Start factory
cd generated-factories/{factory-id}
docker compose up --build

# Monitor with MQTT
mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v
```

---

## 📦 Factory Library

| Factory Type | Machines | Workflows | Config File |
|-------------|----------|-----------|------------|
| **T-Shirt** | Cutting, Sewing, QC, Packaging | Standard, Premium, Custom Print | `tshirt-factory.json` |
| **Automotive** | Stamping, Welding, Painting, Assembly, Inspection | Sedan, SUV | `automotive-assembly-plant.json` |
| **Electronics** | PCB Assembly, Soldering, Testing, Packaging | Smartphone, IoT | `electronics-factory.json` |
| **Pharma** | Blending, Drying, Tablet Press, Coating, Inspection | Standard, Extended Release | `pharmaceutical-plant.json` |
| **Food** | Mixing, Baking, Cooling, QC, Packaging | Cookies, Bread | `food-processing-plant.json` |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Configuration Layer                                    │
│  ├─ factory-configs/              (5 factory examples) │
│  └─ machine-templates/            (7 machine templates)│
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Generation Layer                                       │
│  └─ tools/factory_generator.py   (Auto-code generation)│
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Generated Factory (Docker Services)                    │
│  ├─ Orchestrator      (Workflow coordinator)           │
│  ├─ Machines          (Individual containers, 1 each)  │
│  ├─ PostgreSQL        (Production data)                │
│  ├─ TimescaleDB       (Time-series telemetry)          │
│  └─ MQTT Broker       (Message bus)                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼ MQTT Topics
┌─────────────────────────────────────────────────────────┐
│  API Gateway & Frontends                                │
│  ├─ REST API          (factory_ui_simulator)       │
│  ├─ Customer Frontend  (customer-order-ui, Angular)    │
│  └─ Vehicle Frontend  (vehicle-customizer, HTML/JS)   │
└─────────────────────────────────────────────────────────┘
```

### Key Components

**1. Configuration Layer** (`factory-configs/`, `machine-templates/`)
- JSON-based, no code required
- Validates against schemas in `schemas/`
- 5 complete factory examples + 7 machine templates

**2. Factory Generator** (`tools/factory_generator.py`)
- Reads JSON config
- Generates Python machine classes, orchestrator, docker-compose
- Creates ready-to-run `generated-factories/{factory-id}/`

**3. Generated Factory Services**
- **Orchestrator**: Coordinates production workflows via MQTT
- **Machine Services**: Each machine is a container that:
  - Updates sensors every 2 seconds
  - Publishes telemetry to MQTT every 5 seconds
  - Executes operations based on orchestrator commands
- **PostgreSQL**: Stores production orders, machine telemetry
- **TimescaleDB**: Time-series database for sensor data
- **MQTT Broker** (Mosquitto): Central message bus

**4. API Gateway** (`factory_ui_simulator/`)
- REST API for placing orders and querying machine status
- WebSocket bridge for real-time MQTT data to browsers
- Flask-based, runs on `localhost:5001`

**5. Customer Frontends**
- **customer-order-ui** (Angular): Design and order custom t-shirts
- **vehicle-customizer** (HTML/JS): Configure vehicles

---

## 🔄 How It Works

### Data Flow Example (T-Shirt Production)

```
1. Customer Frontend
   └─ User designs t-shirt → Click "Place Order"

2. REST API
   └─ POST /production { size, color, text } → Sent to MQTT

3. MQTT Broker
   └─ Topic: factory/tshirt-factory-001/production/request
   └─ Orchestrator subscribes and receives order

4. Orchestrator
   └─ Creates workflow: cutting → sewing → QC → packaging

5. Machine Services
   ├─ cutting-01 receives "start" command
   │  └─ Executes for 10-30 seconds
   │  └─ Publishes status/telemetry every 5s
   │  └─ Data stored in PostgreSQL
   ├─ sewing-01 receives "start" after cutting done
   ├─ qualitycheck-01 validates product
   └─ packaging-01 prepares for shipment

6. Real-Time Display
   └─ Frontend receives WebSocket updates from MQTT
   └─ Shows product status in real-time
```

### MQTT Topic Structure (ISA-95 Compliant)

```
factory/{factory-id}/
├─ machines/{machine-id}/
│  ├─ telemetry          (Sensor data: temperature, speed, etc.)
│  ├─ status             (Operational state: idle, busy, error)
│  └─ command            (Orchestrator → Machine: start, stop)
├─ production/
│  ├─ request            (Customer → Orchestrator: new order)
│  ├─ status             (Orchestrator → All: production state)
│  └─ complete           (Orchestrator: order finished)
└─ monitoring/
   ├─ metrics            (Real-time KPIs)
   └─ command            (Control monitoring service)
```

---

## 🛠️ System Status & Features

### ✅ Production Ready
- [x] Template-driven factory generation (zero-code)
- [x] 5 pre-built factory types + 7 machine templates
- [x] MQTT-based messaging (ISA-95 compliant topics)
- [x] PostgreSQL & TimescaleDB persistence
- [x] Docker Compose deployment
- [x] Multi-factory support
- [x] Real-time telemetry & monitoring

### 🎯 Included
- Customer frontends (Angular + HTML/JS)
- REST API gateway with WebSocket
- Automated test case generation
- Production workflow engine
- Monitoring & alerting service

---

## 🏪 File Structure

```
tshirt-factory/
├── README.md                      ← You are here
├── docs/                          ← Documentation
│   ├── HOW_TO_USE.md              (Quick start & troubleshooting)
│   ├── FACTORY_GUIDE.md           (Create custom factories)
│   ├── ARCHITECTURE.md            (System design)
│   ├── EXTENDING.md               (Customization)
│   ├── MEDIUM_ARTICLE.md          (Overview)
│   └── archive/                   (Historical docs)
│
├── factory-configs/               ← Factory definitions (JSON)
│   ├── tshirt-factory.json
│   ├── automotive-assembly-plant.json
│   ├── electronics-factory.json
│   ├── pharmaceutical-plant.json
│   └── food-processing-plant.json
│
├── machine-templates/             ← Reusable machine types (JSON)
│   ├── cutting-machine.json
│   ├── sewing-machine.json
│   ├── packaging-machine.json
│   ├── quality-check-machine.json
│   ├── welding-machine.json
│   ├── pcb-assembly.json
│   └── tablet-press.json
│
├── schemas/                       ← JSON validation schemas
│   ├── factory-config-schema.json
│   └── machine-template-schema.json
│
├── tools/                         ← Code generation tools
│   ├── factory_generator.py       (Main generator)
│   └── create_machine.py          (Helpers)
│
├── shared/                        ← Shared Python modules
│   ├── mqtt_client.py             (MQTT client with wildcard support)
│   ├── base_machine.py            (Machine base class)
│   ├── database.py                (PostgreSQL & TimescaleDB)
│   ├── workflow_engine.py         (Workflow execution)
│   ├── cloud_publisher.py         (Cloud integration)
│   └── config.py                  (Configuration management)
│
├── monitoring-service/            ← Monitoring service (template)
│   ├── monitoring_service.py      (Service code)
│   └── Dockerfile
│
├── production-orchestrator/       ← Orchestrator service (template)
│   ├── orchestrator.py            (Service code)
│   └── Dockerfile
│
├── workflows/                     ← Workflow templates (JSON)
│   ├── tshirt-standard.json
│   ├── premium-tshirt.json
│   ├── custom-embroidery.json
│   └── ... (more)
│
├── mqtt/                          ← MQTT configuration
│   └── mosquitto.conf
│
├── factory_ui_simulator/      ← API Gateway & Monitoring Dashboard
│  ├── app.py                     (Flask app)
│  ├── requirements.txt
│  ├── static/                    (Web assets)
│  └── templates/                 (HTML)
│
├── customer-order-ui/             ← Customer Frontend (Angular)
│  ├── src/
│  ├── package.json
│  └── ... (Angular project)
│
├── vehicle-customizer/            ← Vehicle Frontend (HTML/JS)
│   └── src/
│
└── generated-factories/           ← Generated factory instances
    ├── tshirt-factory-001/        (Complete running factory)
    ├── automotive-plant-001/
    └── ... (more)
```

---

## 🚀 Next Steps

1. **First time?** → Follow the [Quick Start](#-5-minute-quick-start)
2. **Want to understand it?** → Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. **Creating custom factory?** → Follow [docs/FACTORY_GUIDE.md](docs/FACTORY_GUIDE.md)
4. **Extending the system?** → Check [docs/EXTENDING.md](docs/EXTENDING.md)

---

## 📝 Requirements

- **Docker & Docker Compose** (v2+)
- **Python 3.9+** (for generation)
- **Node.js 18+** (for frontends)
- **MQTT client** (optional, for monitoring): `mosquitto-clients`

### Install on macOS
```bash
brew install docker-compose python node mosquitto-clients
```

### Install on Ubuntu 22.04
```bash
bash run_on_ubuntu_2204.sh
```

---

## 🐛 Troubleshooting

### Services not starting?
```bash
# Check logs
docker compose logs -f

# Restart all services
docker compose restart

# Full rebuild
docker compose down -v
docker compose up --build
```

### MQTT not receiving messages?
```bash
# Monitor broker
mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v

# Check if machines are running
docker compose ps
```

### Database connection errors?
```bash
# Check PostgreSQL
docker exec -it tshirt-factory-001-postgres psql -U factory_user -d tshirt_factory -c "SELECT 1;"

# Check TimescaleDB
docker exec -it tshirt-factory-001-timescaledb psql -U factory_user -d factory_timeseries -c "SELECT 1;"
```

---

## 📄 License & Credits

Built with ❤️ for IoT manufacturing simulations.

**Technology Stack**:
- Python (Paho MQTT, Flask)
- PostgreSQL & TimescaleDB
- Docker & Docker Compose
- Angular & Material Design
- Mosquitto MQTT Broker

---

## 📞 Support

- **Docs**: See `docs/` folder
- **Examples**: Check `factory-configs/` and `generated-factories/`
- **Issues**: Check logs with `docker compose logs -f`

---

**Happy Manufacturing! 🏭**
