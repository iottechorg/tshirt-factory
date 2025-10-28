# T-Shirt Factory System

## Complete E-Commerce Manufacturing System

A full-stack IoT-enabled t-shirt manufacturing system that demonstrates end-to-end production from customer order to finished product.

---

## 🎯 Purpose

This is the **original reference implementation** - a complete working example of:
- Customer-facing e-commerce interface
- IoT-enabled manufacturing workflow
- Real-time production monitoring
- MQTT-based machine communication
- Microservices architecture

**Use this system to:**
- Learn full-stack IoT application development
- Understand manufacturing workflow orchestration
- Test e-commerce to production integration
- Demonstrate real-time factory monitoring

---

## 🏭 System Overview

### Customer Journey
```
Customer → tshirt-customizer (Angular) → Order Placed → MQTT
                                                          ↓
                                                    Orchestrator
                                                          ↓
                                          Machine Workflow Execution
                                                          ↓
                                                    Finished Product
```

### Factory Workflow
1. **Cutting Machine** - Cuts fabric based on size
2. **Sewing Machine** - Sews t-shirt pieces together
3. **Quality Check Machine** - Inspects finished product
4. **Packaging Machine** - Packages for shipment

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 16+ (for Angular app)
- Python 3.9+ (optional, for monitoring)

### 1. Start the T-Shirt Factory

```bash
# Navigate to factory services
cd services

# Start all machines and orchestrator
docker-compose up --build
```

This starts:
- 4 machine services (cutting, sewing, quality-check, packaging)
- 1 orchestrator service
- MQTT broker (Mosquitto)
- PostgreSQL database
- Redis cache

### 2. Start the Customer Frontend (Optional)

```bash
# Navigate to customizer
cd tshirt-customizer

# Install dependencies
npm install

# Start development server
ng serve

# Open browser: http://localhost:4200
```

### 3. Start the Monitoring Dashboard (Optional)

```bash
# Navigate to simulator
cd simple_factory_simulator

# Install dependencies
pip install -r requirements.txt

# Start Flask app
python app.py

# Open browser: http://localhost:5001
```

---

## 📁 File Structure

```
services/
├── machines/
│   ├── cutting/              # Fabric cutting machine
│   ├── sewing/               # Sewing machine
│   ├── qualitycheck/         # Quality inspection
│   └── packaging/            # Final packaging
├── orchestrator/             # Production workflow coordinator
└── docker-compose.yml        # Services configuration

tshirt-customizer/            # Angular customer interface
├── src/
│   ├── app/
│   │   ├── tshirt-selector/  # Product customization UI
│   │   └── services/         # API services
│   └── environments/         # Configuration

simple_factory_simulator/     # Flask monitoring dashboard
├── templates/
│   └── index.html           # Dashboard UI
├── static/                  # CSS/JS assets
└── app.py                   # Flask application
```

---

## 🔧 Configuration

### Machine Configuration

Each machine is configured via environment variables in `docker-compose.yml`:

```yaml
cutting:
  environment:
    - MACHINE_ID=cutting-01
    - MQTT_BROKER=mqttbroker
    - MQTT_PORT=1883
    - DATABASE_HOST=postgres
```

### Customer Frontend Configuration

Edit `tshirt-customizer/src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000',
  mqttBroker: 'ws://localhost:9001'
};
```

### Monitoring Dashboard Configuration

Edit `simple_factory_simulator/config.py`:

```python
API_BASE_URL = "http://localhost:5000"
MQTT_BROKER = "localhost"
MQTT_WS_PORT = 9001
```

---

## 💡 Usage Examples

### Place a T-Shirt Order (via Angular App)

1. Open http://localhost:4200
2. Select size (S, M, L, XL)
3. Choose color (White, Black, Red, Blue)
4. Enter custom text (optional)
5. Click "Place Order"

### Place Order via MQTT

```bash
mosquitto_pub -h localhost -p 1883 \
  -t "factory/tshirt-factory/production/request" \
  -m '{
    "product_type": "tshirt",
    "size": "L",
    "color": "blue",
    "custom_text": "IoT Factory"
  }'
```

### Monitor Production via Dashboard

1. Open http://localhost:5001
2. **Machine Monitoring Tab:**
   - View all machine statuses
   - Update sensor values
   - Configure failure rates
3. **Production Monitoring Tab:**
   - Start production manually
   - Adjust success rates
4. **Test Cases Tab:**
   - Run automated tests
   - Generate random orders

### Monitor MQTT Messages

```bash
# Subscribe to all factory topics
mosquitto_sub -h localhost -p 1883 -t "factory/#" -v

# Subscribe to production status
mosquitto_sub -h localhost -p 1883 -t "factory/tshirt-factory/production/status" -v

# Subscribe to specific machine
mosquitto_sub -h localhost -p 1883 -t "factory/tshirt-factory/machines/cutting-01/#" -v
```

### Query Database

```bash
# Connect to PostgreSQL
docker exec -it tshirt-factory-postgres psql -U factory_user -d tshirt_factory

# View production orders
SELECT * FROM production_orders ORDER BY created_at DESC LIMIT 10;

# View machine telemetry
SELECT * FROM machine_telemetry WHERE machine_id = 'cutting-01' ORDER BY timestamp DESC LIMIT 20;

# View production statistics
SELECT
  product_type,
  COUNT(*) as total_orders,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
FROM production_orders
GROUP BY product_type;
```

