# Smart T-Shirt Manufacturing Plant

Complete t-shirt manufacturing facility with cutting, sewing, quality control, and packaging

## Factory Configuration

- **Type**: textile_tshirt
- **ID**: tshirt-factory-001
- **Machines**: 4
- **Workflows**: 3

## Machines

- **cutting-01**: Fabric Cutting Machine #1
- **sewing-01**: Industrial Sewing Machine #1
- **qualitycheck-01**: AI Quality Inspector #1
- **packaging-01**: Automated Packaging System #1

## Workflows

- **standard-tshirt-production**: Standard T-Shirt Production (4 steps)
- **premium-tshirt-production**: Premium T-Shirt Production (4 steps)
- **custom-print-tshirt**: Custom Printed T-Shirt (4 steps)


## Quick Start

```bash
# Start factory
docker compose up --build

# Monitor MQTT
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Send production order
mosquitto_pub -h localhost -p 31883 \
  -t "factory/tshirt-factory-001/production/request" \
  -m '{"product_type": "tshirt", "quantity": 1}'
```

## Production Configuration

- **Mode**: on-demand
- **Target Rate**: 100 tshirts_per_day
- **Quality Control**: Enabled

## Generated Files

This factory was auto-generated from: `factory-configs/tshirt-factory.json`

Generated: 2025-10-27T00:00:00Z
Version: 1.0.0
