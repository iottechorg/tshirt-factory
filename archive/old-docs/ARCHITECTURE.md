# T-Shirt Factory - System Architecture

## High-Level Architecture

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

## Component Details

### Machine Services (Independent Microservices)

Each machine service is identical in structure but implements different sensors and process logic.

```
┌─────────────────────────────────────────┐
│       Machine Service Container         │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     Machine Service Main Loop     │  │
│  │  - Sensor updates (2s interval)   │  │
│  │  - Telemetry publish (5s)         │  │
│  │  - Status publish (10s)           │  │
│  └───────┬──────────────────────┬────┘  │
│          │                      │       │
│  ┌───────▼───────┐     ┌────────▼────┐ │
│  │ MQTT Client   │     │   Machine   │ │
│  │ - Subscribe   │     │   Instance  │ │
│  │ - Publish     │     │   - Sensors │ │
│  │ - Commands    │     │   - Process │ │
│  └───────────────┘     └─────────────┘ │
│                                         │
│  Environment:                           │
│  - MACHINE_ID                           │
│  - MACHINE_TYPE                         │
│  - MQTT_BROKER                          │
└─────────────────────────────────────────┘
```

### Production Orchestrator

```
┌───────────────────────────────────────────────┐
│     Production Orchestrator Container         │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │      Production Queue Manager           │ │
│  │  - Receives production requests         │ │
│  │  - Queues orders                        │ │
│  │  - Processes sequentially               │ │
│  └────────┬──────────────────────┬─────────┘ │
│           │                      │           │
│  ┌────────▼──────────┐  ┌────────▼────────┐ │
│  │ Workflow Engine    │  │  MQTT Client    │ │
│  │                    │  │                 │ │
│  │ Steps:             │  │ - Subscribe to  │ │
│  │ 1. Cutting         │  │   requests      │ │
│  │ 2. Sewing          │  │ - Send commands │ │
│  │ 3. Ironing         │  │ - Publish status│ │
│  │ 4. Printing        │  └─────────────────┘ │
│  │                    │                      │
│  │ For each step:     │  ┌─────────────────┐ │
│  │ - Find machine     │  │  DB Connector   │ │
│  │ - Send command     │  │                 │ │
│  │ - Wait for result  │  │ - Save orders   │ │
│  │ - Log to DB        │  │ - Save steps    │ │
│  │ - Publish status   │  │ - Query status  │ │
│  └────────────────────┘  └─────────────────┘ │
└───────────────────────────────────────────────┘
```

## Data Flow

### Machine Telemetry Flow

```
┌──────────┐         ┌──────────┐         ┌──────────────┐
│ Machine  │  MQTT   │   MQTT   │  MQTT   │  Subscribers │
│ Service  ├────────►│  Broker  ├────────►│  (Optional)  │
│          │ Publish │          │ Forward │              │
└────┬─────┘         └──────────┘         └──────────────┘
     │
     │ Every 5s
     │
     ▼
┌──────────────────────────────────────┐
│ Topic: factory/site-01/machine/      │
│        cutting/cutting-01/telemetry  │
│                                      │
│ Payload:                             │
│ {                                    │
│   "machine_id": "cutting-01",        │
│   "machine_type": "cutting",         │
│   "sensor_data": {                   │
│     "blade_temperature": 32.5,       │
│     "blade_pressure": 1.2,           │
│     "cut_speed": 0.25,               │
│     "motor_current": 0.8             │
│   },                                 │
│   "runtime_state": "idle",           │
│   "timestamp": 1729584000            │
│ }                                    │
└──────────────────────────────────────┘
```

### Production Request Flow

