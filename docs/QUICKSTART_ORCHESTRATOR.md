# Production Orchestrator Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- MQTT broker running (included in docker-compose)
- Python 3.8+ (for CLI tools)

## Starting the System

### 1. Start All Services

```bash
cd /Users/cemakpolat/Development/top-projects/tshirt-factory
docker-compose up -d
```

This starts:
- MQTT broker (mosquitto)
- PostgreSQL database
- TimescaleDB
- Redis
- All machine services (cutting, sewing, ironing, printing, quality-check, folding, packaging)
- Production orchestrator

### 2. Verify Services are Running

```bash
docker-compose ps
```

All services should show "Up" status.

### 3. Check Orchestrator Logs

```bash
docker-compose logs -f production-orchestrator
```

You should see:
```
Starting Production Orchestrator V2 (Workflow-based)
Loaded 8 workflow(s) from /app/workflows
Total workflows available: 12
  - Standard T-Shirt Production (tshirt) - 4 steps
  - Complete Production Chain with All Machines (premium-complete) - 7 steps
  ...
Orchestrator is running...
```

## Basic Usage Examples

### Example 1: Simple T-Shirt Order

Submit a basic t-shirt order using MQTT:

```bash
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/production/request" \
  -m '{
    "product_name": "Blue Cotton T-Shirt",
    "product_type": "tshirt",
    "product_details": {
      "material": "Cotton",
      "cut_size": "Medium",
      "stitch_type": "Straight",
      "thread_color": "Blue",
      "iron_temperature_setpoint": 150,
      "steam_level": "Medium",
      "ink_type": "Water-based",
      "design_name": "Logo1"
    }
  }'
```

### Example 2: Complete Production Chain

Order using the full 7-step workflow:

```bash
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/production/request" \
  -m '{
    "product_name": "Premium Complete T-Shirt",
    "workflow_id": "workflow-complete-production",
    "product_details": {
      "material": "Cotton",
      "cut_size": "Large"
    }
  }'
```

### Example 3: Monitor Order Progress

In a separate terminal, subscribe to production status:

```bash
mosquitto_sub -h localhost -p 31883 \
  -t "factory/site-01/production/#" \
  -v
```

You'll see:
```
factory/site-01/production/{order-id}/status {"event": "started", "status": "in_progress", ...}
factory/site-01/production/{order-id}/step/step-1/status {"status": "success", ...}
factory/site-01/production/{order-id}/step/step-2/status {"status": "success", ...}
...
factory/site-01/production/{order-id}/result {"status": "completed", ...}
```

## Using the Workflow Manager CLI

### List Available Workflows

```bash
python3 services/production-orchestrator/workflow_manager.py list
```

Output:
```
Available Workflows:
--------------------------------------------------------------------------------

  ID: workflow-complete-production
  Name: Complete Production Chain with All Machines
  Type: premium-complete
  Steps: 7
    1. precision_cut (cutting) - timeout: 60s, retries: 0
    2. premium_sew (sewing) - timeout: 90s, retries: 0
    3. press_garment (ironing) - timeout: 60s, retries: 0
    4. apply_design (printing) - timeout: 60s, retries: 1
    5. inspect_product (qualitycheck) - timeout: 45s, retries: 0
    6. fold_for_retail (folding) - timeout: 30s, retries: 0
    7. retail_package (packaging) - timeout: 45s, retries: 0
...
```

### Submit Order via CLI

```bash
python3 services/production-orchestrator/workflow_manager.py order \
  --name "My Custom Shirt" \
  --workflow "workflow-tshirt-standard" \
  --details '{"material": "Denim", "cut_size": "XL"}'
```

### Adjust Workflow Timeout

If quality check is taking too long:

```bash
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-5" \
  --param "timeout_seconds" \
  --value 90
```

### Add Retries for Unreliable Step

```bash
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-4" \
  --param "retry_count" \
  --value 3
```

### Query Performance Metrics

```bash
python3 services/production-orchestrator/workflow_manager.py performance
```

## Monitoring and Debugging

### View Machine Status

```bash
# All machine data
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/machine/#"

# Specific machine
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/machine/cutting/cutting-01/#"
```

### View Orchestrator Logs

```bash
docker-compose logs -f production-orchestrator
```

### View Machine Logs

```bash
# Cutting machine
docker-compose logs -f cutting-machine-01

# Sewing machine
docker-compose logs -f sewing-machine-01

# All machines
docker-compose logs -f cutting-machine-01 sewing-machine-01 ironing-machine-01
```

## Common Scenarios

### Scenario 1: Machine Taking Too Long

**Problem**: Quality check step timing out frequently

**Solution**:
```bash
# Check current timeout
python3 services/production-orchestrator/workflow_manager.py list | grep -A 10 qualitycheck

# Increase timeout
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-5" \
  --param "timeout_seconds" \
  --value 120

# Submit new order to test
python3 services/production-orchestrator/workflow_manager.py order \
  --name "Test Order" \
  --workflow "workflow-complete-production"
```

### Scenario 2: High Error Rate on Printing

**Problem**: Printing step failing frequently

**Solution**:
```bash
# Add retry attempts
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-tshirt-standard" \
  --step "step-4" \
  --param "retry_count" \
  --value 2

# Monitor next order
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/production/+/step/step-4/#" &
python3 services/production-orchestrator/workflow_manager.py order \
  --name "Retry Test" \
  --workflow "workflow-tshirt-standard"
```

### Scenario 3: Create Custom Workflow

**Problem**: Need a workflow for embroidered jackets

