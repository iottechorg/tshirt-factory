# Two-System Architecture Overview

## Complete System Comparison and Architecture

This document provides a comprehensive architectural view of both factory systems in this repository.

---

## 🏗️ System Architecture Comparison

### System 1: T-Shirt Factory (Reference Implementation)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       T-SHIRT FACTORY SYSTEM                        │
│                  (Complete E-Commerce Implementation)                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────┐         ┌────────────────────────┐     │
│  │   tshirt-customizer    │         │ simple_factory_simulator│     │
│  │   (Angular + Tailwind) │         │  (Flask + Tailwind)     │     │
│  ├────────────────────────┤         ├────────────────────────┤     │
│  │ - Product selection    │         │ - Machine monitoring    │     │
│  │ - Size/color picker    │         │ - Sensor control        │     │
│  │ - Custom text input    │         │ - Production control    │     │
│  │ - Order placement      │         │ - Test automation       │     │
│  │                        │         │                         │     │
│  │ User: Customer         │         │ User: Factory operator  │     │
│  └────────┬───────────────┘         └───────────┬─────────────┘     │
│           │                                     │                    │
└───────────┼─────────────────────────────────────┼────────────────────┘
            │                                     │
            │ HTTP REST API                       │ HTTP REST API
            │                                     │ MQTT WebSocket
            ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      COMMUNICATION LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    ┌──────────────────────┐                         │
│                    │   MQTT Broker        │                         │
│                    │   (Mosquitto)        │                         │
│                    ├──────────────────────┤                         │
│                    │ Port: 1883 (MQTT)    │                         │
│                    │ Port: 9001 (WS)      │                         │
│                    └──────────┬───────────┘                         │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    ┌──────────────────────┐                         │
│                    │   Orchestrator       │                         │
│                    ├──────────────────────┤                         │
│                    │ - Receives orders    │                         │
│                    │ - Workflow execution │                         │
│                    │ - Step coordination  │                         │
│                    │ - Status tracking    │                         │
│                    └──────────┬───────────┘                         │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                                ▼
        ┌───────────┬───────────┼───────────┬───────────┐
        │           │           │           │           │
        ▼           ▼           ▼           ▼           │
┌─────────────────────────────────────────────────────────────────────┐
│                        MACHINE LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Cutting  │  │ Sewing   │  │ Quality  │  │Packaging │           │
│  │ Machine  │  │ Machine  │  │  Check   │  │ Machine  │           │
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤           │
│  │Sensors:  │  │Sensors:  │  │Sensors:  │  │Sensors:  │           │
│  │- Temp    │  │- Temp    │  │- Score   │  │- Speed   │           │
│  │- Pressure│  │- Tension │  │- Defects │  │- Count   │           │
│  │          │  │          │  │          │  │          │           │
│  │Operations│  │Operations│  │Operations│  │Operations│           │
│  │- Cut     │  │- Sew     │  │- Inspect │  │- Pack    │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │             │             │                   │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────┐         ┌────────────────────────┐     │
│  │   PostgreSQL           │         │   Redis                │     │
│  ├────────────────────────┤         ├────────────────────────┤     │
│  │ - Production orders    │         │ - Session cache        │     │
│  │ - Machine telemetry    │         │ - Queue management     │     │
│  │ - Production history   │         │ - Temp data            │     │
│  │ - Machine status       │         │                        │     │
│  └────────────────────────┘         └────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### System 2: Generic Factory Platform (Universal Generator)