```
1. Request Received
   ┌─────────┐
   │ Client  │
   └────┬────┘
        │ mosquitto_pub
        ▼
   ┌─────────────────────────────────────┐
   │ Topic: factory/site-01/production/  │
   │        request                      │
   │                                     │
   │ {                                   │
   │   "product_name": "T-Shirt",        │
   │   "product_details": {...}          │
   │ }                                   │
   └─────────────────────────────────────┘
        │
        ▼
   ┌──────────────────┐
   │  Orchestrator    │
   │  - Creates order │
   │  - Queues        │
   └────┬─────────────┘
        │

2. Execute Step 1: Cutting
        │
        ▼
   ┌──────────────────────────────────────┐
   │ Command Topic:                        │
   │ factory/site-01/machine/cutting/      │
   │         cutting-01/command            │
   │                                       │
   │ {                                     │
   │   "command": "process",               │
   │   "process_data": {                   │
   │     "material": "Cotton",             │
   │     "cut_size": "Large"               │
   │   }                                   │
   │ }                                     │
   └──────────────────────────────────────┘
        │
        ▼
   ┌──────────────┐
   │ Cutting      │
   │ Machine      │ Processes (5s)
   │ Service      │
   └──────────────┘
        │
        ▼
   ┌──────────────────────────────────────┐
   │ Status Topic:                         │
   │ factory/site-01/production/           │
   │         {order_id}/step/cutting/status│
   │                                       │
   │ {                                     │
   │   "name": "cutting",                  │
   │   "status": "success",                │
   │   "machine_id": "cutting-01"          │
   │ }                                     │
   └──────────────────────────────────────┘

3. Repeat for Sewing, Ironing, Printing

4. Final Result
        │
        ▼
   ┌──────────────────────────────────────┐
   │ Result Topic:                         │
   │ factory/site-01/production/           │
   │         {order_id}/result             │
   │                                       │
   │ {                                     │
   │   "order_id": "uuid",                 │
   │   "status": "completed",              │
   │   "steps": [...],                     │
   │   "completed_at": timestamp           │
   │ }                                     │
   └──────────────────────────────────────┘
        │
        ▼
   ┌──────────────┐
   │ PostgreSQL   │
   │ - Save order │
   │ - Save steps │
   └──────────────┘
```

## Database Schema

### PostgreSQL (Transactional Data)

```
┌─────────────────────────────────────┐
│ machines                            │
├─────────────────────────────────────┤
│ PK machine_id     VARCHAR(100)      │
│    machine_type   VARCHAR(50)       │
│    machine_name   VARCHAR(100)      │
│    created_at     TIMESTAMP         │
│    updated_at     TIMESTAMP         │
└─────────────────────────────────────┘
                │
                │ 1:N
                ▼
┌─────────────────────────────────────┐
│ production_orders                   │
├─────────────────────────────────────┤
│ PK order_id       VARCHAR(100)      │
│    product_name   VARCHAR(200)      │
│    product_details JSONB            │
│    status         VARCHAR(50)       │
│    created_at     TIMESTAMP         │
│    completed_at   TIMESTAMP         │
└─────────────────────────────────────┘
                │
                │ 1:N
                ▼
┌─────────────────────────────────────┐
│ production_steps                    │
├─────────────────────────────────────┤
│ PK step_id        SERIAL             │
│ FK order_id       VARCHAR(100)      │
│ FK machine_id     VARCHAR(100)      │
│    step_name      VARCHAR(50)       │
│    status         VARCHAR(50)       │
│    process_data   JSONB             │
│    started_at     TIMESTAMP         │
│    completed_at   TIMESTAMP         │
└─────────────────────────────────────┘
```

### TimescaleDB (Time-Series Data)

```
┌─────────────────────────────────────┐
│ sensor_telemetry (Hypertable)       │
├─────────────────────────────────────┤
│    time           TIMESTAMPTZ PK    │
│    machine_id     VARCHAR(100)      │
│    machine_type   VARCHAR(50)       │
│    sensor_name    VARCHAR(100)      │
│    sensor_value   DOUBLE PRECISION  │
│    runtime_state  VARCHAR(50)       │
└─────────────────────────────────────┘
                │
                │ Continuous Aggregate
                ▼
┌─────────────────────────────────────┐
│ sensor_telemetry_hourly             │
├─────────────────────────────────────┤
│    bucket         TIMESTAMPTZ       │
│    machine_id     VARCHAR(100)      │
│    machine_type   VARCHAR(50)       │
│    sensor_name    VARCHAR(100)      │
│    avg_value      DOUBLE PRECISION  │
│    min_value      DOUBLE PRECISION  │
│    max_value      DOUBLE PRECISION  │
│    sample_count   INTEGER           │
└─────────────────────────────────────┘
```