**Solution**:

1. Create new workflow file:

```bash
cat > workflows/custom-embroidered-jacket.json << 'EOF'
{
  "workflow_id": "workflow-embroidered-jacket",
  "workflow_name": "Custom Embroidered Jacket",
  "description": "Jacket with custom embroidery",
  "product_type": "jacket-embroidered",
  "steps": [
    {
      "step_id": "step-1",
      "machine_type": "cutting",
      "operation": "cut_jacket_pieces",
      "required_inputs": ["material", "cut_size"],
      "optional_inputs": [],
      "outputs": ["cut_pieces"],
      "timeout_seconds": 90,
      "retry_count": 0
    },
    {
      "step_id": "step-2",
      "machine_type": "sewing",
      "operation": "sew_jacket",
      "required_inputs": ["cut_pieces", "stitch_type", "thread_color"],
      "optional_inputs": [],
      "outputs": ["sewn_jacket"],
      "timeout_seconds": 120,
      "retry_count": 0
    },
    {
      "step_id": "step-3",
      "machine_type": "printing",
      "operation": "embroider_design",
      "required_inputs": ["sewn_jacket"],
      "optional_inputs": ["design_name"],
      "outputs": ["embroidered_jacket"],
      "timeout_seconds": 180,
      "retry_count": 1
    },
    {
      "step_id": "step-4",
      "machine_type": "qualitycheck",
      "operation": "inspect_jacket",
      "required_inputs": ["embroidered_jacket"],
      "optional_inputs": [],
      "outputs": ["inspected_jacket"],
      "timeout_seconds": 60,
      "retry_count": 0
    },
    {
      "step_id": "step-5",
      "machine_type": "packaging",
      "operation": "package_jacket",
      "required_inputs": ["inspected_jacket"],
      "optional_inputs": ["package_type"],
      "outputs": ["packaged_jacket"],
      "timeout_seconds": 60,
      "retry_count": 0
    }
  ],
  "metadata": {
    "estimated_time_minutes": 45,
    "complexity": "complex"
  }
}
EOF
```

2. Restart orchestrator to load new workflow:

```bash
docker-compose restart production-orchestrator
```

3. Submit order with new workflow:

```bash
python3 services/production-orchestrator/workflow_manager.py order \
  --name "Custom Jacket #1" \
  --workflow "workflow-embroidered-jacket" \
  --details '{"material": "Leather", "cut_size": "Large", "design_name": "Eagle"}'
```

## Testing the System

### Test 1: Single Order End-to-End

```bash
# Terminal 1: Monitor all production activity
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/production/#"

# Terminal 2: Submit order
mosquitto_pub -h localhost -p 31883 \
  -t "factory/site-01/production/request" \
  -m '{"product_name": "Test Shirt", "product_type": "tshirt"}'
```

Expected result: See order progress through all steps and completion

### Test 2: Multiple Concurrent Orders

```bash
# Submit 5 orders in quick succession
for i in {1..5}; do
  python3 services/production-orchestrator/workflow_manager.py order \
    --name "Batch Order $i" \
    --workflow "workflow-tshirt-standard"
  sleep 1
done
```

Expected result: Orders processed sequentially, machines coordinated properly

### Test 3: Workflow Adjustment During Production

```bash
# Terminal 1: Start monitoring
docker-compose logs -f production-orchestrator

# Terminal 2: Submit order
python3 services/production-orchestrator/workflow_manager.py order \
  --name "Adjustment Test" \
  --workflow "workflow-complete-production"

# Terminal 3: While running, adjust timeout
sleep 5
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-6" \
  --param "timeout_seconds" \
  --value 45

# Submit another order to see adjustment take effect
python3 services/production-orchestrator/workflow_manager.py order \
  --name "After Adjustment" \
  --workflow "workflow-complete-production"
```

Expected result: Second order uses new timeout value

## Troubleshooting

### Issue: Orders not processing

**Check orchestrator logs:**
```bash
docker-compose logs production-orchestrator | tail -50
```

**Verify machines are registered:**
```bash
# Should see "Registered machine: cutting/cutting-01" etc.
docker-compose logs production-orchestrator | grep "Registered machine"
```

**Check MQTT broker:**
```bash
docker-compose logs mqttbroker | tail -20
```

### Issue: Machine timeouts

**Check machine is running:**
```bash
docker-compose ps | grep machine
```

**Check machine logs:**
```bash
docker-compose logs <machine-name>
```

**Increase timeout:**
```bash
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "<workflow-id>" \
  --step "<step-id>" \
  --param "timeout_seconds" \
  --value 120
```

### Issue: High failure rate

**Query performance:**
```bash
python3 services/production-orchestrator/workflow_manager.py performance
```

**Check orchestrator logs for failures:**
```bash
docker-compose logs production-orchestrator | grep -i "failed"
```

**Add retries:**
```bash
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "<workflow-id>" \
  --step "<step-id>" \
  --param "retry_count" \
  --value 2
```

## Next Steps

1. **Explore Workflows**: Review all workflows in `/workflows` directory
2. **Create Custom Workflows**: Design workflows for your specific products
3. **Monitor Performance**: Regularly check machine performance metrics
4. **Optimize**: Adjust timeouts and retries based on actual performance
5. **Scale**: Add more machine instances to handle higher load

## Additional Resources

- Full documentation: `ORCHESTRATOR_README.md`
- Workflow examples: `/workflows/*.json`
- Machine service code: `/services/machines/*/`
- Orchestrator code: `/services/production-orchestrator/orchestrator.py`
