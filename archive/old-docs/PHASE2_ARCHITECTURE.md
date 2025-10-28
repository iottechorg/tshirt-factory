# Phase 2 - Cloud Integration Architecture

## Overview

Phase 2 adds enterprise-grade cloud connectivity, security, and monitoring to the T-Shirt Factory, making it production-ready for real IoT cloud deployments.

## Architecture Diagram

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
│                    Cloud Connector Layer                              │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ AWS IoT          │  │ Azure IoT        │  │ HTTP/REST        │  │
│  │ Connector        │  │ Connector        │  │ Publisher        │  │
│  │ - Device Shadow  │  │ - Device Twin    │  │ - Webhooks       │  │
│  │ - MQTT Bridge    │  │ - Direct Methods │  │ - Custom APIs    │  │
│  └─────────┬────────┘  └─────────┬────────┘  └─────────┬────────┘  │
│            │                     │                      │            │
└────────────┼─────────────────────┼──────────────────────┼────────────┘
             │                     │                      │
             └─────────────────────┼──────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│                      Edge Gateway Layer                               │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Edge Gateway Service                                         │   │
│  │ - Local data aggregation                                     │   │
│  │ - Protocol translation (MQTT ↔ Cloud)                       │   │
│  │ - Buffering during outages                                   │   │
│  │ - Edge analytics and filtering                               │   │
│  │ - Certificate management                                      │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                           │                                          │
└───────────────────────────┼──────────────────────────────────────────┘
                            │
                            │ TLS/SSL (optional for local)
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│                      Local MQTT Broker                                │
│                   (with TLS/SSL, Auth)                               │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Mosquitto with:                                               │  │
│  │ - TLS/SSL certificates                                        │  │
│  │ - Username/password authentication                            │  │
│  │ - ACL (Access Control Lists)                                  │  │
│  │ - Certificate-based client authentication                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────┬────────────┬────────────┬────────────┬────────────┬──────────┘
       │            │            │            │            │
       ▼            ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Cutting  │ │ Sewing   │ │ Ironing  │ │ Printing │ │ Production   │
│ Machine  │ │ Machine  │ │ Machine  │ │ Machine  │ │ Orchestrator │
│          │ │          │ │          │ │          │ │              │
│ + Certs  │ │ + Certs  │ │ + Certs  │ │ + Certs  │ │ + Certs      │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability                        │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Prometheus  │  │   Grafana    │  │     Jaeger   │             │
│  │  (Metrics)   │  │ (Dashboards) │  │   (Tracing)  │             │
│  └──────┬───────┘  └──────────────┘  └──────────────┘             │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Metrics Collection Points:                                    │ │
│  │ - Machine telemetry rates                                     │ │
│  │ - Production throughput                                       │ │
│  │ - MQTT message rates                                          │ │
│  │ - Cloud connector health                                      │ │
│  │ - System resource usage                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Security Layer                                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Secrets Management (HashiCorp Vault)                          │ │
│  │ - MQTT credentials                                            │ │
│  │ - Cloud API keys                                              │ │
│  │ - Database passwords                                          │ │
│  │ - TLS certificates                                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Certificate Authority                                         │ │
│  │ - Generate client certificates                                │ │
│  │ - Sign certificates                                           │ │
│  │ - Certificate revocation                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

## Phase 2 Components

### 1. Cloud Connectors

#### AWS IoT Core Connector
**Features:**
- MQTT bridge to AWS IoT Core
- Device Shadow synchronization
- Thing registry integration
- Message routing rules
- Dead letter queue handling

**Topics:**
```
Publish to AWS:
  $aws/things/{machine_id}/shadow/update
  factory/telemetry/{machine_id}

Subscribe from AWS:
  $aws/things/{machine_id}/shadow/update/accepted
  $aws/things/{machine_id}/shadow/update/rejected
  factory/commands/{machine_id}
```

#### Azure IoT Hub Connector
**Features:**
- Azure IoT Hub MQTT/AMQP connection
- Device Twin synchronization
- Direct Methods support
- Telemetry upload
- Cloud-to-device messaging

**Integration:**
```
Device Twin Properties:
  - Machine status
  - Sensor calibration
  - Configuration

Direct Methods:
  - Emergency stop
  - Update firmware
  - Run diagnostics
```

#### Generic Cloud Publisher
**Features:**
- HTTP/REST API publishing
- Webhook support
- Custom cloud platform integration
- Batch message publishing
- Retry logic with exponential backoff

### 2. Security Implementation

#### MQTT TLS/SSL
```
mosquitto/
├── ca.crt              # Certificate Authority
├── server.crt          # Server certificate
├── server.key          # Server private key
└── clients/
    ├── cutting-01.crt  # Client certificates
    ├── cutting-01.key
    ├── sewing-01.crt
    └── ...
```

**mosquitto.conf:**
```
listener 8883
cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
require_certificate true
use_identity_as_username true

# ACLs
acl_file /mosquitto/config/acl.conf
```

**ACL Configuration:**
```
# Machines can only publish to their own topics
user cutting-01
topic write factory/site-01/machine/cutting/cutting-01/#

# Orchestrator can publish and subscribe
user orchestrator
topic readwrite factory/site-01/#

# Cloud connector read-only on telemetry
user cloud-connector
topic read factory/site-01/machine/+/+/telemetry
```

#### Authentication Methods
1. **Certificate-based** (recommended for production)
2. **Username/password** (for development)
3. **OAuth 2.0 tokens** (for cloud integration)

### 3. Edge Gateway