```
┌─────────────────────────────────────────────────────────────────────┐
│                   GENERIC FACTORY PLATFORM                          │
│             (JSON-Driven Universal Factory Generator)               │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────┐         ┌────────────────────────┐     │
│  │  Machine Templates     │         │  Factory Configs       │     │
│  │  (JSON Files)          │         │  (JSON Files)          │     │
│  ├────────────────────────┤         ├────────────────────────┤     │
│  │ welding-machine.json   │────────▶│ automotive-plant.json  │     │
│  │ pcb-assembly.json      │   Used  │ electronics-factory... │     │
│  │ tablet-press.json      │    by   │ pharmaceutical-plant.. │     │
│  │ (unlimited types)      │         │ food-processing-plant..│     │
│  │                        │         │ (unlimited factories)  │     │
│  │ Define:                │         │ Define:                │     │
│  │ - Sensors & behaviors  │         │ - Machine instances    │     │
│  │ - Operations           │         │ - Workflows            │     │
│  │ - Failure modes        │         │ - Production config    │     │
│  │ - Telemetry config     │         │ - KPIs & metrics       │     │
│  └────────────────────────┘         └───────────┬────────────┘     │
│                                                  │                   │
└──────────────────────────────────────────────────┼───────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GENERATION LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    ┌──────────────────────┐                         │
│                    │  Factory Generator   │                         │
│                    │  (Python Tool)       │                         │
│                    ├──────────────────────┤                         │
│                    │ 1. Load JSON configs │                         │
│                    │ 2. Validate schemas  │                         │
│                    │ 3. Generate code:    │                         │
│                    │    - Machine classes │                         │
│                    │    - Orchestrator    │                         │
│                    │    - docker-compose  │                         │
│                    │    - Workflows       │                         │
│                    │    - Documentation   │                         │
│                    └──────────┬───────────┘                         │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                                ▼ Generates
┌─────────────────────────────────────────────────────────────────────┐
│                      GENERATED FACTORY                              │
│                   (Example: Automotive Plant)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Frontend Layer                           │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │          ┌────────────────────────────┐                     │   │
│  │          │ simple_factory_simulator   │                     │   │
│  │          │ (Universal Monitoring)     │                     │   │
│  │          ├────────────────────────────┤                     │   │
│  │          │ - Machine monitoring       │                     │   │
│  │          │ - Production control       │                     │   │
│  │          │ - Test automation          │                     │   │
│  │          │                            │                     │   │
│  │          │ Configured via env vars:   │                     │   │
│  │          │ MQTT_PORT=31883            │                     │   │
│  │          │ MQTT_WS_PORT=39001         │                     │   │
│  │          └──────────┬─────────────────┘                     │   │
│  │                     │                                        │   │
│  └─────────────────────┼────────────────────────────────────────┘   │
│                        │                                             │
│  ┌─────────────────────┼────────────────────────────────────────┐   │
│  │          Communication Layer                                 │   │
│  ├─────────────────────┼────────────────────────────────────────┤   │
│  │                     │                                         │   │
│  │          ┌──────────▼─────────────┐                          │   │
│  │          │   MQTT Broker          │                          │   │
│  │          │   (Mosquitto)          │                          │   │
│  │          ├────────────────────────┤                          │   │
│  │          │ Port: 31883 (MQTT)     │                          │   │
│  │          │ Port: 39001 (WS)       │                          │   │
│  │          └──────────┬─────────────┘                          │   │
│  │                     │                                         │   │
│  └─────────────────────┼────────────────────────────────────────┘   │
│                        │                                             │
│  ┌─────────────────────┼────────────────────────────────────────┐   │
│  │          Orchestration Layer                                 │   │
│  ├─────────────────────┼────────────────────────────────────────┤   │
│  │                     │                                         │   │
│  │          ┌──────────▼─────────────┐                          │   │
│  │          │   Generated            │                          │   │
│  │          │   Orchestrator         │                          │   │
│  │          ├────────────────────────┤                          │   │
│  │          │ Workflows:             │                          │   │
│  │          │ - sedan-production     │                          │   │
│  │          │ - suv-production       │                          │   │
│  │          │                        │                          │   │
│  │          │ Features:              │                          │   │
│  │          │ - Parallel steps       │                          │   │
│  │          │ - Conditional execution│                          │   │
│  │          │ - Retry logic          │                          │   │
│  │          └──────────┬─────────────┘                          │   │
│  │                     │                                         │   │
│  └─────────────────────┼────────────────────────────────────────┘   │
│                        │                                             │
│  ┌─────────────────────┼────────────────────────────────────────┐   │
│  │          Machine Layer (6 Machines)                          │   │
│  ├─────────────────────┼────────────────────────────────────────┤   │
│  │                     │                                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │ Stamping │  │ Welding  │  │ Welding  │  │ Painting │   │   │
│  │  │   #1     │  │   #1     │  │   #2     │  │   #1     │   │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │   │
│  │       │             │\____________/│             │          │   │
│  │       │             │ Parallel    │             │          │   │
│  │       │             │ Operations  │             │          │   │
│  │       │             │             │             │          │   │
│  │  ┌────▼─────┐  ┌──────────┐                               │   │
│  │  │ Assembly │  │Inspection│                               │   │
│  │  │   #1     │  │   #1     │                               │   │
│  │  └──────────┘  └──────────┘                               │   │
│  │                                                            │   │
│  │  Each machine has:                                        │   │
│  │  - Generated Python class                                 │   │
│  │  - Configurable sensors (random_walk, sine_wave, etc.)    │   │
│  │  - Operations with formulas                               │   │
│  │  - Failure modes                                          │   │
│  │  - Docker container                                       │   │
│  │                                                            │   │
│  └─────────────────────┬──────────────────────────────────────┘   │
│                        │                                            │
│  ┌─────────────────────┼──────────────────────────────────────┐   │
│  │          Persistence Layer                                 │   │
│  ├─────────────────────┼──────────────────────────────────────┤   │
│  │                     │                                       │   │
│  │  ┌──────────────────▼────────┐  ┌────────────────────┐    │   │
│  │  │  PostgreSQL/TimescaleDB   │  │  Redis (optional)  │    │   │
│  │  ├───────────────────────────┤  ├────────────────────┤    │   │
│  │  │ - Production orders       │  │ - Caching          │    │   │
│  │  │ - Time-series sensor data │  │ - Queues           │    │   │
│  │  │ - OEE metrics             │  │                    │    │   │
│  │  │ - KPI tracking            │  │                    │    │   │
│  │  │ - Inventory simulation    │  │                    │    │   │
│  │  └───────────────────────────┘  └────────────────────┘    │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Feature Comparison Matrix

| Feature | T-Shirt Factory | Generic Factory Platform |
|---------|-----------------|--------------------------|
| **Architecture** | Fixed, hardcoded | Dynamic, JSON-generated |
| **Machines** | 4 (cutting, sewing, quality, packaging) | Unlimited, configurable |
| **Workflows** | 1 fixed workflow | Unlimited workflows per factory |
| **Frontend** | 2 apps (customer + monitoring) | 1 monitoring app (universal) |
| **Configuration** | Docker Compose + env vars | JSON templates + generation |
| **Customization** | Code changes required | JSON editing only |
| **Sensor Behaviors** | Hardcoded random | Configurable (random_walk, sine_wave, etc.) |
| **Parallel Processing** | No | Yes (parallel_group) |
| **Conditional Steps** | No | Yes (quality gates) |
| **Failure Modes** | Basic | Advanced with conditions |
| **Production Modes** | Fixed | continuous, batch, on-demand, scheduled |
| **KPI Tracking** | Basic | Custom formulas and metrics |
| **Inventory Management** | No | Yes, configurable |
| **Time Scaling** | Fixed | Configurable (1x to 100x) |
| **Database** | PostgreSQL + Redis | PostgreSQL/TimescaleDB + Redis |
| **MQTT Topics** | Hardcoded | ISA-95 compliant, dynamic |
| **Documentation** | Manual | Auto-generated |
| **Setup Time** | 10 minutes | 15-30 minutes |
| **Learning Curve** | Easy | Moderate |
| **Use Case** | Education, simple demos | IoT testing, complex simulations |
| **Extensibility** | Low (requires coding) | High (JSON only) |
| **Industry Coverage** | T-shirt manufacturing only | ANY manufacturing domain |

---

## 🔄 Data Flow Comparison

### T-Shirt Factory Data Flow

```
Customer Order (Angular)
         │
         ├─ HTTP POST /order
         │
         ▼
   API Gateway
         │
         ├─ MQTT Publish: factory/tshirt-factory/production/request
         │
         ▼
  Orchestrator
         │
         ├─ Reads fixed workflow
         │
         ├─ Step 1 → MQTT: factory/tshirt-factory/machines/cutting-01/command
         │            ↓
         │         Cutting Machine processes
         │            ↓
         │         MQTT: factory/tshirt-factory/machines/cutting-01/operation
         │            ↓
         │         Returns to Orchestrator
         │
         ├─ Step 2 → Sewing Machine
         ├─ Step 3 → Quality Check
         ├─ Step 4 → Packaging
         │
         ├─ MQTT Publish: factory/tshirt-factory/production/complete
         │
         ▼
  Database (PostgreSQL)
  Monitoring Dashboard
  Customer Notification
