# Documentation Index

> Complete reference for the Universal Factory Simulation Platform

---

## 📚 Quick Navigation

### 👤 Just Getting Started?
1. **Start here**: [../README.md](../README.md) - Overview, quick start, and file structure
2. **5-minute setup**: Follow the Quick Start section in README.md
3. **Running example**: `python3 tools/factory_generator.py factory-configs/tshirt-factory.json`

---

## 📖 Complete Documentation

### [README.md](../README.md) - Main Entry Point
**What**: System overview, quick start guide, file structure
**When to read**: First time using the system
**Contents**:
- What this system does
- 5-minute quick start (3 options)
- Factory library (5 pre-built examples)
- System architecture diagram
- Common commands
- File structure
- Troubleshooting

### [ARCHITECTURE.md](ARCHITECTURE.md) - System Design Deep Dive
**What**: Technical architecture, data flow, component details
**When to read**: Understanding how the system works internally
**Contents**:
- Three-layer design (configuration, generation, execution)
- Core components (MQTT broker, machines, orchestrator, monitoring, databases)
- Complete data flow diagrams
- Service communication patterns
- MQTT protocol details
- Database schemas (PostgreSQL & TimescaleDB)
- Extension points

### [EXTENDING.md](EXTENDING.md) - Customization Guide
**What**: How to create custom factories, machines, and frontends
**When to read**: Building your own factory or extending the system
**Contents**:
- Creating custom factories (step-by-step)
- Creating custom machines (Python class template)
- Creating custom frontends (Angular or HTML/JS)
- Extending services (orchestrator, monitoring)
- Custom workflows (JSON structure)

---

## 🚀 Common Tasks

| Task | Resource |
|------|----------|
| **Generate a factory** | [README.md](../README.md#-5-minute-quick-start) |
| **Run generated factory** | [README.md](../README.md#-5-minute-quick-start) |
| **Understand architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Create custom factory** | [EXTENDING.md](EXTENDING.md#creating-custom-factories) |
| **Create custom machine** | [EXTENDING.md](EXTENDING.md#creating-custom-machines) |
| **Build custom frontend** | [EXTENDING.md](EXTENDING.md#creating-custom-frontends) |
| **Extend services** | [EXTENDING.md](EXTENDING.md#extending-services) |
| **Understand MQTT** | [ARCHITECTURE.md](ARCHITECTURE.md#mqtt-protocol-details) |
| **Troubleshoot issues** | [README.md](../README.md#-troubleshooting) |

---

## 📁 File References in Docs

### Configuration Files
- **Machine templates**: `machine-templates/*.json`
- **Factory configs**: `factory-configs/*.json`
- **Workflows**: `workflows/*.json`
- **Schemas**: `schemas/*.json`

### Generated Factories
- **Location**: `generated-factories/{factory-id}/`
- **Structure**: See README.md file structure section

### Source Code
- **Generator**: `tools/factory_generator.py`
- **Shared modules**: `shared/`
- **Monitoring**: `monitoring-service/`
- **Orchestrator**: `production-orchestrator/`

### Frontends
- **T-Shirt**: `tshirt-customizer/` (Angular)
- **Vehicle**: `vehicle-customizer/` (HTML/JS)
- **API Gateway**: `simple_factory_simulator/` (Flask)

---

## 🎯 Learning Path

**Beginner** (30 minutes)
1. Read [README.md](../README.md) - Overview section
2. Run [Quick Start](../README.md#-5-minute-quick-start)
3. Explore generated factory: `docker compose logs -f`

**Intermediate** (1-2 hours)
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Understand design
2. Check MQTT messages: `mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v`
3. Query database: See Troubleshooting section

**Advanced** (2-4 hours)
1. Read [EXTENDING.md](EXTENDING.md) - Customization guide
2. Create custom factory config
3. Generate and run custom factory
4. Modify workflows or add machine types

**Expert** (ongoing)
1. Extend services (custom orchestrator logic)
2. Build custom frontends
3. Integrate with external systems via MQTT

---

## 🔗 Cross-References

### README.md Links in Docs
- Quick start commands
- File structure reference
- Troubleshooting guide
- Technology stack

### ARCHITECTURE.md Links in Docs
- Component details
- Data flow diagrams
- Database schemas
- MQTT protocol

### EXTENDING.md Links in Docs
- Step-by-step customization
- Code templates
- Example configurations

---

## 📊 Architecture Overview

```
User Reads README.md
         ↓
    Understands What (System does)
    Understands Why (Problem it solves)
    Understands How (Quick start)
         ↓
      Runs Factory
         ↓
    Questions: "How does it work internally?"
         ↓
User Reads ARCHITECTURE.md
         ↓
    Understands Components
    Understands Data Flow
    Understands Messaging
    Understands Databases
         ↓
      Comfortable with System
         ↓
    Questions: "Can I customize it?"
         ↓
User Reads EXTENDING.md
         ↓
    Creates Custom Factory
    Extends Machines
    Builds Custom Frontend
    Modifies Workflows
         ↓
      System Fully Mastered
```

---

## ✅ Documentation Checklist

- [x] README.md - Quick start & overview
- [x] ARCHITECTURE.md - Technical deep dive
- [x] EXTENDING.md - Customization guide
- [x] This index file - Navigation

---

## 📝 File Locations

**At a glance**:
```
tshirt-factory/
├── README.md               ← START HERE
├── docs/
│   ├── index.md           ← You are here
│   ├── ARCHITECTURE.md    ← Technical details
│   └── EXTENDING.md       ← How to customize
├── factory-configs/       ← Pre-built factories
├── machine-templates/     ← Reusable machines
├── tools/                 ← Generator tool
├── shared/                ← Shared Python code
└── generated-factories/   ← Your running factories
```

---

## 🆘 Need Help?

1. **Quick questions?** Check README.md [Troubleshooting](../README.md#-troubleshooting)
2. **Understanding design?** Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Want to customize?** Follow [EXTENDING.md](EXTENDING.md)
4. **Still stuck?** Check logs: `docker compose logs -f`

---

**Version**: 1.0 | **Updated**: November 2025 | **Status**: Production Ready ✅
