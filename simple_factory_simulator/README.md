# Factory Monitoring Dashboard

## Universal Factory Simulator & Monitoring Interface

A Flask-based monitoring dashboard with a modern Tailwind CSS interface that works with **both** factory systems in this repository.

---

## 🎯 Purpose

This monitoring dashboard provides real-time factory monitoring and control capabilities for:

1. **T-Shirt Factory** - Monitor the original 4-machine t-shirt production system
2. **Generic Factory Platform** - Monitor ANY generated factory (automotive, pharma, electronics, etc.)

---

## ✨ Features

### Modern Tailwind CSS Interface
- Gradient backgrounds and card-based layouts
- Responsive design for all screen sizes
- Real-time data updates via MQTT
- Interactive controls and status indicators
- SVG icons throughout

### Three Main Sections

#### 1. Machine Monitoring
- Real-time machine status table
- Sensor value updates and configuration
- Machine failure rate adjustments
- Live sensor data display

#### 2. Production Management
- Manual production triggering
- Product configuration (name, details)
- Success rate adjustment
- Production status tracking
- Real-time production updates via MQTT

#### 3. Test Cases & Automation
- Predefined test case execution
- Random test case generation
- Automated production intervals
- Production results history
- Test automation for QA

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
cd simple_factory_simulator

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The dashboard auto-configures based on environment variables:

```bash
# For T-Shirt Factory (default)
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export MQTT_WS_PORT=9001
export WEBAPP_PORT=5001

# For Generated Factory
export MQTT_BROKER=localhost
export MQTT_PORT=31883
export MQTT_WS_PORT=39001
export WEBAPP_PORT=5001
```

### Run the Dashboard

```bash
python app.py
```

Open browser: **http://localhost:5001**

---

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Default | T-Shirt Factory | Generic Factory |
|----------|-------------|---------|----------------|-----------------|
| `MQTT_BROKER` | MQTT broker address | `broker.emqx.io` | `localhost` | `localhost` |
| `MQTT_PORT` | MQTT broker port | `1883` | `1883` | `31883` |
| `MQTT_WS_PORT` | MQTT WebSocket port | `8083` | `9001` | `39001` |
| `WEBAPP_PORT` | Flask server port | `5001` | `5001` | `5001` |
| `PRODUCTION_SUCCESS_RATE` | Default success rate | `0.99` | `0.99` | `0.99` |
| `PRODUCTION_LOOP_INTERVAL` | Production check interval (s) | `10` | `10` | `10` |
| `MACHINE_DATA_PUBLISH_INTERVAL` | Sensor publish interval (s) | `5` | `5` | `5` |
| `MACHINE_DATA_REST_REQUEST_INTERVAL` | REST API poll interval (s) | `10` | `10` | `10` |

### Edit Configuration File

Alternatively, edit `config.py`:

```python
# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_WS_PORT = int(os.getenv("MQTT_WS_PORT", 9001))

# Flask Configuration
WEBAPP_PORT = os.getenv("WEBAPP_PORT", 5001)
API_BASE_URL = "http://localhost:" + str(WEBAPP_PORT)

# Production Configuration
PRODUCTION_SUCCESS_RATE = float(os.getenv("PRODUCTION_SUCCESS_RATE", 0.99))
MACHINE_NAMES = ["cutting", "sewing", "ironing", "printing"]
```

---

## 📊 Using with T-Shirt Factory

### 1. Start T-Shirt Factory Services

```bash
cd services
docker-compose up --build
```

### 2. Start Monitoring Dashboard

```bash
cd simple_factory_simulator
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export MQTT_WS_PORT=9001
python app.py
```

### 3. Open Dashboard

Navigate to **http://localhost:5001**

---

## 🏭 Using with Generated Factories

### 1. Generate a Factory

```bash
python tools/factory_generator.py factory-configs/automotive-assembly-plant.json
```

### 2. Start Generated Factory

```bash
cd generated-factories/automotive-plant-001
docker compose up --build
```

### 3. Configure Dashboard for Generated Factory

