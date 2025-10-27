# Universal Factory Simulation Platform

## 🚀 Create ANY Factory Type Through JSON Configuration

**From T-Shirt Factory to Universal Manufacturing Platform** - Generate complete factory simulations for automotive, food processing, electronics, pharmaceuticals, and ANY manufacturing domain in **15-30 minutes**.

---

## What Is This?

A **zero-code factory simulation platform** that allows you to:

- ✅ Define machine types with sensors and operations (JSON)
- ✅ Configure complete factories with workflows (JSON)
- ✅ Auto-generate Python code, Docker configs, and workflows
- ✅ Run realistic IoT-enabled manufacturing simulations

**No programming required. Just JSON configuration.**

## Quick Start (15 Minutes)

### 1. Use Pre-Built Factory Examples

```bash
# Generate an automotive factory
python tools/factory_generator.py factory-configs/automotive-assembly-plant.json

# Generate an electronics factory
python tools/factory_generator.py factory-configs/electronics-factory.json

# Generate a pharmaceutical plant
python tools/factory_generator.py factory-configs/pharmaceutical-plant.json

# Generate a food processing plant
python tools/factory_generator.py factory-configs/food-processing-plant.json

# Navigate and run
cd generated-factories/automotive-plant-001
docker compose up --build
```

### 2. Monitor Your Factory

```bash
# Watch MQTT messages in real-time
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Send production order
mosquitto_pub -h localhost -p 31883 \
  -t "factory/automotive-plant-001/production/request" \
  -m '{"product_type": "sedan", "quantity": 1}'
```

### 3. Check Data

```bash
# Query database
docker exec -it automotive-plant-001-postgres psql -U factory_user -d automotive_factory

# Check machine logs
docker logs -f automotive-plant-001-welding-01
```

---

## Real-World Factory Examples

### 🚗 Automotive Assembly Plant

**Features**:
- 6 machines: Stamping → Welding (2x parallel) → Painting → Assembly → Inspection
- 2 workflows: Sedan production, SUV production
- 50 vehicles/day, 3 shifts
- Parallel welding operations
- Quality inspection with conditional execution
- OEE tracking, inventory simulation

**Config**: `factory-configs/automotive-assembly-plant.json`

```bash
python tools/factory_generator.py factory-configs/automotive-assembly-plant.json
cd generated-factories/automotive-plant-001
docker compose up
```

### 📱 Electronics Manufacturing

**Features**:
- 6 machines: PCB Assembly (2x) → Soldering → Testing (2x) → Packaging
- 2 workflows: Smartphone PCB, IoT Sensor modules
- 500 units/hour
- Parallel component placement
- AOI and functional testing
- First-pass yield tracking

**Config**: `factory-configs/electronics-factory.json`

### 💊 Pharmaceutical Plant

**Features**:
- 7 machines: Blending → Granulation → Drying → Tablet Press → Coating → Inspection → Packaging
- 2 workflows: Standard coated tablets, Immediate release tablets
- GMP-compliant batch production
- 8 batches/day
- Content uniformity tracking
- Batch traceability

**Config**: `factory-configs/pharmaceutical-plant.json`

### 🍪 Food Processing Plant

**Features**:
- 6 machines: Mixing → Baking → Cooling → Quality Check → Packaging → Labeling
- 2 workflows: Cookie production, Bread production
- 20 batches/day
- Food safety compliance
- Yield optimization
- Batch tracking

**Config**: `factory-configs/food-processing-plant.json`

---

## Architecture

```
┌────────────────────────────────────────┐
│      Machine Templates (JSON)          │
│  - Define sensors & behaviors          │
│  - Configure operations                │
│  - Set failure modes                   │
└─────────────────┬──────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────┐
│     Factory Configuration (JSON)       │
│  - Deploy machine instances            │
│  - Define workflows                    │
│  - Set production parameters           │
└─────────────────┬──────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────┐
│      Factory Generator (Python)        │
│  - Generates machine code              │
│  - Creates docker-compose              │
│  - Produces documentation              │
└─────────────────┬──────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────┐
│     Running Factory Simulation         │
│  - MQTT communication                  │
│  - Database persistence                │
│  - Real-time telemetry                 │
└────────────────────────────────────────┘
```