```python
class EdgeGateway:
    """Edge gateway for local processing and cloud bridging"""

    Features:
    - Data aggregation and filtering
    - Protocol translation
    - Offline buffering (store & forward)
    - Edge analytics
    - Certificate management
    - Health monitoring
```

**Capabilities:**
- Aggregate sensor data (reduce cloud traffic)
- Filter unnecessary messages
- Local caching during cloud outages
- Edge-based alerts
- Data compression
- Message batching

### 4. Monitoring Stack

#### Prometheus Metrics
```yaml
Metrics Collected:
  # Machine Metrics
  - machine_telemetry_count
  - machine_operation_duration_seconds
  - machine_failure_rate
  - machine_uptime_seconds

  # Production Metrics
  - production_orders_total
  - production_orders_completed
  - production_orders_failed
  - production_step_duration_seconds

  # MQTT Metrics
  - mqtt_messages_published_total
  - mqtt_messages_received_total
  - mqtt_connection_errors_total

  # Cloud Metrics
  - cloud_messages_sent_total
  - cloud_connection_status
  - cloud_api_latency_seconds
```

#### Grafana Dashboards
1. **Factory Overview**
   - Real-time production rate
   - Machine status grid
   - Active orders
   - Success/failure rates

2. **Machine Details**
   - Sensor trends over time
   - Operation history
   - Failure analysis
   - Maintenance predictions

3. **Production Analytics**
   - Workflow execution times
   - Bottleneck identification
   - Resource utilization
   - Quality metrics

4. **Cloud Integration**
   - Message throughput
   - Cloud latency
   - Connection health
   - Cost tracking

### 5. Secrets Management

```yaml
# Using HashiCorp Vault
secrets/
  factory/
    mqtt/
      username: factory_client
      password: <encrypted>
    aws/
      access_key_id: <encrypted>
      secret_access_key: <encrypted>
    azure/
      connection_string: <encrypted>
    database/
      postgres_password: <encrypted>
```

**Integration:**
```python
from hvac import Client

vault_client = Client(url='http://vault:8200')
vault_client.auth.token('root-token')

# Retrieve secrets
mqtt_creds = vault_client.secrets.kv.read_secret(
    path='factory/mqtt'
)
```

## Data Flow with Cloud Integration

### Telemetry Flow

```
Machine Sensor Data
       │
       ▼
Local MQTT (TLS)
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
Edge Gateway          Production DB
       │              (PostgreSQL)
       │
   Aggregation
   Filtering
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
       ▼          ▼          ▼          ▼
   AWS IoT   Azure IoT  Custom API  Prometheus
    Core        Hub                  (Metrics)
```

### Command Flow

```
Cloud Console/API
       │
       ▼
Cloud Platform (AWS/Azure)
       │
       ▼
Cloud Connector
       │
       ▼
Edge Gateway
       │
       ▼
Local MQTT (TLS)
       │
       ▼
Target Machine
```

## Security Considerations

### 1. Network Security
- All MQTT traffic encrypted with TLS 1.3
- Certificate pinning for cloud connections
- VPN/Private network for cloud connectivity
- Firewall rules limiting exposed ports

### 2. Authentication & Authorization
- Client certificates for machine authentication
- ACLs restricting topic access per client
- Cloud API keys rotated regularly
- Database credentials encrypted

### 3. Data Protection
- Encryption at rest for databases
- Encrypted backups
- PII/sensitive data masking
- Audit logging

### 4. Secrets Management
- No hardcoded credentials
- Vault for secret storage
- Automatic secret rotation
- Least privilege access

## Deployment Options

### Option 1: Full Cloud Deployment
```
Machines → Cloud MQTT → Cloud Processing → Cloud Storage
```
- All components in cloud (AWS EC2, Azure VMs)
- Managed services (AWS IoT, Azure IoT Hub)
- Highest availability

### Option 2: Hybrid Edge-Cloud
```
Machines → Edge Gateway → Cloud Connectors → Cloud
```
- Machines and edge on-premises
- Cloud connectors bridge to cloud
- Best for latency-sensitive operations

### Option 3: Multi-Cloud
```
Machines → Edge Gateway ─┬→ AWS IoT Core
                        ├→ Azure IoT Hub
                        └→ Custom Cloud API
```
- Publish to multiple clouds simultaneously
- Redundancy and vendor diversification
- Cross-cloud analytics

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| MQTT Latency | < 50ms | Local broker |
| Cloud Latency | < 200ms | Including TLS handshake |
| Throughput | > 1000 msg/s | Per broker |
| Uptime | 99.9% | With redundancy |
| Data Loss | < 0.01% | With buffering |

## Cost Optimization

1. **Edge Filtering**: Reduce cloud traffic by 70%
2. **Message Batching**: Reduce API calls
3. **Compression**: Reduce bandwidth costs
4. **Tiered Storage**: Hot/warm/cold data strategy
5. **Auto-scaling**: Scale based on load

## Testing Strategy

### Security Testing
- Penetration testing
- Certificate validation
- ACL enforcement tests
- Secret rotation tests

### Integration Testing
- Cloud connector failover
- Edge gateway buffering
- TLS connection tests
- Multi-cloud scenarios

### Performance Testing
- Load testing (10,000+ messages/s)
- Latency measurements
- Cloud API rate limiting
- Buffer overflow scenarios

## Migration from Phase 1

1. **Add TLS to existing MQTT** (minimal disruption)
2. **Deploy edge gateway** (transparent proxy)
3. **Enable cloud connectors** (optional)
4. **Add monitoring** (observability first)
5. **Implement secrets management** (security hardening)

---

This architecture provides enterprise-grade cloud connectivity while maintaining the flexibility and independence of the microservices design from Phase 1.
