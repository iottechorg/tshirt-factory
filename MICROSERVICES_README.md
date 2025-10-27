# T-Shirt Factory - Microservices Architecture (Phase 1)

This document describes the new microservices architecture for the T-Shirt Factory simulator, designed for IoT cloud projects.

## Architecture Overview

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
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│ PostgreSQL     │   │ TimescaleDB    │   │ Redis          │
│ (Transactional)│   │ (Time-Series)  │   │ (Cache)        │
└────────────────┘   └────────────────┘   └────────────────┘
```

## Phase 1 Implementation

### Completed Features

#### 1. Microservices Architecture
- **Machine Services**: Each machine (cutting, sewing, ironing, printing) runs as an independent containerized service
- **Production Orchestrator**: Coordinates production workflow across all machines
- **Shared Libraries**: Common code for MQTT communication, database access, and base machine functionality

#### 2. Improved MQTT Topic Structure
Following ISA-95 industrial standards:

```
# Machine Topics
factory/{site_id}/machine/{machine_type}/{machine_id}/status
factory/{site_id}/machine/{machine_type}/{machine_id}/telemetry
factory/{site_id}/machine/{machine_type}/{machine_id}/command

# Production Topics
factory/{site_id}/production/request
factory/{site_id}/production/{order_id}/status
factory/{site_id}/production/{order_id}/step/{step_name}/status
factory/{site_id}/production/{order_id}/result
```

#### 3. Database Persistence
- **PostgreSQL**: Stores production orders, machine registry, production steps
- **TimescaleDB**: Stores time-series sensor data with automatic aggregation and retention policies
- **Redis**: Ready for caching and real-time state management

## Directory Structure

```
tshirt-factory/
├── services/
│   ├── shared/                      # Shared libraries
│   │   ├── config.py               # Configuration management
│   │   ├── mqtt_client.py          # Enhanced MQTT client
│   │   ├── base_machine.py         # Base machine class
│   │   ├── database.py             # Database utilities
│   │   └── requirements.txt
│   ├── machines/                    # Machine services
│   │   ├── cutting/
│   │   │   ├── cutting_machine.py
│   │   │   ├── machine_service.py
│   │   │   └── Dockerfile
│   │   ├── sewing/
│   │   ├── ironing/
│   │   └── printing/
│   └── production-orchestrator/     # Production coordinator
│       ├── orchestrator.py
│       └── Dockerfile
├── infrastructure/
│   └── databases/
│       ├── init-postgres.sql
│       ├── init-timescaledb.sql
│       └── docker-compose.databases.yml
├── simple_factory_simulator/        # Original monolithic app (legacy)
├── docker-compose.microservices.yml # Main compose file
└── MICROSERVICES_README.md          # This file
```

## Running the Microservices

### Prerequisites
- Docker and Docker Compose
- At least 4GB RAM available for containers

### Quick Start

1. **Start all services:**
   ```bash
   docker compose -f docker-compose.microservices.yml up --build
   ```

2. **Start only databases:**
   ```bash
   docker compose -f infrastructure/databases/docker-compose.databases.yml up -d
   ```

3. **Start specific machines:**
   ```bash
   docker compose -f docker-compose.microservices.yml up cutting-machine-01 sewing-machine-01
   ```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| MQTT Broker | 31883 | MQTT protocol |
| MQTT WebSocket | 9001 | MQTT over WebSocket |
| PostgreSQL | 5432 | Transactional database |
| TimescaleDB | 5433 | Time-series database |
| Redis | 6379 | Cache |
| Factory Simulator (Legacy) | 5001 | Original web UI |
| Frontend | 8080 | T-shirt customizer UI |

## Machine Services

Each machine service:
- Publishes telemetry data every 5 seconds
- Publishes status updates every 10 seconds
- Listens for commands on its command topic
- Processes operations when requested by the orchestrator
- Maintains sensor data with realistic variations

### Sending Commands to Machines

```bash
# Example: Update sensor value
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/machine/cutting/cutting-01/command" \
  -m '{"command": "update_sensor", "sensor_name": "blade_temperature", "value": 35}'

# Example: Set failure rate
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/machine/cutting/cutting-01/command" \
  -m '{"command": "set_failure_rate", "rate": 0.1}'
```

## Production Orchestrator

The orchestrator manages the complete production workflow:
1. Receives production requests via MQTT
2. Coordinates execution across cutting → sewing → ironing → printing
3. Publishes status updates at each step
4. Stores results in PostgreSQL database

### Requesting Production

```bash
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/production/request" \
  -m '{
    "product_name": "T-Shirt",
    "product_details": {
      "material": "Cotton",
      "cut_size": "Large",
      "stitch_type": "Zigzag",
      "thread_color": "Blue",
      "iron_temperature_setpoint": 140,
      "steam_level": "Medium",
      "ink_type": "Water-based"
    }
  }'