---

## What You Can Configure

### Machine Templates

Define reusable machine types:

**Sensors**:
- Types: float, integer, boolean, string
- Behaviors: random_walk, sine_wave, step, conditional
- Ranges and anomaly detection

**Operations**:
- Duration: fixed, range, formula-based
- Inputs and outputs
- Failure modes with probabilities
- Sensor impacts

**Telemetry**:
- Custom metrics
- Time-based aggregations
- Publish intervals

**Example**: `machine-templates/welding-machine.json`

### Factory Configuration

Define complete factories:

**Machines**:
- Instance deployment
- Location tracking
- Configuration overrides

**Workflows**:
- Sequential and parallel steps
- Conditional execution
- Retry logic

**Production**:
- Modes: continuous, batch, on-demand, scheduled
- Shift schedules
- Quality control
- Inventory simulation
- KPI tracking

**Example**: `factory-configs/automotive-assembly-plant.json`

---

## Create Your Own Factory

### Step 1: Define Machine Template (5 min)

`machine-templates/my-machine.json`:

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
    }
  ],
  "operations": [
    {
      "name": "pick_and_place",
      "duration": {"type": "fixed", "value": 3.0},
      "inputs": [{"name": "component", "required": true}],
      "outputs": [{"name": "assembled_part"}]
    }
  ],
  "telemetry_config": {
    "publish_interval": 5.0
  }
}
```

### Step 2: Create Factory Config (10 min)

`factory-configs/my-factory.json`:

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
python tools/factory_generator.py factory-configs/my-factory.json
cd generated-factories/my-factory-001
docker compose up --build
```

---

## Supported Factory Types

✅ **Automotive** - Body shop, paint shop, assembly
✅ **Electronics** - PCB assembly, SMT, testing
✅ **Pharmaceutical** - Tablet manufacturing, coating, packaging
✅ **Food Processing** - Baking, mixing, packaging
✅ **Textile** - Cutting, sewing, dyeing, finishing
✅ **Chemical** - Mixing, heating, filtering
✅ **Aerospace** - CNC machining, assembly, testing
✅ **Medical Devices** - Injection molding, assembly, sterilization
✅ **Battery** - Cell assembly, testing, pack formation
✅ **ANY manufacturing domain!**

---

## Key Features

### IoT Integration
- ISA-95 compliant MQTT topics
- Real-time telemetry publishing
- Cloud-ready architecture (AWS IoT, Azure IoT Hub)

### Data Persistence
- PostgreSQL for transactional data
- TimescaleDB for time-series sensor data
- Redis for caching

### Realistic Simulation
- Sensor behaviors (random_walk, sine_wave, etc.)
- Failure modes with conditions
- Maintenance and degradation
- Material consumption tracking

### Production Flexibility
- Multiple production modes
- Parallel workflows
- Conditional steps
- Quality gates
- Inventory management

### Monitoring & Analytics
- OEE tracking
- Custom KPIs
- Time-series aggregations
- Anomaly detection

---

## Documentation

### Quick Start
- **[QUICK_START_GENERIC_FACTORY.md](QUICK_START_GENERIC_FACTORY.md)** - Create factory in 15 minutes

### Complete Guide
- **[GENERIC_FACTORY_SYSTEM.md](GENERIC_FACTORY_SYSTEM.md)** - Full platform documentation

### Technical
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Project status and version history
- **[MICROSERVICES_README.md](MICROSERVICES_README.md)** - Microservices architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams

