# Universal Factory Simulation Platform

## 🏭 Create ANY Factory Type Through JSON Configuration

Generate complete factory simulations for **t-shirts, automotive, electronics, pharmaceuticals, food processing**, and ANY manufacturing domain in **15-30 minutes**.

---

## 🚀 What Is This?

A **zero-code factory simulation platform** that allows you to:

- ✅ Define machine types with sensors and operations (JSON)
- ✅ Configure complete factories with workflows (JSON)
- ✅ Auto-generate Python code, Docker configs, and workflows
- ✅ Run realistic IoT-enabled manufacturing simulations
- ✅ Create customer-facing frontends for ANY factory

**No programming required. Just JSON configuration.**

---

## ⚡ Quick Start (15 Minutes)

### Option 1: T-Shirt Factory (With Customer Frontend)

```bash
# Generate t-shirt factory
python3 tools/factory_generator.py factory-configs/tshirt-factory.json

# Start factory services
cd generated-factories/tshirt-factory-001
docker compose up --build

# In another terminal - Start API Gateway
cd simple_factory_simulator
export MQTT_PORT=1883
export MQTT_WS_PORT=9001
python3 app.py

# Open customer frontend
cd tshirt-customizer
npm install
ng serve
# Then open: http://localhost:4200
```

### Option 2: Automotive Factory

```bash
# Generate automotive factory
python3 tools/factory_generator.py factory-configs/automotive-assembly-plant.json

# Start factory services
cd generated-factories/automotive-plant-001
docker compose up --build

# In another terminal - Start API Gateway
cd simple_factory_simulator
export MQTT_PORT=31883
export MQTT_WS_PORT=39001
python3 app.py

# Open vehicle customizer
open vehicle-customizer/src/index.html
```

### Option 3: Other Factories (Electronics, Pharma, Food)

```bash
# Generate any factory
python3 tools/factory_generator.py factory-configs/electronics-factory.json
python3 tools/factory_generator.py factory-configs/pharmaceutical-plant.json
python3 tools/factory_generator.py factory-configs/food-processing-plant.json

# Start and monitor
cd generated-factories/{factory-id}
docker compose up --build

# Monitor MQTT
mosquitto_sub -h localhost -p {mqtt_port} -t "factory/#" -v
```

---

## 📦 What's Included

### 🏭 Pre-Built Factory Examples

| Factory Type | Machines | Workflows | Production Mode |
|-------------|----------|-----------|----------------|
| **T-Shirt Factory** | Cutting, Sewing, QC, Packaging | Standard, Premium, Custom | On-demand |
| **Automotive Plant** | Stamping, Welding (2x), Painting, Assembly, Inspection | Sedan, SUV | 50 vehicles/day |
| **Electronics Factory** | PCB Assembly (2x), Soldering, Testing (2x), Packaging | Smartphone, IoT Sensor | 500 units/hour |
| **Pharmaceutical Plant** | Blending, Granulation, Drying, Tablet Press, Coating, Inspection, Packaging | Standard, Immediate Release | 8 batches/day |
| **Food Processing Plant** | Mixing, Baking, Cooling, QC, Packaging, Labeling | Cookies, Bread | 20 batches/day |

### 🎨 Customer-Facing Frontends

| Frontend | Technology | Factory | Status |
|---------|-----------|---------|--------|
| **tshirt-customizer** | Angular + Material + Tailwind | tshirt-factory-001 | ✅ Ready |
| **vehicle-customizer** | HTML/JS + Tailwind | automotive-plant-001 | ✅ Ready |

