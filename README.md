# Universal Factory Simulation Platform

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
open http://localhost:4200  # (after running: cd customer-order-ui && ng serve)
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
- [x] All 9 services running (machines, orchestrator, monitoring, databases)
- [x] MQTT messaging working (messages flowing: machines → broker → monitoring)
- [x] Data persistence (PostgreSQL & TimescaleDB)
- [x] Wildcard subscriptions with callback routing
- [x] Docker-based deployment
- [x] Multi-factory support

### 🎯 Included Frontends
- [x] T-Shirt Customizer (Angular + Material + Tailwind)
- [x] Vehicle Customizer (HTML/JS + Tailwind)

### 📚 Documentation
- **README.md** (this file) - Overview and quick start
- **docs/ARCHITECTURE.md** - Detailed component architecture
- **docs/EXTENDING.md** - Creating custom factories
- **docs/MQTT_GUIDE.md** - MQTT topics and message formats
- **docs/API_REFERENCE.md** - REST API endpoints

---

## 📖 Documentation

### For Quick Start
👉 See the **Quick Start** section above

### For Understanding Architecture
👉 **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**
- Three-layer system design
- Data flow diagrams
- Component interactions
- Service lifecycle

### For Creating Custom Factories
👉 **[docs/EXTENDING.md](docs/EXTENDING.md)**
- Add new machine types
- Create custom factory configurations
- Extend frontends
- Modify workflows

### For MQTT Integration
👉 **[docs/MQTT_GUIDE.md](docs/MQTT_GUIDE.md)**
- Topic structure
- Message formats
- Subscription patterns
- Integration examples

### For API Development
👉 **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)**
- REST endpoints
- WebSocket usage
- Error handling
- Authentication (if configured)

---

## 🔧 Common Commands

### Generate a Factory
```bash
python3 tools/factory_generator.py factory-configs/tshirt-factory.json
python3 tools/factory_generator.py factory-configs/automotive-assembly-plant.json
```

### Run Generated Factory
```bash
cd generated-factories/tshirt-factory-001
docker compose up --build
```

### Monitor Machine Activity (MQTT)
```bash
mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v
```

### View Database
```bash
# PostgreSQL
docker exec -it tshirt-factory-001-postgres psql -U factory_user -d tshirt_factory

# Query machine data
SELECT * FROM machine_status_log ORDER BY timestamp DESC LIMIT 10;
```

### Logs
```bash
# Monitor specific service
docker logs -f tshirt-factory-001-monitoring
docker logs -f tshirt-factory-001-orchestrator
docker logs -f cutting-01
```

### Stop Factory
```bash
cd generated-factories/tshirt-factory-001
docker compose down
```

---

## 🏪 File Structure

```
tshirt-factory/
├── README.md                      ← You are here
├── docs/                          ← Detailed documentation
│   ├── ARCHITECTURE.md            (System design)
│   ├── EXTENDING.md               (Custom factories)
│   ├── MQTT_GUIDE.md              (Message topics)
│   └── API_REFERENCE.md           (REST/WebSocket APIs)
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
3. **Creating custom factory?** → Follow [docs/EXTENDING.md](docs/EXTENDING.md)
4. **Integrating with external system?** → Check [docs/MQTT_GUIDE.md](docs/MQTT_GUIDE.md)

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
