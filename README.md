# T-Shirt Factory - Complete IoT Manufacturing System

A comprehensive IoT-enabled t-shirt manufacturing simulation system featuring microservices architecture, real-time machine coordination, and modern web interface for order customization.

## 🏗️ Architecture Overview

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

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.8+ (for CLI tools)

### Start the Complete System

```bash
# Clone and navigate to project
cd tshirt-factory

# Start all services (databases, MQTT, machines, orchestrator)
docker-compose up -d

# Start the web interface
cd tshirt-customizer
npm install
npm start
```

Visit `http://localhost:4200` to access the t-shirt customizer interface.

### Verify System Health

```bash
# Check all services are running
docker-compose ps

# View orchestrator logs
docker-compose logs -f production-orchestrator

# Test machine coordination
python test_orchestrator.py
```

## 📋 Components

### Machine Services (8 Independent Microservices)
Each machine runs as a containerized service with MQTT communication:

- **Cutting Service**: Fabric cutting operations
- **Sewing Service**: Assembly and stitching
- **Ironing Service**: Heat treatment and pressing
- **Printing Service**: Design application
- **Quality Check Service**: Automated inspection
- **Folding Service**: Product preparation
- **Packaging Service**: Final packaging

### Production Orchestrator
Coordinates complex workflows across all machines:
- **Real Machine Coordination**: Waits for actual machine responses (not simulated)
- **Workflow Management**: Configurable production steps with retry logic
- **State Tracking**: Monitors machine availability and performance
- **Error Handling**: Automatic retries and failure recovery

### Web Interface (Angular)
Modern dark-theme t-shirt customization interface:
- **Live Preview**: Real-time t-shirt visualization
- **AI Design Generation**: Automatic design creation using AI
- **Order Management**: Complete order lifecycle tracking
- **Responsive Design**: Mobile-first approach

### Data Persistence
- **PostgreSQL**: Transactional data (orders, inventory)
- **TimescaleDB**: Time-series sensor data and telemetry
- **Redis**: High-performance caching and session storage

## 🔧 Development Setup

### Backend Services

```bash
# Start infrastructure (databases, MQTT)
docker-compose -f infrastructure/databases/docker-compose.databases.yml up -d

# Start machine services
docker-compose up cutting sewing ironing printing qualitycheck folding packaging

# Start orchestrator
docker-compose up production-orchestrator
```

### Frontend Development

```bash
cd tshirt-customizer
npm install
npm start  # Development server at http://localhost:4200
```

### Testing

```bash
# Run orchestrator tests
python test_orchestrator.py

# Build frontend for production
cd tshirt-customizer
npm run build
```

## 📡 API Documentation

### Order Submission
```typescript
POST /production
{
  "material": "cotton",
  "size": "M",
  "color": "navy",
  "collar": "crew",
  "design_keywords": "mountain landscape",
  "quantity": 1
}
```

### Machine Status
Subscribe to MQTT topics:
- `factory/site1/machine/{type}/{id}/status`
- `factory/site1/machine/{type}/{id}/telemetry`

### Workflow Configuration
Workflows defined in JSON format in `/workflows/` directory:
```json
{
  "workflow_id": "tshirt-standard",
  "steps": [
    {
      "step_id": "cut-fabric",
      "operation": "cut_fabric",
      "machine_type": "cutting",
      "timeout_seconds": 30,
      "retry_count": 2
    }
  ]
}
```

## 🐳 Deployment

### Production Deployment

```bash
# Build all services
docker-compose build

# Deploy with production configuration
docker-compose -f docker-compose.yml up -d

# Scale machine services as needed
docker-compose up -d --scale cutting=3 --scale sewing=2
```

### Environment Configuration

Key environment variables:
- `MQTT_BROKER_HOST`: MQTT broker hostname
- `POSTGRES_HOST`: PostgreSQL connection string
- `REDIS_URL`: Redis connection URL
- `ORCHESTRATOR_WORKFLOW_DIR`: Path to workflow definitions

## 🔍 Monitoring & Troubleshooting

### Service Health Checks

```bash
# Check all services
docker-compose ps

# View service logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

### Common Issues

1. **Port Conflicts**: Default ports may conflict with local services
   - PostgreSQL: Change 5432 → 15432 in docker-compose.yml
   - Redis: Change 6379 → 16379 in docker-compose.yml

2. **MQTT Connection Issues**: Ensure broker is running and accessible

3. **Machine Coordination Failures**: Check workflow configurations and machine availability

## 📊 Workflows

Pre-configured production workflows:

- **tshirt-standard**: Basic 4-step t-shirt production
- **premium-tshirt**: Enhanced quality workflow
- **custom-embroidery**: Specialized embroidery process
- **multi-color-print**: Advanced printing workflow
- **complete-production-chain**: Full 7-step manufacturing process

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper testing
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.