Check the generated factory's `docker-compose.yml` for ports:

```yaml
# Usually:
mqttbroker:
  ports:
    - "31883:1883"   # MQTT port
    - "39001:9001"   # WebSocket port
```

### 4. Start Dashboard with Correct Ports

```bash
cd simple_factory_simulator
export MQTT_BROKER=localhost
export MQTT_PORT=31883
export MQTT_WS_PORT=39001
python app.py
```

### 5. Open Dashboard

Navigate to **http://localhost:5001**

---

## 🎨 Dashboard Features

### Machine Monitoring Tab

**Features:**
- Machine status table (ID, Name, Sensors)
- Machine selector dropdown
- Sensor value updater
- Failure rate configuration
- Collapsible machine settings

**Actions:**
- Select a machine
- Update sensor values in real-time
- Adjust machine failure rates
- View sensor status

### Production Monitoring Tab

**Features:**
- Product name input with random generator
- Product details (JSON) with random generator
- Production success rate configuration
- Production status display
- Real-time production updates via MQTT

**Actions:**
- Enter product details
- Generate random product data
- Start production manually
- Adjust production success rate
- Monitor production progress

### Test Cases & Automation Tab

**Features:**
- Predefined test case selector
- Random test case generator
- Automated production with configurable intervals
- Production results display
- Start/Stop automated production
- Clear results history

**Predefined Test Cases:**
- `normal_production` - Standard production flow
- `high_temp_cutting` - Test high temperature scenario
- `low_thread_tension_sewing` - Test low tension scenario
- `high_failure_rate` - Test failure handling
- `sensor_check` - Verify all sensors
- `random_test` - Generate random test scenario

---

## 🔌 API Endpoints

The dashboard exposes a RESTful API:

### Machine Endpoints

```bash
# Get all machines
GET /machines

# Update machine configuration
PUT /machines/{machine_id}
Content-Type: application/json
{
  "failure_rate": 0.1
}

# Update specific sensor
PUT /machines/sensor/{machine_id}/{sensor_name}
Content-Type: application/json
{
  "value": 35.5
}
```

### Production Endpoints

```bash
# Start production
POST /production
Content-Type: application/json
{
  "product_name": "T-Shirt",
  "product_details": {"size": "L", "color": "blue"}
}

# Update production configuration
PUT /production/config
Content-Type: application/json
{
  "success_rate": 0.95
}
```

### Test Endpoints

```bash
# Run test case
POST /test/{test_case}

# Available test cases:
# - normal_production
# - high_temp_cutting
# - low_thread_tension_sewing
# - high_failure_rate
# - sensor_check
# - random_test
```

---

## 🗂️ File Structure & Components

```
simple_factory_simulator/
├── templates/
│   └── index.html              # Main dashboard UI (Tailwind CSS)
├── static/
│   ├── style.css               # Custom styles and animations
│   ├── script.js               # Dashboard JavaScript
│   └── test_cases.json         # Test case definitions
├── app.py                      # Flask application (API endpoints)
├── config.py                   # Configuration management
├── managers.py                 # Machine & production managers
├── machine.py                  # Machine model
├── production.py               # Production process logic
├── mqtt_publisher.py           # MQTT publisher
├── client.py                   # MQTT client
├── util.py                     # Utility functions
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Component Details

#### 1. `config.py`
- **Purpose:** Stores project configuration settings
- **Key Settings:** MQTT broker details, topics, default success rate, machine names

#### 2. `machine.py`
- **Purpose:** Defines the `Machine` class representing a factory machine
- **Key Attributes:** Machine ID, name, state, sensor data, failure rate
- **Key Methods:** Simulates operation, updates sensors, returns JSON data

#### 3. `mqtt_publisher.py`
- **Purpose:** Handles MQTT communication with broker
- **Key Methods:** Connects, publishes messages, manages MQTT client

#### 4. `production.py`
- **Purpose:** Manages production workflow and steps
- **Key Attributes:** Production steps, status, failure rate, production queue
- **Key Methods:** Enqueues requests, executes steps, publishes results

#### 5. `util.py`
- **Purpose:** Helper functions
- **Key Functions:** Fetch machines by ID, generate random data, API responses

#### 6. `managers.py`
- **Purpose:** Main application managers
- **Key Classes:**
  - `MachineManager`: Manages machines and data publishing
  - `ProductionManager`: Manages production processes

#### 7. `app.py`
- **Purpose:** Flask application with REST API
- **Key Routes:** Endpoints for machines, production, tests

#### 8. `templates/index.html`
- **Purpose:** Modern Tailwind CSS dashboard interface
- **Features:** Tabs, cards, gradients, responsive design

---

## 🧪 Testing

### Manual Testing

```bash
# Test API connection
curl http://localhost:5001/machines

