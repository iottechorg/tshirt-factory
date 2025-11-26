# T-Shirt Factory Documentation

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [System Architecture](#system-architecture)
3. [Microservices Architecture](#microservices-architecture)
4. [Production Orchestrator](#production-orchestrator)
5. [Machine Coordination Flow](#machine-coordination-flow)
6. [Implementation Details](#implementation-details)
7. [Cloud Integration (Phase 2)](#cloud-integration-phase-2)

---

## Quick Start Guide

### Prerequisites

- Docker and Docker Compose installed
- MQTT broker running (included in docker-compose)
- Python 3.8+ (for CLI tools)

### Starting the System

#### 1. Start All Services

```bash
cd /path/to/tshirt-factory
docker-compose up -d
```

This starts:
- MQTT broker (mosquitto)
- PostgreSQL database
- TimescaleDB for time-series data
- Redis cache
- 7 machine services (cutting, sewing, ironing, printing, quality-check, folding, packaging)
- Production orchestrator
- Factory simulator (legacy)
- Frontend (Angular)

#### 2. Check Service Status

```bash
docker-compose ps
```

#### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f cutting-machine-01
```

#### 4. Test Production

```bash
# Send a test order via MQTT
mosquitto_pub -h localhost -p 31883 -t "factory/site-01/production/request" -m '{"product_type": "tshirt", "quantity": 1, "order_id": "test-001"}'
```

#### 5. Monitor via Web Interface

Open http://localhost:8080 to access the factory dashboard.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             MQTT Broker Layer                                │
│                        (Eclipse Mosquitto)                                   │
│                                                                              │
│  Topics:                                                                     │
│  • factory/{site}/machine/{type}/{id}/{status|telemetry|command}           │
│  • factory/{site}/production/{order_id}/{status|result}                     │
└───────────────────┬──────────────────────────────────────┬──────────────────┘
                    │                                      │
        ┌───────────▼────────┐                 ┌───────────▼────────┐
        │  Machine Services   │                 │    Orchestrator    │
        └───────────┬────────┘                 └───────────┬────────┘
                    │                                      │
    ┌───────┬───────┼───────┬───────┐                     │
    │       │       │       │       │                     │
┌───▼──┐ ┌──▼──┐ ┌─▼───┐ ┌─▼────┐  │                     │
│Cutting│ │Sewing││Iron-││Print-│  │                     │
│  -01  │ │ -01 ││ing  ││ing   │  │                     │
│       │ │     ││ -01 ││ -01  │  │                     │
└───┬───┘ └──┬──┘ └─┬───┘ └─┬────┘  │                     │
    │        │      │       │       │                     │
    └────────┴──────┴───────┴───────┼─────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │      Persistence Layer         │
                    │                                │
                    │  ┌──────────┐  ┌──────────┐   │
                    │  │PostgreSQL│  │Timescale │   │
                    │  │          │  │    DB    │   │
                    │  │Production│  │  Sensor  │   │
                    │  │   Data   │  │   Data   │   │
                    │  └──────────┘  └──────────┘   │
                    │                                │
                    │  ┌──────────┐                 │
                    │  │  Redis   │                 │
                    │  │  Cache   │                 │
                    │  └──────────┘                 │
                    └────────────────────────────────┘
```

### Component Details

#### Machine Services (Independent Microservices)

Each machine service is identical in structure but implements different sensors and process logic.

**Structure:**
- `machine_service.py` - Main service entry point
- `{machine_type}_machine.py` - Machine-specific implementation
- `Dockerfile` - Container configuration
- Shared modules: `base_machine.py`, `mqtt_client.py`, `config.py`, `database.py`

**Key Features:**
- MQTT-based communication
- Sensor data simulation
- Command processing
- Health monitoring
- Database logging

#### Production Orchestrator

Central coordination service that manages production workflows.

**Responsibilities:**
- Order intake and queuing
- Workflow selection and execution
- Machine assignment and coordination
- Progress tracking and reporting
- Error handling and recovery

#### Persistence Layer

**PostgreSQL:** Production data, orders, machine states
**TimescaleDB:** Time-series sensor data, performance metrics
**Redis:** Caching, session management, real-time data

---

## Microservices Architecture

### Architecture Overview

The factory has been redesigned as a distributed system with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                      MQTT Broker (Eclipse Mosquitto)         │
│                  Topic: factory/{site}/...                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│ Cutting        │   │ Sewing         │   │ Ironing        │
│ Machine        │   │ Machine        │   │ Machine        │
│ Service        │   │ Service        │   │ Service        │
└────────────────┘   └────────────────┘   └────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │ Production          │
                   │ Orchestrator        │
                   │ Service             │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │   Persistence       │
                   │     Layer           │
                   └─────────────────────┘
```

### Service Communication

**MQTT Topics Structure:**
```
factory/{site}/machine/{type}/{id}/{message_type}
factory/{site}/production/{order_id}/{status|result}
```

**Message Types:**
- `status` - Machine state changes
- `telemetry` - Sensor data
- `command` - Control commands
- `register` - Service registration

### Deployment

Each service runs in its own Docker container with:
- Independent scaling
- Isolated failure domains
- Shared volume mounts for logs
- Health checks and restart policies

---

## Production Orchestrator

### Overview

The Production Orchestrator is a sophisticated workflow-based system that coordinates multiple machines in the factory to produce products according to defined workflows.

### Key Features

#### ✅ Real Machine Coordination
- **Machine State Tracking**: Tracks each machine's status (idle, busy, error)
- **Response Handling**: Waits for actual machine responses via MQTT
- **Timeout Management**: Configurable timeouts for each workflow step
- **Queue Management**: Intelligently assigns work to available machines

#### ✅ Workflow Management
- **JSON-Based Workflows**: Define workflows in JSON files
- **Dynamic Loading**: Workflows loaded from `/workflows` directory
- **Runtime Adjustment**: Modify workflow parameters without restart
- **Multiple Product Types**: Support for different product workflows

#### ✅ Production Monitoring
- **Real-time Metrics**: Order status, machine utilization, throughput
- **Performance Tracking**: Step completion times, error rates
- **Historical Data**: Production statistics and trends

### Workflow Execution

1. **Order Intake**: Receive production orders via MQTT
2. **Workflow Selection**: Choose appropriate workflow based on product type
3. **Step Execution**: For each workflow step:
   - Find available machine of required type
   - Send processing command
   - Wait for completion response
   - Handle success/failure/retry logic
4. **Completion**: Mark order as complete when all steps finish

---

## Machine Coordination Flow

### Complete Order Processing Flow

#### Timeline View: T-Shirt Order (4 Steps)

```
Time  | Orchestrator              | Cutting Machine    | Sewing Machine     | Ironing Machine    | Printing Machine
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=0   | Receive Order             |                    |                    |                    |
      | Select Workflow           |                    |                    |                    |
      | Queue Order               |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=1   | STEP 1: Start             |                    |                    |                    |
      | Find: cutting-01 (IDLE)   |                    |                    |                    |
      | Mark: cutting-01 BUSY     |                    |                    |                    |
      | Send Command →            |                    |                    |                    |
      |                           | Receive Command    |                    |                    |
      |                           | Validate Data      |                    |                    |
      |                           | Start Processing   |                    |                    |
t=2   | Wait for response...      | Processing...      |                    |                    |
t=3   |                           | Processing...      |                    |                    |
t=4   |                           | Processing...      |                    |                    |
t=5   |                           | Processing...      |                    |                    |
t=6   |                           | Complete!          |                    |                    |
      |                           | Send Response →    |                    |                    |
      | ← Receive Response        |                    |                    |                    |
      | Status: SUCCESS           |                    |                    |                    |
      | Mark: cutting-01 IDLE     |                    |                    |                    |
      | Track: time=5.2s          |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=7   | STEP 2: Start             |                    |                    |                    |
      | Find: sewing-01 (IDLE)    |                    |                    |                    |                    |
      | Mark: sewing-01 BUSY      |                    |                    |                    |
      | Send Command →            |                    |                    |                    |
      |                           |                    | Receive Command    |                    |
      |                           |                    | Start Processing   |                    |
t=8   | Wait for response...      |                    | Processing...      |                    |
t=9   |                           |                    | Processing...      |                    |
t=10  |                           |                    | Processing...      |                    |
t=11  |                           |                    | Processing...      |                    |
t=12  |                           |                    | Complete!          |                    |
      |                           |                    | Send Response →    |                    |
      | ← Receive Response        |                    |                    |                    |
      | Status: SUCCESS           |                    |                    |                    |
      | Mark: sewing-01 IDLE      |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=13  | STEP 3: Start             |                    |                    |                    |
      | Find: ironing-01 (IDLE)   |                    |                    |                    |
      | Mark: ironing-01 BUSY     |                    |                    |                    |
```

### Coordination States

**Machine States:**
- `IDLE` - Available for work
- `BUSY` - Currently processing
- `ERROR` - Failed state
- `MAINTENANCE` - Under maintenance

**Order States:**
- `QUEUED` - Waiting for processing
- `PROCESSING` - Currently being worked on
- `COMPLETED` - Successfully finished
- `FAILED` - Processing failed

---

## Implementation Details

### What Was Implemented

#### ✅ Complete Workflow-Based Machine Coordination

The production orchestrator now provides **real machine coordination** where:

1. **Order arrives** → Orchestrator selects workflow
2. **For each step in workflow**:
   - Orchestrator finds available machine
   - Sends command via MQTT
   - **WAITS for machine response** (with timeout)
   - Machine processes work (simulates real work time 4-7s)
   - Machine responds with success/failure
   - Orchestrator receives response
   - On success → proceed to next step
   - On failure → retry (if configured) or fail order
3. **All steps complete** → Order marked as completed

#### Key Implementation Details

##### 1. Machine Response Handling

```python
def _execute_step(self, order, step, machine_id):
    # Send command to machine
    command = {
        "command": "process",
        "process_data": {...},
        "order_id": order["order_id"],
        "step_id": step["id"]
    }

    # Publish command
    self.mqtt_client.publish(command_topic, json.dumps(command))

    # Wait for response with timeout
    response = self._wait_for_response(order["order_id"], step["id"], timeout_seconds)

    if response and response.get("status") == "success":
        return True
    else:
        return False
```

##### 2. Workflow Engine

- **JSON Workflow Definitions**: Stored in `/workflows/` directory
- **Dynamic Loading**: Workflows loaded at startup and reloadable
- **Step Dependencies**: Sequential execution with proper ordering
- **Error Recovery**: Configurable retry logic and failure handling

##### 3. Machine State Management

- **Real-time Tracking**: MQTT-based state updates
- **Health Monitoring**: Automatic detection of failed machines
- **Load Balancing**: Intelligent assignment based on current load

### Database Schema

#### Production Data (PostgreSQL)
- `orders` - Production orders
- `order_steps` - Individual workflow steps
- `machines` - Machine registry and status
- `workflows` - Workflow definitions

#### Time-Series Data (TimescaleDB)
- `machine_telemetry` - Sensor readings over time
- `production_metrics` - Performance statistics
- `system_events` - Audit trail

---

## Cloud Integration (Phase 2)

### Overview

Phase 2 adds enterprise-grade cloud connectivity, security, and monitoring to the T-Shirt Factory, making it production-ready for real IoT cloud deployments.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Cloud Layer                                  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   AWS IoT    │  │  Azure IoT   │  │  Generic     │             │
│  │   Core       │  │    Hub       │  │  Cloud API   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                      │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          │  TLS/SSL         │  TLS/SSL         │  HTTPS
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────────────┐
│                         Edge Layer                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Cloud Bridge │  │   Security   │  │  Monitoring │             │
│  │              │  │   Gateway    │  │   Service   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                      │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ MQTT     │       │ Secure   │       │ Metrics  │
    │ Broker   │       │ Comm     │       │ Export   │
    └──────────┘       └──────────┘       └──────────┘
```

### Key Components

#### Cloud Bridge Service
- **Multi-Cloud Support**: AWS IoT Core, Azure IoT Hub, Generic REST APIs
- **Protocol Translation**: MQTT ↔ Cloud protocols
- **Device Registry**: Cloud device management
- **Command Routing**: Bidirectional command flow

#### Security Gateway
- **TLS/SSL Termination**: Secure cloud connections
- **Certificate Management**: Device certificates and rotation
- **Authentication**: JWT tokens, API keys
- **Authorization**: Role-based access control

#### Monitoring Service
- **Metrics Collection**: System and application metrics
- **Log Aggregation**: Centralized logging
- **Alerting**: Threshold-based notifications
- **Dashboards**: Real-time monitoring views

### Deployment Options

#### 1. Full Cloud Deployment
- All services run in cloud containers
- Direct cloud connectivity
- Managed databases and message queues

#### 2. Hybrid Deployment
- Edge services on-premises
- Cloud bridge for connectivity
- Selective data synchronization

#### 3. Air-Gapped Deployment
- Complete local deployment
- Optional cloud backup/sync
- Offline operation capability

### Security Features

- **End-to-End Encryption**: TLS 1.3, certificate-based auth
- **Device Security**: Secure boot, firmware updates
- **Network Security**: VPC isolation, security groups
- **Data Protection**: Encryption at rest and in transit
- **Audit Logging**: Comprehensive security event logging

---

## API Reference

### MQTT Topics

#### Machine Communication
```
factory/{site}/machine/{type}/{id}/status
factory/{site}/machine/{type}/{id}/telemetry
factory/{site}/machine/{type}/{id}/command
factory/{site}/machine/{type}/{id}/register
```

#### Production Coordination
```
factory/{site}/production/request
factory/{site}/production/{order_id}/status
factory/{site}/production/{order_id}/result
```

#### Orchestrator Control
```
factory/{site}/orchestrator/workflow/adjust
factory/{site}/orchestrator/performance/query
```

### REST API Endpoints

#### Factory Simulator (Port 5001)
- `GET /api/orders` - List active orders
- `POST /api/orders` - Create new order
- `GET /api/machines` - Machine status
- `GET /api/metrics` - System metrics

#### Frontend (Port 8080)
- Web dashboard for monitoring and control
- Real-time updates via WebSocket
- Order management interface

---

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check container status
docker-compose ps

# View service logs
docker-compose logs {service_name}

# Restart specific service
docker-compose restart {service_name}
```

#### MQTT Connection Issues
```bash
# Check MQTT broker
docker-compose logs mqttbroker

# Test MQTT connection
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v
```

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs postgres
docker-compose logs timescaledb

# Test database connection
docker-compose exec postgres psql -U factory_user -d factory_db
```

### Performance Tuning

#### Memory Usage
- Adjust container memory limits in `docker-compose.yml`
- Monitor with `docker stats`

#### Network Latency
- Optimize MQTT QoS settings
- Use persistent connections
- Implement connection pooling

#### Database Performance
- Monitor query performance
- Adjust connection pool sizes
- Implement proper indexing

---

## Development

### Project Structure
```
tshirt-factory/
├── services/                    # Microservices
│   ├── machines/               # Machine services
│   │   ├── cutting/
│   │   ├── sewing/
│   │   └── ...
│   └── production-orchestrator/
├── workflows/                  # Workflow definitions
├── infrastructure/             # Database schemas
├── mqtt/                       # MQTT configuration
├── docs/                       # Documentation
├── tshirt-customizer/          # Frontend application
└── docker-compose.yml          # Service orchestration
```

### Adding New Machines

1. Create machine directory: `services/machines/{machine_type}/`
2. Implement machine class inheriting from `BaseMachine`
3. Add Dockerfile with proper COPY paths
4. Update docker-compose.yml
5. Add workflow steps if needed

### Extending Workflows

1. Create JSON workflow file in `/workflows/`
2. Define steps with machine types and parameters
3. Test workflow execution
4. Monitor performance metrics

---

## Contributing

### Code Standards
- Python: PEP 8 with type hints
- Docker: Multi-stage builds, security best practices
- Documentation: Clear, comprehensive, up-to-date

### Testing
- Unit tests for business logic
- Integration tests for service communication
- Performance tests for high-load scenarios
- End-to-end tests for complete workflows

### Deployment
- Automated CI/CD pipelines
- Blue-green deployments
- Rollback procedures
- Monitoring and alerting

---

*This documentation is automatically generated from multiple source files and kept up-to-date with the codebase.*