### Cloud Integration
- **[PHASE2_ARCHITECTURE.md](PHASE2_ARCHITECTURE.md)** - Cloud architecture design
- **[PHASE2_IMPLEMENTATION_GUIDE.md](PHASE2_IMPLEMENTATION_GUIDE.md)** - Cloud implementation guide

### Schemas
- **[schemas/machine-template-schema.json](schemas/machine-template-schema.json)** - Machine template schema
- **[schemas/factory-config-schema.json](schemas/factory-config-schema.json)** - Factory configuration schema

---

## File Structure

```
├── schemas/                              # JSON schemas
│   ├── machine-template-schema.json
│   └── factory-config-schema.json
│
├── machine-templates/                    # Reusable machine definitions
│   ├── welding-machine.json
│   ├── pcb-assembly.json
│   ├── tablet-press.json
│   └── ... (add unlimited types)
│
├── factory-configs/                      # Complete factory definitions
│   ├── automotive-assembly-plant.json
│   ├── electronics-factory.json
│   ├── pharmaceutical-plant.json
│   ├── food-processing-plant.json
│   └── ... (add unlimited factories)
│
├── tools/
│   ├── factory_generator.py             # Generate factory from JSON
│   └── create_machine.py                # Create machine template
│
├── generated-factories/                  # Generated factory outputs
│   ├── automotive-plant-001/
│   ├── electronics-factory-001/
│   └── ...
│
└── services/                             # Original T-shirt factory (still available)
    ├── machines/
    └── orchestrator/
```

---

## Requirements

- **Docker** and **Docker Compose**
- **Python 3.9+**
- **MQTT Broker** (included in docker-compose)
- **PostgreSQL** (included in docker-compose)

---

## Use Cases

### 🎓 Education
- Learn IoT architecture
- Understand manufacturing workflows
- Study MQTT and time-series data
- Practice microservices design

### 🧪 Testing
- Test IoT platforms and dashboards
- Validate data pipelines
- Load test cloud infrastructure
- Prototype production systems

### 📊 Demo & Proof-of-Concept
- Showcase IoT capabilities
- Demonstrate real-time monitoring
- Prove architecture concepts
- Present to stakeholders

### 🔬 Research
- Study manufacturing optimization
- Analyze production data
- Test ML/AI algorithms
- Simulate factory scenarios

---

## What Makes This Special

1. **Universal** - Works for ANY manufacturing domain
2. **Zero-Code** - Pure JSON configuration
3. **Rapid** - Create factories in 15-30 minutes
4. **Realistic** - Sensor behaviors, failures, timing
5. **Scalable** - From 1 machine to 100s
6. **Reusable** - Share templates across factories
7. **Versioned** - Track configs in git
8. **IoT-Ready** - MQTT, databases, cloud integration

---

## Evolution

**Phase 1**: Microservices Architecture (4 machines)
**Phase 1.5**: Flexible Workflows
**Phase 1.6**: Extensible Machines (7 machines, generator tool)
**Phase 1.7**: **UNIVERSAL PLATFORM** (ANY factory via JSON!)

---

## License

MIT License - See LICENSE file

---

## Contributing

Contributions welcome! Please read CONTRIBUTING.md

---

## Support

- **Issues**: GitHub Issues
- **Documentation**: See docs/ directory
- **Examples**: See factory-configs/ directory

---

## Quick Commands

```bash
# Generate factory
python tools/factory_generator.py factory-configs/automotive-assembly-plant.json

# Start factory
cd generated-factories/automotive-plant-001
docker compose up --build

# Monitor MQTT
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Send order
mosquitto_pub -h localhost -p 31883 \
  -t "factory/automotive-plant-001/production/request" \
  -m '{"product_type": "sedan", "quantity": 1}'

# Query database
docker exec -it automotive-plant-001-postgres psql -U factory_user -d automotive_factory

# Stop factory
docker compose down
```

---

**Transform your manufacturing simulation needs into reality in minutes!** 🏭🚀

**Version 2.0** - Universal Factory Platform