## Deployment Architecture

### Docker Compose Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Host                          │
│                                                         │
│  ┌────────────────────────────────────────────────┐    │
│  │          factory-network (bridge)              │    │
│  │                                                │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    │
│  │  │ cutting  │  │ sewing   │  │ ironing  │    │    │
│  │  │   -01    │  │   -01    │  │   -01    │    │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘    │    │
│  │       │             │             │           │    │
│  │       └─────────────┼─────────────┘           │    │
│  │                     │                         │    │
│  │              ┌──────▼──────┐                  │    │
│  │              │    MQTT     │                  │    │
│  │              │   Broker    │                  │    │
│  │              └──────┬──────┘                  │    │
│  │                     │                         │    │
│  │              ┌──────▼──────┐                  │    │
│  │              │ Production  │                  │    │
│  │              │Orchestrator │                  │    │
│  │              └──────┬──────┘                  │    │
│  │                     │                         │    │
│  │       ┌─────────────┼─────────────┐           │    │
│  │       │             │             │           │    │
│  │  ┌────▼────┐  ┌─────▼─────┐  ┌───▼────┐     │    │
│  │  │Postgres │  │Timescale  │  │ Redis  │     │    │
│  │  │   DB    │  │    DB     │  │        │     │    │
│  │  └─────────┘  └───────────┘  └────────┘     │    │
│  │                                                │    │
│  └────────────────────────────────────────────────┘    │
│                                                         │
│  Exposed Ports:                                        │
│  - 31883: MQTT                                         │
│  - 9001:  MQTT WebSocket                               │
│  - 5432:  PostgreSQL                                   │
│  - 5433:  TimescaleDB                                  │
│  - 6379:  Redis                                        │
│  - 5001:  Web UI (legacy)                              │
└─────────────────────────────────────────────────────────┘
```

## Scaling Architecture

### Horizontal Scaling Example

```
Before (Single Machine per Type):
┌──────────┐
│ Cutting  │
│   -01    │
└────┬─────┘
     │
     ▼
┌──────────┐
│  MQTT    │
└──────────┘

After (Multiple Machines):
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Cutting  │  │ Cutting  │  │ Cutting  │
│   -01    │  │   -02    │  │   -03    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   ▼
              ┌──────────┐
              │  MQTT    │
              └──────────┘
                   │
                   ▼
              ┌──────────┐
              │Production│
              │Orchestr. │
              │          │
              │ Load     │
              │ Balancer │
              └──────────┘
```

## Network Communication

### Port Mapping

| Container | Internal Port | External Port | Protocol |
|-----------|--------------|---------------|----------|
| mqttbroker | 1883 | 31883 | MQTT |
| mqttbroker | 9001 | 9001 | WebSocket |
| postgres | 5432 | 5432 | PostgreSQL |
| timescaledb | 5432 | 5433 | PostgreSQL |
| redis | 6379 | 6379 | Redis |
| factory-simulator | 5001 | 5001 | HTTP |

### Service Communication

All services communicate via:
1. **MQTT** (pub/sub messaging)
2. **Database** (shared persistence)
3. **No direct HTTP** between services (except legacy web UI)

This follows the **event-driven architecture** pattern.

## Comparison: Before vs After

| Aspect | Before (Monolithic) | After (Microservices) |
|--------|---------------------|----------------------|
| Processes | 1 | 11+ |
| Scaling | Vertical only | Horizontal per service |
| Deployment | Single container | Multi-container |
| Database | None | 3 databases |
| MQTT Topics | 2 simple topics | Hierarchical structure |
| Fault Tolerance | None | Service isolation |
| Development | Tightly coupled | Independent services |
| Cloud Ready | No | Yes |

---

This architecture provides a solid foundation for IoT cloud projects with proper separation of concerns, scalability, and maintainability.