---

## 📊 MQTT Topic Structure

### Production Topics
```
factory/tshirt-factory/production/request    # New order requests
factory/tshirt-factory/production/status     # Production status updates
factory/tshirt-factory/production/complete   # Completed orders
```

### Machine Topics
```
factory/tshirt-factory/machines/{machine_id}/status      # Machine status
factory/tshirt-factory/machines/{machine_id}/telemetry   # Sensor data
factory/tshirt-factory/machines/{machine_id}/command     # Control commands
factory/tshirt-factory/machines/{machine_id}/operation   # Operation results
```

---

## 🎨 Frontend Features (tshirt-customizer)

### Modern Tailwind CSS Design
- Gradient backgrounds (indigo-purple)
- Card-based layout with shadows
- Interactive size/color selectors
- Visual color picker with checkmarks
- Responsive grid layout
- Real-time order status
- Animation effects

### Key Components
- **TshirtSelectorComponent** - Main customization interface
- **OrderService** - API integration
- **MqttService** - Real-time updates

---

## 📈 Monitoring Dashboard Features (simple_factory_simulator)

### Machine Monitoring
- Real-time machine status table
- Sensor value updates
- Failure rate configuration
- Machine selection and control

### Production Management
- Manual production triggering
- Product name/details generation
- Success rate adjustment
- Production status tracking

### Test Automation
- Predefined test cases
- Random test generation
- Automated production intervals
- Production results history

---

## 🔍 Troubleshooting

### Machines Not Starting

```bash
# Check Docker logs
docker-compose logs cutting
docker-compose logs orchestrator

# Verify MQTT broker
docker-compose logs mqttbroker

# Check database
docker-compose logs postgres
```

### Frontend Connection Issues

1. Verify API is running: `curl http://localhost:5000/health`
2. Check MQTT WebSocket: `telnet localhost 9001`
3. Check browser console for errors
4. Verify CORS configuration

### Production Not Starting

1. Check orchestrator logs: `docker-compose logs orchestrator`
2. Verify all machines are healthy: `curl http://localhost:5000/machines`
3. Check MQTT connectivity: `mosquitto_sub -h localhost -p 1883 -t "factory/#"`
4. Verify database connection

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up --build

# Backup database
docker exec tshirt-factory-postgres pg_dump -U factory_user tshirt_factory > backup.sql

# Restore database
docker exec -i tshirt-factory-postgres psql -U factory_user tshirt_factory < backup.sql
```

---

## 🧪 Testing

### Run All Test Cases

```bash
# Via monitoring dashboard
# Open http://localhost:5001
# Navigate to "Test Cases" tab
# Click "Run Test Case" → Select "All"
```

### Manual Testing

```bash
# Test cutting machine
mosquitto_pub -h localhost -p 1883 \
  -t "factory/tshirt-factory/machines/cutting-01/command" \
  -m '{"command": "cut_fabric", "size": "L"}'

# Test full workflow
curl -X POST http://localhost:5000/production/start \
  -H "Content-Type: application/json" \
  -d '{
    "product_type": "tshirt",
    "size": "M",
    "color": "red"
  }'
```

---

## 📦 Production Deployment

### Environment Variables

```bash
# Production configuration
export ENVIRONMENT=production
export MQTT_BROKER=mqtt.yourcompany.com
export MQTT_PORT=8883
export MQTT_USE_TLS=true
export DATABASE_HOST=db.yourcompany.com
export DATABASE_PASSWORD=<secure-password>
export REDIS_HOST=redis.yourcompany.com
```

### Docker Compose Production

```yaml
version: '3.8'
services:
  orchestrator:
    image: your-registry/tshirt-orchestrator:latest
    environment:
      - ENVIRONMENT=production
      - MQTT_BROKER=${MQTT_BROKER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
```

---

## 🆚 Comparison with Generic Factory Platform

| Feature | T-Shirt Factory | Generic Factory Platform |
|---------|----------------|--------------------------|
| **Purpose** | Complete e-commerce example | Universal factory generator |
| **Workflow** | Fixed (4 machines) | Configurable (unlimited) |
| **Frontend** | Customer orders | Monitoring only |
| **Use Case** | Learning, demos | IoT testing, simulation |
| **Complexity** | Simple | Advanced |
| **Configuration** | Docker Compose | JSON templates |
| **Output** | Running services | Generated code |

**When to use T-Shirt Factory:**
- Learning IoT + microservices
- Demonstrating e-commerce integration
- Teaching factory automation concepts

**When to use Generic Platform:**
- Testing IoT platforms with various factory types
- Simulating automotive, pharma, electronics manufacturing
- Generating custom factory configurations

See [README.md](README.md) for Generic Factory Platform documentation.

---

## 📚 Additional Resources

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Microservices**: See [MICROSERVICES_README.md](MICROSERVICES_README.md)
- **Generic Platform**: See [GENERIC_FACTORY_SYSTEM.md](GENERIC_FACTORY_SYSTEM.md)
- **Project Status**: See [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 🤝 Contributing

Contributions welcome! This is the reference implementation, so please:
- Keep it simple and understandable
- Maintain the fixed 4-machine workflow
- Focus on clarity over features
- Update documentation with changes

---

## 📄 License

MIT License - See LICENSE file

---

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: This file and linked docs
- **Examples**: See `tshirt-customizer/` for frontend code

---

**Version 1.0** - T-Shirt Factory Reference Implementation
