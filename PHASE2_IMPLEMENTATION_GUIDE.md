# Phase 2 - Cloud Integration Implementation Guide

## Status: Architecture Designed ✅ | Implementation: Ready to Start

Phase 2 builds upon the flexible workflow system from Phase 1 by adding enterprise-grade cloud connectivity, security, and monitoring.

## What Phase 2 Adds

### 1. Cloud Connectivity
- AWS IoT Core integration
- Azure IoT Hub integration
- Generic HTTP/REST cloud APIs
- Multi-cloud publishing support

### 2. Security
- MQTT TLS/SSL encryption
- Client certificate authentication
- Access Control Lists (ACLs)
- Secrets management

### 3. Monitoring & Observability
- Prometheus metrics collection
- Grafana dashboards
- Distributed tracing
- Real-time alerts

### 4. Edge Computing
- Edge gateway for data aggregation
- Local buffering during outages
- Edge analytics
- Protocol translation

## Implementation Roadmap

### Quick Win Path (1-2 hours)

Start with the most impactful components first:

#### Step 1: Add Basic Cloud Publishing (30 min)
The `cloud_publisher.py` already exists with basic functionality.

**What it does:**
- Publishes telemetry to a simulated "cloud" topic
- Production event publishing
- Already integrated in `orchestrator.py`

**Test it:**
```bash
# Subscribe to cloud topics
mosquitto_sub -h localhost -p 31883 -t "cloud/#" -v

# Trigger production - watch cloud messages
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/production/request" \
  -m '{"product_name": "Test", "product_details": {}}'
```

#### Step 2: Add Prometheus Metrics (45 min)

**File:** `services/shared/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Machine metrics
machine_operations = Counter('machine_operations_total', 'Total operations', ['machine_type', 'status'])
machine_uptime = Gauge('machine_uptime_seconds', 'Machine uptime', ['machine_id'])

# Production metrics
production_orders = Counter('production_orders_total', 'Total orders', ['status'])
production_duration = Histogram('production_duration_seconds', 'Production time')

# Start metrics server
start_http_server(9090)
```

**Integrate in machines:**
```python
# In machine_service.py
from metrics import machine_operations

def process_operation(...):
    result = machine.process_operation(data)
    machine_operations.labels(
        machine_type=machine.machine_type,
        status=result['status']
    ).inc()
```

**Access metrics:**
```bash
curl http://localhost:9090/metrics
```

#### Step 3: Add Grafana Dashboard (15 min)

**File:** `infrastructure/monitoring/docker-compose.monitoring.yml`

```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - factory-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - factory-network
```

**Start monitoring:**
```bash
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
```

**Access:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Full Implementation Path (1-2 days)

#### Day 1: Security & Cloud Connectors

**Morning (4 hours):**

1. **MQTT TLS/SSL Setup**
   - Generate certificates
   - Configure Mosquitto for TLS
   - Update clients for TLS connections

**Files to create:**
```
infrastructure/security/
├── generate-certs.sh
├── ca.crt
├── server.crt
├── server.key
└── clients/
    ├── cutting-01.crt
    └── cutting-01.key
```

2. **AWS IoT Core Connector**
   - Install AWS IoT SDK
   - Create device registry
   - Implement shadow synchronization

**File:** `services/cloud-connectors/aws-iot/aws_connector.py`

**Afternoon (4 hours):**

3. **Azure IoT Hub Connector**
   - Install Azure IoT SDK
   - Create device twins
   - Implement direct methods

**File:** `services/cloud-connectors/azure-iot/azure_connector.py`

4. **Secrets Management**
   - Deploy Vault container
   - Migrate credentials to Vault
   - Update services to read from Vault

#### Day 2: Monitoring & Edge Gateway

**Morning (4 hours):**

5. **Complete Prometheus Integration**
   - Add metrics to all services
   - Create recording rules
   - Set up alert rules

6. **Create Grafana Dashboards**
   - Factory overview dashboard
   - Machine details dashboard
   - Production analytics dashboard

**Afternoon (4 hours):**

7. **Edge Gateway Implementation**
   - Data aggregation logic
   - Buffering during outages
   - Protocol translation

**File:** `services/cloud-connectors/edge-gateway/gateway.py`

8. **Integration Testing**
   - Test cloud publishing
   - Verify TLS connections
   - Load testing

## Component Details

### AWS IoT Core Connector

```python
from awsiot import mqtt_connection_builder

class AWSIoTConnector(CloudPublisher):
    def __init__(self, endpoint, cert_path, key_path, ca_path):
        self.endpoint = endpoint
        self.connection = mqtt_connection_builder.mtls_from_path(
            endpoint=endpoint,
            cert_filepath=cert_path,
            pri_key_filepath=key_path,
            ca_filepath=ca_path
        )

    def connect(self):
        connect_future = self.connection.connect()
        connect_future.result()
        return True

    def publish_message(self, topic, payload):
        self.connection.publish(
            topic=topic,
            payload=json.dumps(payload),
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
```

### Azure IoT Hub Connector