# Trigger production
curl -X POST http://localhost:5001/production \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Test Product", "product_details": {"test": true}}'

# Run test case
curl -X POST http://localhost:5001/test/normal_production
```

### MQTT Testing

```bash
# Subscribe to all topics (T-shirt factory)
mosquitto_sub -h localhost -p 1883 -t "#" -v

# Subscribe to all topics (Generated factory)
mosquitto_sub -h localhost -p 31883 -t "#" -v
```

---

## 🎯 Use Cases

### For T-Shirt Factory
- Monitor 4-machine workflow
- Test production scenarios
- Adjust sensor values for demonstrations
- Simulate machine failures
- Educational purposes

### For Generic Factories
- Monitor generated factory operations
- Test automotive/pharma/electronics workflows
- Validate factory configurations
- Debug machine operations
- IoT platform testing

---

## 🔍 Troubleshooting

### Dashboard Won't Start

```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port availability
lsof -i :5001
```

### Can't Connect to MQTT

```bash
# Verify broker is running (T-shirt)
mosquitto_sub -h localhost -p 1883 -t "test" -v

# Verify broker is running (Generated)
mosquitto_sub -h localhost -p 31883 -t "test" -v

# Check WebSocket port
telnet localhost 9001   # T-shirt factory
telnet localhost 39001  # Generated factory
```

### No Machine Data

1. Verify factory services are running: `docker ps`
2. Check API endpoint: `curl http://localhost:5001/machines`
3. Check MQTT topics: `mosquitto_sub -h localhost -p 1883 -t "#"`
4. Review Flask logs in terminal

### Production Not Starting

1. Check production API
2. Verify MQTT connection
3. Check orchestrator logs (if using services)
4. Verify all machines are healthy

---

## 🆚 Dashboard vs Other Frontends

| Feature | simple_factory_simulator | tshirt-customizer |
|---------|-------------------------|-------------------|
| **Purpose** | Factory monitoring | Customer orders |
| **Target User** | Factory operator | End customer |
| **Functionality** | Monitor & control | Place orders |
| **Factory Support** | T-Shirt + Generic | T-Shirt only |
| **Technology** | Flask + Tailwind | Angular + Tailwind |
| **Use Case** | Operations/Testing | E-commerce |

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t factory-simulator .
```

### Run with Docker Compose

```bash
docker compose up --build -d
```

### Access the Web App

Open your browser: **http://localhost:5001**

---

## 📚 Additional Resources

- **[TSHIRT_FACTORY_README.md](../TSHIRT_FACTORY_README.md)** - T-shirt factory guide
- **[GENERIC_FACTORY_SYSTEM.md](../GENERIC_FACTORY_SYSTEM.md)** - Generic platform guide
- **[README.md](../README.md)** - Main repository guide

---

## ⚠️ Known Issues

- Replace development web server with production server
- Code restructuring needed if using gunicorn (MQTT/WebSocket connection issues)
- Consider flask_mqtt as alternative: https://flask-mqtt.readthedocs.io/en/latest/usage.html#configure-the-mqtt-client

---

## 🤝 Contributing

Contributions welcome! This dashboard should remain universal and work with any factory type.

---

## 📄 License

MIT License - See LICENSE file

---

**Version 1.0** - Universal Factory Monitoring Dashboard