```

### Generic Factory Data Flow

```
Production Request (via MQTT or API)
         │
         ├─ JSON workflow definition
         │
         ▼
Generated Orchestrator
         │
         ├─ Parses JSON workflow
         │
         ├─ Step 1 (parallel_group: 1)
         │   ├─ MQTT → Machine A (e.g., PCB Assembly #1)
         │   └─ MQTT → Machine B (e.g., PCB Assembly #2)
         │        ↓               ↓
         │    Processes in parallel
         │        ↓               ↓
         │    Both complete
         │
         ├─ Step 2 (conditional)
         │   ├─ MQTT → Machine C (e.g., Reflow Oven)
         │        ↓
         │    Operation with formula: duration = f(temp, components)
         │        ↓
         │    Sensor behaviors: sine_wave, random_walk
         │        ↓
         │    Check conditions: quality_score >= 0.95
         │        ↓
         │    Pass? Continue : Retry/Fail
         │
         ├─ Step 3 → Testing machines (parallel)
         ├─ Step 4 → Packaging
         │
         ├─ Calculate KPIs (custom formulas)
         ├─ Update inventory
         ├─ Track OEE metrics
         │
         ├─ MQTT Publish: factory/{factory_id}/production/complete
         │
         ▼
TimescaleDB (time-series data)
PostgreSQL (transactional data)
Monitoring Dashboard (universal)
Custom integrations
```

---

## 🎯 When to Use Each System

### Use T-Shirt Factory When:

1. **Learning IoT basics**
   - You're new to IoT manufacturing systems
   - You want to understand microservices architecture
   - You need a simple, complete example

2. **Education & Teaching**
   - Teaching factory automation concepts
   - Demonstrating e-commerce integration
   - Classroom demonstrations

3. **Quick Demos**
   - Showcasing IoT capabilities in 10 minutes
   - Presenting to non-technical stakeholders
   - Proof-of-concept for simple workflows

4. **E-Commerce Integration**
   - Testing customer order systems
   - Building customer-facing applications
   - Understanding order-to-production flow

### Use Generic Factory Platform When:

1. **IoT Platform Testing**
   - Testing dashboards with various factory types
   - Validating data pipelines with different data patterns
   - Load testing with realistic manufacturing data

2. **Industry-Specific Simulations**
   - Automotive assembly plants
   - Pharmaceutical GMP-compliant production
   - Electronics SMT lines
   - Food processing with safety compliance
   - Any other manufacturing domain

3. **Complex Workflows**
   - Parallel processing requirements
   - Conditional execution and quality gates
   - Multiple production modes
   - Advanced failure scenarios

4. **Research & Development**
   - Manufacturing optimization studies
   - ML/AI algorithm testing
   - Production scenario analysis
   - Factory design validation

5. **Rapid Prototyping**
   - Creating multiple factory types quickly
   - Testing different configurations
   - Iterating on factory designs
   - A/B testing production strategies

---

## 🔌 Integration Points

### Both Systems Provide:

1. **MQTT Integration**
   - ISA-95 compliant topics
   - Real-time telemetry
   - Command/control interface
   - Status updates

2. **REST API**
   - Machine management
   - Production control
   - Configuration updates
   - Status queries

3. **Database Access**
   - PostgreSQL for transactional data
   - Time-series data (TimescaleDB for generic)
   - Historical analysis
   - Reporting

4. **Monitoring Dashboard**
   - simple_factory_simulator works with both
   - Configurable via environment variables
   - Real-time visualization
   - Control interface

### Cloud Integration (Both Systems)

```
Factory System (T-Shirt or Generic)
         │
         ├─ MQTT Bridge
         │
         ▼
Cloud IoT Platform (AWS IoT, Azure IoT Hub, etc.)
         │
         ├─ Data ingestion
         │
         ▼
Cloud Services
         ├─ Data Lake (S3, Blob Storage)
         ├─ Analytics (Athena, Synapse)
         ├─ Dashboards (Grafana, Power BI)
         ├─ ML/AI (SageMaker, ML Studio)
         └─ Alerts (SNS, Event Grid)
```

---

## 🚀 Migration Path

### From T-Shirt Factory to Generic Platform

If you want to migrate your t-shirt factory to the generic platform:

1. **Create Machine Templates**
   ```bash
   # Create templates for each machine type
   machine-templates/cutting-machine.json
   machine-templates/sewing-machine.json
   machine-templates/quality-check.json
   machine-templates/packaging-machine.json
   ```

2. **Create Factory Configuration**
   ```bash
   # Define t-shirt factory using templates
   factory-configs/tshirt-factory.json
   ```

3. **Generate Factory**
   ```bash
   python tools/factory_generator.py factory-configs/tshirt-factory.json
   ```

4. **Test Generated Factory**
   ```bash
   cd generated-factories/tshirt-factory-001
   docker compose up --build
   ```

5. **Update Frontend**
   - Point tshirt-customizer to new endpoints
   - Configure simple_factory_simulator with new ports

### Benefits of Migration:
- More flexible configuration
- Advanced sensor behaviors
- Better failure simulation
- Conditional workflow steps
- Custom KPI tracking
- Time-series data with TimescaleDB

### Reasons to Keep T-Shirt Factory:
- Simpler to understand
- Faster to set up
- Better for education
- Complete e-commerce example
- Proven reference implementation

---

## 📚 Documentation Cross-Reference

| Topic | T-Shirt Factory | Generic Platform |
|-------|----------------|------------------|
| **Quick Start** | [TSHIRT_FACTORY_README.md](TSHIRT_FACTORY_README.md) | [QUICK_START_GENERIC_FACTORY.md](QUICK_START_GENERIC_FACTORY.md) |
| **Complete Guide** | [TSHIRT_FACTORY_README.md](TSHIRT_FACTORY_README.md) | [GENERIC_FACTORY_SYSTEM.md](GENERIC_FACTORY_SYSTEM.md) |
| **Monitoring** | [simple_factory_simulator/README.md](simple_factory_simulator/README.md) | [simple_factory_simulator/README.md](simple_factory_simulator/README.md) |
| **Architecture** | This document | This document |
| **Configuration** | Docker Compose | JSON Schemas |
| **Examples** | services/ directory | factory-configs/ directory |

---

## 🎓 Learning Path Recommendation

1. **Start with T-Shirt Factory** (Day 1)
   - Understand basic concepts
   - Learn MQTT communication
   - Explore microservices architecture
   - Run the monitoring dashboard

2. **Explore Generic Platform** (Day 2-3)
   - Review JSON schemas
   - Generate an automotive factory
   - Compare with t-shirt factory
   - Understand configuration benefits

3. **Create Custom Factory** (Day 4-5)
   - Design your own machine templates
   - Create a custom factory configuration
   - Generate and run your factory
   - Integrate with monitoring dashboard

4. **Advanced Topics** (Day 6+)
   - Cloud integration
   - Custom KPIs and metrics
   - Complex workflows
   - Production optimization

---

## 📞 Support

- **Issues**: Use GitHub Issues
- **T-Shirt Factory**: See [TSHIRT_FACTORY_README.md](TSHIRT_FACTORY_README.md)
- **Generic Platform**: See [GENERIC_FACTORY_SYSTEM.md](GENERIC_FACTORY_SYSTEM.md)
- **Examples**: Check factory-configs/ directory

---

**Version 1.0** - Two-System Architecture Guide