👉 **Create your own**: See [FRONTEND_REPLICATION_GUIDE.md](FRONTEND_REPLICATION_GUIDE.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              JSON Configuration Layer                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Machine Templates (7)          Factory Configs (5)     │
│  ├─ cutting-machine.json        ├─ tshirt-factory.json │
│  ├─ sewing-machine.json         ├─ automotive-plant... │
│  ├─ quality-check-machine.json  ├─ electronics-fact... │
│  ├─ packaging-machine.json      ├─ pharmaceutical-p... │
│  ├─ welding-machine.json        └─ food-processing-...  │
│  ├─ pcb-assembly.json                                   │
│  └─ tablet-press.json                                   │
│                                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Factory Generator (Python Tool)              │
├─────────────────────────────────────────────────────────┤
│  ✓ Load & validate JSON schemas                        │
│  ✓ Generate machine classes                            │
│  ✓ Generate orchestrator                               │
│  ✓ Generate docker-compose                             │
│  ✓ Generate workflows                                  │
│  ✓ Generate documentation                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Generated Factories (Running Services)       │
├─────────────────────────────────────────────────────────┤
│  generated-factories/                                   │
│  ├─ tshirt-factory-001/        ← T-shirt factory       │
│  ├─ automotive-plant-001/      ← Automotive factory    │
│  ├─ electronics-factory-001/   ← Electronics factory   │
│  └─ ...                                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Use Cases

### 🎓 Education & Learning
- **Learn IoT Architecture**: MQTT, time-series databases, microservices
- **Understand Manufacturing**: ISA-95, OEE, production workflows
- **Full-Stack Development**: Backend APIs, frontends, databases
- **Practice DevOps**: Docker, container orchestration

### 🧪 Testing & Development
- **IoT Platform Testing**: Generate realistic factory data
- **Dashboard Development**: Test monitoring UIs with live data
- **Cloud Integration**: Validate AWS IoT, Azure IoT Hub integrations
- **Load Testing**: Simulate hundreds of sensors publishing data

### 📊 Demos & Proof-of-Concept
- **Customer Demos**: Show end-to-end IoT solutions
- **Stakeholder Presentations**: Interactive factory simulations
- **Trade Shows**: Run live manufacturing demonstrations
- **Sales Engineering**: Prove platform capabilities

### 🔬 Research & Prototyping
- **Manufacturing Optimization**: Study production efficiency
- **ML/AI Training**: Generate datasets for predictive maintenance
- **Digital Twin Development**: Prototype virtual factory models
- **Process Improvement**: Simulate workflow changes

---

## 🚀 Create Your Own Factory

### Step 1: Define Machine Template (5 min)

Create `machine-templates/my-machine.json`:

```json
{
  "machine_type": "assembly",
  "machine_name": "Assembly Robot",
  "sensors": [
    {
      "name": "arm_position",
      "type": "float",
      "range": {"min": 0, "max": 180},
      "update_behavior": {
        "type": "random_walk",
        "parameters": {"variation": 1.0}
      }
    },
    {
      "name": "temperature",
      "type": "float",
      "range": {"min": 20, "max": 80},
      "update_behavior": {
        "type": "sine_wave",
        "parameters": {"amplitude": 5.0, "frequency": 0.1}
      }
    }
  ],
  "operations": [
    {
      "name": "pick_and_place",
      "duration": {"type": "fixed", "value": 3.0},
      "inputs": [{"name": "component", "required": true}],
      "outputs": [{"name": "assembled_part"}],
      "failure_modes": [
        {"type": "random", "probability": 0.02}
      ]
    }
  ],
  "telemetry_config": {
    "publish_interval": 5.0
  }
}
```

### Step 2: Create Factory Configuration (10 min)

Create `factory-configs/my-factory.json`:

```json
{
  "factory_id": "my-factory-001",
  "factory_name": "My Manufacturing Plant",
  "factory_type": "custom",
  "machines": [
    {
      "machine_id": "assembly-01",
      "machine_type": "assembly",
      "template_file": "machine-templates/my-machine.json",
      "instance_name": "Assembly Robot #1",
      "enabled": true
    }
  ],
  "workflows": [
    {
      "workflow_id": "basic-production",
      "workflow_name": "Basic Production",
      "product_type": "assembled_product",
      "steps": [
        {
          "step_id": "step-1",
          "machine_type": "assembly",
          "operation": "pick_and_place",
          "required_inputs": ["component"],
          "outputs": ["assembled_part"]
        }
      ]
    }
  ],
  "production_config": {
    "mode": "continuous",
    "target_rate": {"value": 100, "unit": "units_per_hour"}
  }
}
```

### Step 3: Generate and Run (2 min)

```bash
# Generate factory
python3 tools/factory_generator.py factory-configs/my-factory.json

# Navigate to generated factory
cd generated-factories/my-factory-001

# Start all services
docker compose up --build

# Monitor in real-time
mosquitto_sub -h localhost -p 1883 -t "factory/#" -v
```

---

## 📚 Documentation

### Getting Started
- **[QUICK_START_GENERIC_FACTORY.md](QUICK_START_GENERIC_FACTORY.md)** - Create your first factory in 15 minutes
- **[FRONTEND_REPLICATION_GUIDE.md](FRONTEND_REPLICATION_GUIDE.md)** - Build customer-facing apps for ANY factory

### Platform Details
- **[GENERIC_FACTORY_SYSTEM.md](GENERIC_FACTORY_SYSTEM.md)** - Complete platform documentation
- **[MIGRATION_TO_JSON_BASED.md](MIGRATION_TO_JSON_BASED.md)** - Migration from hardcoded to JSON-based

### API & Monitoring
- **[simple_factory_simulator/README.md](simple_factory_simulator/README.md)** - Universal monitoring dashboard

### Configuration Schemas
- **[schemas/machine-template-schema.json](schemas/machine-template-schema.json)** - Machine template schema
- **[schemas/factory-config-schema.json](schemas/factory-config-schema.json)** - Factory configuration schema

### Frontend Examples
- **[tshirt-customizer/README.md](tshirt-customizer/README.md)** - Angular frontend for t-shirt orders
- **[vehicle-customizer/README.md](vehicle-customizer/README.md)** - HTML/JS frontend for vehicle orders

---

## 📁 Repository Structure

```
tshirt-factory/
│
├── 📁 JSON CONFIGURATION (Primary System)
│   ├── machine-templates/               # Reusable machine definitions
│   │   ├── cutting-machine.json         # T-shirt cutting
│   │   ├── sewing-machine.json          # T-shirt sewing
│   │   ├── quality-check-machine.json   # Quality inspection
│   │   ├── packaging-machine.json       # Packaging & labeling
│   │   ├── welding-machine.json         # Automotive welding
│   │   ├── pcb-assembly.json            # Electronics PCB
│   │   └── tablet-press.json            # Pharmaceutical tablet
│   │
│   ├── factory-configs/                 # Factory definitions
│   │   ├── tshirt-factory.json          # T-shirt manufacturing
│   │   ├── automotive-assembly-plant.json
│   │   ├── electronics-factory.json
│   │   ├── pharmaceutical-plant.json
│   │   └── food-processing-plant.json
│   │
│   ├── tools/
│   │   ├── factory_generator.py         # Factory generator
│   │   └── create_machine.py            # Machine template creator
│   │
│   └── generated-factories/
│       ├── tshirt-factory-001/          # Generated t-shirt factory
│       ├── automotive-plant-001/
│       ├── electronics-factory-001/
│       └── ...
│
├── 📁 CUSTOMER FRONTENDS (Connect to Generated Factories)
│   ├── tshirt-customizer/               # Angular app for t-shirt orders
│   ├── vehicle-customizer/              # HTML/JS app for vehicle orders
│   └── simple_factory_simulator/        # Universal monitoring dashboard
│
├── 📁 SCHEMAS
│   ├── machine-template-schema.json     # Machine template validation
│   └── factory-config-schema.json       # Factory config validation
│
├── 📁 ARCHIVED (Reference Only)
│   ├── old-docs/                        # Archived documentation
│   └── services_hardcoded_original/     # Old hardcoded services
│
└── 📁 DOCUMENTATION
    ├── README.md                        # This file
    ├── GENERIC_FACTORY_SYSTEM.md        # Platform documentation
    ├── QUICK_START_GENERIC_FACTORY.md   # Quick start guide
    ├── MIGRATION_TO_JSON_BASED.md       # Migration guide
    └── FRONTEND_REPLICATION_GUIDE.md    # Frontend creation guide
```

---

## 🔧 What You Can Configure

### Machine Templates

**Sensors**:
- Types: float, integer, boolean, string
- Behaviors: random_walk, sine_wave, step, conditional
- Ranges with min/max values
- Alert conditions for anomalies

**Operations**:
- Duration: fixed, range, formula-based
- Inputs and outputs
- Failure modes with probabilities
- Conditional failures based on sensor values
- Sensor impacts during operations

**Telemetry**:
- Custom metrics and KPIs
- Time-based aggregations
- Configurable publish intervals
- MQTT topic customization

### Factory Configurations

**Machines**:
- Deploy multiple instances from templates
- Location and zone tracking
- Machine-specific overrides
- Enable/disable individual machines

**Workflows**:
- Sequential and parallel steps
- Conditional execution based on quality
- Retry logic for failed steps
- Multiple product types

**Production**:
- Modes: continuous, batch, on-demand, scheduled
- Shift schedules (24/7, 8-hour shifts, etc.)
- Quality control thresholds
- Inventory simulation
- Custom KPI tracking

**Networking**:
- MQTT broker ports
- WebSocket ports
- PostgreSQL ports
- Container networking

---

## ✨ Key Features

### IoT Integration
- ✅ ISA-95 compliant MQTT topics
- ✅ Real-time telemetry publishing
- ✅ Cloud-ready (AWS IoT, Azure IoT Hub, Google Cloud IoT)
- ✅ WebSocket support for browser clients

### Data Persistence
- ✅ PostgreSQL for transactional data
- ✅ TimescaleDB for time-series sensor data
- ✅ Production order tracking
- ✅ Machine state history

### Realistic Simulation
- ✅ Multiple sensor update behaviors
- ✅ Failure modes with conditional triggers
- ✅ Maintenance operations
- ✅ Material consumption tracking
- ✅ Quality score calculations

### Production Flexibility
- ✅ Multiple production modes
- ✅ Parallel workflow execution
- ✅ Conditional steps with quality gates
- ✅ Inventory management
- ✅ Batch tracking

### Monitoring & Analytics
- ✅ OEE (Overall Equipment Effectiveness) tracking
- ✅ Custom KPI calculations
- ✅ Time-series data aggregations
- ✅ Real-time dashboard updates
- ✅ MQTT message monitoring

---

## 🌍 Supported Factory Types

This platform works for **ANY** manufacturing domain:

- ✅ **Automotive** - Body shops, paint shops, final assembly
- ✅ **Electronics** - PCB assembly, SMT lines, testing
- ✅ **Pharmaceutical** - Tablet manufacturing, coating, packaging
- ✅ **Food Processing** - Baking, mixing, packaging, labeling
- ✅ **Textile** - Cutting, sewing, dyeing, finishing
- ✅ **Chemical** - Mixing, heating, filtering, distillation
- ✅ **Aerospace** - CNC machining, assembly, NDT testing
- ✅ **Medical Devices** - Injection molding, assembly, sterilization
- ✅ **Battery** - Cell assembly, testing, pack formation
- ✅ **Semiconductor** - Wafer fabrication, testing, packaging
- ✅ **Any other manufacturing domain!**

---

## 📊 What Makes This Special

1. **Universal** - Works for ANY manufacturing domain
2. **Zero-Code** - Pure JSON configuration, no programming
3. **Rapid** - Create complete factories in 15-30 minutes
4. **Realistic** - Authentic sensor behaviors, failures, timing
5. **Scalable** - From 1 machine to 100s of machines
6. **Reusable** - Share machine templates across factories
7. **Versioned** - Track all configs in git
8. **IoT-Ready** - MQTT, databases, cloud integration built-in
9. **Frontend Pattern** - Replicate customer apps for any factory
10. **Production-Ready** - Docker containerized, microservices architecture

---

## 🧪 Testing Your Factory

### 1. Start Factory Services

```bash
cd generated-factories/your-factory-001
docker compose up --build
```

### 2. Monitor MQTT Messages

```bash
# Subscribe to all factory topics
mosquitto_sub -h localhost -p 1883 -t "factory/#" -v

# Subscribe to specific machine
mosquitto_sub -h localhost -p 1883 -t "factory/your-factory-001/machines/cutting-01/#" -v
```

### 3. Send Production Order

```bash
mosquitto_pub -h localhost -p 1883 \
  -t "factory/your-factory-001/production/request" \
  -m '{
    "workflow_id": "standard-production",
    "product_type": "your_product",
    "quantity": 1,
    "parameters": {
      "size": "M",
      "color": "blue"
    }
  }'
```

### 4. Check Database

```bash
# Access PostgreSQL
docker exec -it your-factory-001-postgres psql -U factory_user -d your_factory

# Query production orders
SELECT * FROM production_orders;

# Query machine telemetry
SELECT * FROM machine_telemetry ORDER BY timestamp DESC LIMIT 10;
```

### 5. View Logs

```bash
# View all services
docker compose logs -f

# View specific machine
docker logs -f your-factory-001-cutting-01
```

---

## 🔄 Evolution & Version History

- **Phase 1.0**: Hardcoded T-shirt factory (4 machines)
- **Phase 1.5**: Flexible workflows with JSON configuration
- **Phase 1.6**: Machine template generator (7 machine types)
- **Phase 1.7**: Multi-factory support (automotive, pharma, electronics, food)
- **Phase 2.0**: **Universal JSON-Based Platform** (ANY factory type!)
  - All factories generated from JSON
  - Customer-facing frontend pattern
  - Complete migration from hardcoded services

See [MIGRATION_TO_JSON_BASED.md](MIGRATION_TO_JSON_BASED.md) for migration details.

---

## 💡 Pro Tips

1. **Start with Examples** - Copy and modify existing factory configs
2. **Reuse Templates** - Share machine templates across factories
3. **Test Incrementally** - Start with 1-2 machines, add more gradually
4. **Monitor MQTT** - Always watch MQTT messages during development
5. **Use Schemas** - Validate JSON configs against schemas
6. **Version Control** - Track your factory configs in git
7. **Document Workflows** - Add clear descriptions to workflow steps
8. **Frontend Pattern** - Use tshirt-customizer or vehicle-customizer as templates

---

## 🛠️ Requirements

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.9+
- **MQTT Broker** (Mosquitto - included in docker-compose)
- **PostgreSQL** 13+ (included in docker-compose)
- **Node.js** 16+ (for Angular frontends only)

---

## 🆘 Troubleshooting

### Factory won't generate
```bash
# Validate JSON syntax
python3 -m json.tool factory-configs/your-factory.json

# Check for schema errors in output
python3 tools/factory_generator.py factory-configs/your-factory.json
```

### Docker services won't start
```bash
# Check port conflicts
lsof -i :1883  # MQTT
lsof -i :9001  # WebSocket
lsof -i :5432  # PostgreSQL

# View detailed logs
cd generated-factories/your-factory-001
docker compose logs
```

### No MQTT messages
- Verify MQTT broker is running: `docker ps | grep mosquitto`
- Check machine logs: `docker logs -f your-factory-001-machine-01`
- Confirm topic subscription: `mosquitto_sub -h localhost -p 1883 -t "#" -v`

### Frontend can't connect
- Verify simple_factory_simulator is running on port 5001
- Check MQTT_PORT and MQTT_WS_PORT environment variables
- Confirm factory_id matches in frontend config

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

Contributions welcome! Areas for contribution:
- New machine templates
- Factory configurations for different industries
- Frontend examples
- Documentation improvements
- Bug fixes and enhancements

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: See docs linked above
- **Examples**: Check `factory-configs/` directory
- **Templates**: Browse `machine-templates/` directory

---

## 🎯 Quick Command Reference

```bash
# Generate factory
python3 tools/factory_generator.py factory-configs/your-factory.json

# Start factory
cd generated-factories/your-factory-001
docker compose up --build

# Start API gateway
cd simple_factory_simulator
export MQTT_PORT=1883
export MQTT_WS_PORT=9001
python3 app.py

# Monitor MQTT
mosquitto_sub -h localhost -p 1883 -t "factory/#" -v

# Send order
mosquitto_pub -h localhost -p 1883 \
  -t "factory/your-factory-001/production/request" \
  -m '{"workflow_id": "standard", "quantity": 1}'

# Query database
docker exec -it your-factory-001-postgres psql -U factory_user -d your_factory

# Stop factory
docker compose down

# Clean up
docker compose down -v  # Removes volumes too
```

---

**🏭 Transform your factory simulation needs into reality in minutes! 🚀**

**Version 2.0** - Universal JSON-Based Factory Platform