```

## Database Schema

### PostgreSQL Tables

- **machines**: Machine registry
- **production_orders**: Production order tracking
- **production_steps**: Individual step execution records
- **machine_status_log**: Machine status history

### TimescaleDB Tables

- **sensor_telemetry**: Raw sensor data (hypertable)
- **sensor_telemetry_hourly**: Aggregated hourly sensor data

## Environment Variables

### Machine Services
- `MACHINE_ID`: Unique machine identifier
- `MACHINE_TYPE`: Type of machine (cutting, sewing, etc.)
- `MQTT_BROKER`: MQTT broker hostname
- `FACTORY_SITE_ID`: Factory site identifier (default: site-01)
- `MACHINE_SENSOR_UPDATE_INTERVAL`: Sensor update interval in seconds
- `MACHINE_DATA_PUBLISH_INTERVAL`: Data publish interval in seconds

### Production Orchestrator
- `PRODUCTION_LOOP_INTERVAL`: Production queue check interval
- `PRODUCTION_SUCCESS_RATE`: Success rate for operations (0.0-1.0)
- `DB_HOST`, `DB_PORT`, `DB_NAME`: PostgreSQL connection
- `TIMESCALE_HOST`: TimescaleDB connection

## Monitoring

### View Logs
```bash
# All services
docker compose -f docker-compose.microservices.yml logs -f

# Specific service
docker compose -f docker-compose.microservices.yml logs -f cutting-machine-01

# Production orchestrator
docker compose -f docker-compose.microservices.yml logs -f production-orchestrator
```

### Monitor MQTT Traffic
```bash
# Subscribe to all factory topics
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Subscribe to specific machine telemetry
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/machine/cutting/+/telemetry" -v

# Subscribe to production results
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/production/+/result" -v
```

### Database Queries

```sql
-- View all production orders
SELECT * FROM production_orders ORDER BY created_at DESC LIMIT 10;

-- View production steps for an order
SELECT * FROM production_steps WHERE order_id = 'order-id-here';

-- View recent sensor data (TimescaleDB)
SELECT * FROM sensor_telemetry
WHERE machine_id = 'cutting-01'
  AND time > NOW() - INTERVAL '1 hour'
ORDER BY time DESC;

-- View aggregated sensor data
SELECT * FROM sensor_telemetry_hourly
WHERE machine_type = 'cutting'
ORDER BY bucket DESC;
```

## Benefits of Microservices Architecture

1. **Scalability**: Each machine can be scaled independently
2. **Resilience**: Machine failures don't affect the entire system
3. **Realistic Simulation**: Machines can be deployed to different networks/regions
4. **Cloud-Ready**: Easy integration with AWS IoT, Azure IoT Hub, etc.
5. **Development**: Teams can work on individual services independently
6. **Testing**: Easier to test individual components and failure scenarios

## Next Steps (Phase 2 & 3)

### Phase 2 - Cloud Integration
- [ ] AWS IoT Core connector
- [ ] Azure IoT Hub connector
- [ ] TLS/SSL for MQTT
- [ ] Authentication and authorization
- [ ] Prometheus + Grafana monitoring
- [ ] Edge gateway simulator

### Phase 3 - Advanced Features
- [ ] Kubernetes deployment manifests
- [ ] Service mesh (Istio/Linkerd)
- [ ] API Gateway
- [ ] Advanced simulation scenarios (failures, network partitions, etc.)
- [ ] Predictive maintenance algorithms
- [ ] Energy consumption modeling

## Troubleshooting

### Services won't start
```bash
# Check service status
docker compose -f docker-compose.microservices.yml ps

# Rebuild specific service
docker compose -f docker-compose.microservices.yml build --no-cache cutting-machine-01

# Remove all containers and start fresh
docker compose -f docker-compose.microservices.yml down -v
docker compose -f docker-compose.microservices.yml up --build
```

### MQTT connection issues
```bash
# Test MQTT broker
mosquitto_pub -h localhost -p 31883 -t test -m "hello"
mosquitto_sub -h localhost -p 31883 -t test

# Check broker logs
docker logs factory-mqtt
```

### Database connection issues
```bash
# Check PostgreSQL
docker exec -it factory-postgres psql -U factory_user -d factory_db

# Check TimescaleDB
docker exec -it factory-timescaledb psql -U factory_user -d factory_timeseries
```

## Contributing

When adding new features to the microservices architecture:
1. Update shared libraries in `services/shared/`
2. Follow the existing machine service pattern
3. Update this README with new features
4. Add appropriate environment variables to docker-compose
5. Test with both isolated and integrated scenarios

## License

Same as the main project.