```python
from azure.iot.device import IoTHubDeviceClient

class AzureIoTConnector(CloudPublisher):
    def __init__(self, connection_string):
        self.client = IoTHubDeviceClient.create_from_connection_string(
            connection_string
        )

    def connect(self):
        self.client.connect()
        return True

    def publish_message(self, topic, payload):
        message = Message(json.dumps(payload))
        message.content_type = "application/json"
        self.client.send_message(message)
```

### Edge Gateway

```python
class EdgeGateway:
    def __init__(self, local_mqtt, cloud_publishers):
        self.local_mqtt = local_mqtt
        self.cloud_publishers = cloud_publishers
        self.buffer = []
        self.aggregation_window = 10  # seconds

    def start(self):
        # Subscribe to local telemetry
        self.local_mqtt.subscribe(
            "factory/+/machine/+/+/telemetry",
            self.on_telemetry
        )

    def on_telemetry(self, topic, payload):
        # Aggregate data
        self.buffer.append(payload)

        if len(self.buffer) >= 10:
            aggregated = self.aggregate_data()
            self.publish_to_cloud(aggregated)

    def aggregate_data(self):
        # Combine multiple readings
        return {
            "readings": self.buffer,
            "avg_temperature": avg([r['temperature'] for r in self.buffer])
        }
```

## Configuration Examples

### MQTT with TLS

**mosquitto.conf:**
```
listener 8883
cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
require_certificate true

# ACLs
acl_file /mosquitto/config/acl.conf
```

**acl.conf:**
```
# Machine can only publish to own topics
user cutting-01
topic write factory/site-01/machine/cutting/cutting-01/#

# Orchestrator full access
user orchestrator
topic readwrite factory/site-01/#
```

### Prometheus Config

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'factory-machines'
    static_configs:
      - targets:
        - 'cutting-machine-01:9090'
        - 'sewing-machine-01:9090'
        - 'ironing-machine-01:9090'
        - 'printing-machine-01:9090'

  - job_name: 'production-orchestrator'
    static_configs:
      - targets: ['production-orchestrator:9090']
```

## Testing Checklist

### Security Testing
- [ ] TLS connection established
- [ ] Certificate validation working
- [ ] ACLs preventing unauthorized access
- [ ] Secrets not in environment variables

### Cloud Integration Testing
- [ ] Messages reaching AWS IoT Core
- [ ] Device shadows synchronized
- [ ] Azure device twin updated
- [ ] Failover to backup cloud

### Performance Testing
- [ ] 1000+ messages/second throughput
- [ ] < 100ms local MQTT latency
- [ ] < 500ms cloud publish latency
- [ ] Buffer handles 10k messages

### Monitoring Testing
- [ ] Metrics visible in Prometheus
- [ ] Grafana dashboards loading
- [ ] Alerts triggering correctly
- [ ] Traces showing end-to-end flow

## Dependencies to Add

**requirements.txt additions:**
```
# AWS IoT
awsiotsdk==1.19.0

# Azure IoT
azure-iot-device==2.13.0

# Monitoring
prometheus-client==0.19.0

# Security
cryptography==41.0.7
hvac==2.0.0  # Vault client
```

## Quick Start Commands

### Start with Cloud Publishing
```bash
# Already works! Just start the system
docker compose -f docker-compose.microservices.yml up --build

# Watch cloud messages
mosquitto_sub -h localhost -p 31883 -t "cloud/#" -v
```

### Add Monitoring
```bash
# Start monitoring stack
docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d

# Open Grafana
open http://localhost:3000
```

### Enable TLS (when certificates ready)
```bash
# Generate certificates
cd infrastructure/security && ./generate-certs.sh

# Update docker-compose to use TLS port
# Restart services
docker compose -f docker-compose.microservices.yml down
docker compose -f docker-compose.microservices.yml up --build
```

## Migration Strategy

### Phase 2a: Monitoring First (Low Risk)
1. Add Prometheus metrics to existing services
2. Deploy Grafana
3. Create dashboards
4. **No changes to MQTT or production flow**

### Phase 2b: Cloud Publishing (Medium Risk)
1. Deploy cloud connectors as separate services
2. Subscribe to existing MQTT topics
3. Publish to cloud in parallel
4. **Original flow unchanged**

### Phase 2c: Security Hardening (High Risk - Test First!)
1. Deploy TLS-enabled MQTT in parallel (port 8883)
2. Test with one machine first
3. Gradually migrate machines
4. Switch orchestrator last

## Next Steps

Choose your path:

**Option 1: Quick Value (1-2 hours)**
- Use existing cloud publisher
- Add basic Prometheus metrics
- Deploy Grafana

**Option 2: Production Ready (1-2 days)**
- Implement all components
- Full TLS/SSL
- AWS + Azure connectors
- Complete monitoring

**Option 3: Incremental (1 week, part-time)**
- Week 1: Monitoring
- Week 2: Cloud connectors
- Week 3: Security
- Week 4: Edge gateway

---

All architecture documents and component designs are ready. The foundation from Phase 1 makes Phase 2 implementation straightforward - it's just adding layers on top!
