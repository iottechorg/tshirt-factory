# Production Orchestrator - Workflow-Based Coordination

## Overview

The Production Orchestrator is a sophisticated workflow-based system that coordinates multiple machines in the factory to produce products according to defined workflows. It provides real machine coordination, performance tracking, error handling, and dynamic workflow adjustment.

## Key Features

### ✅ Real Machine Coordination
- **Machine State Tracking**: Tracks each machine's status (idle, busy, error)
- **Response Handling**: Waits for actual machine responses via MQTT
- **Timeout Management**: Configurable timeouts for each workflow step
- **Queue Management**: Intelligently assigns work to available machines

### ✅ Workflow Management
- **JSON-Based Workflows**: Define workflows in JSON files
- **Dynamic Loading**: Workflows loaded from `/workflows` directory
- **Runtime Adjustment**: Modify workflow parameters without restart
- **Multiple Product Types**: Support for different product workflows

### ✅ Error Handling & Recovery
- **Automatic Retries**: Configurable retry counts per step
- **Failure Tracking**: Monitors and records failures
- **State Recovery**: Maintains order state through failures
- **Performance Metrics**: Tracks success rates and timing

### ✅ Performance Monitoring
- **Machine Performance**: Tracks operations, failures, and average times
- **Workflow Analytics**: Monitors step completion times
- **Error Rate Tracking**: Per-machine failure rates
- **MQTT-Based Queries**: Query performance via MQTT

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Orchestrator                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Workflow   │      │   Machine    │                     │
│  │   Registry   │      │   Registry   │                     │
│  └──────────────┘      └──────────────┘                     │
│                                                               │
│  ┌──────────────────────────────────────────────┐           │
│  │         Production Order Queue               │           │
│  └──────────────────────────────────────────────┘           │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Performance  │  │ Machine State│  │   Response   │      │
│  │  Tracking    │  │   Monitor    │  │   Handler    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└───────────────────────┬─────────────────────────────────────┘
                        │ MQTT
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐            ┌────────▼────────┐
│    Machines    │            │   Workflow      │
│  (cutting,     │            │   Manager CLI   │
│   sewing, etc) │            └─────────────────┘
└────────────────┘
```

## Workflow Structure

Workflows are defined in JSON format with the following structure:

```json
{
  "workflow_id": "workflow-tshirt-standard",
  "workflow_name": "Standard T-Shirt Production",
  "description": "Complete t-shirt production workflow",
  "product_type": "tshirt",
  "steps": [
    {
      "step_id": "step-1",
      "machine_type": "cutting",
      "operation": "cut_fabric",
      "required_inputs": ["material", "cut_size"],
      "optional_inputs": [],
      "outputs": ["cut_fabric"],
      "timeout_seconds": 60,
      "retry_count": 0
    }
    // ... more steps
  ],
  "metadata": {
    "estimated_time_minutes": 20,
    "complexity": "standard"
  }
}
```

### Workflow Parameters

- **workflow_id**: Unique identifier for the workflow
- **workflow_name**: Human-readable name
- **product_type**: Product type this workflow produces
- **steps**: Array of workflow steps
  - **step_id**: Unique step identifier
  - **machine_type**: Type of machine needed
  - **operation**: Operation to perform
  - **required_inputs**: Required data inputs
  - **optional_inputs**: Optional data inputs
  - **outputs**: Data produced by this step
  - **timeout_seconds**: Max time to wait for completion
  - **retry_count**: Number of retries on failure

## MQTT Topics

### Subscribed Topics (Orchestrator Listens)

```
# Production requests
factory/{site_id}/production/request

# Machine registration
factory/{site_id}/machine/+/+/register

# Machine responses
factory/{site_id}/production/+/step/+/response

# Workflow adjustments
factory/{site_id}/orchestrator/workflow/adjust

# Performance queries
factory/{site_id}/orchestrator/performance/query
```

### Published Topics (Orchestrator Sends)

```
# Machine commands
factory/{site_id}/machine/{type}/{id}/command

# Production status
factory/{site_id}/production/{order_id}/status

# Step status
factory/{site_id}/production/{order_id}/step/{step_id}/status

# Final results
factory/{site_id}/production/{order_id}/result
```

## Usage Examples

### 1. Submit a Production Order

```bash
# Using the workflow manager CLI
python3 services/production-orchestrator/workflow_manager.py order \
  --name "Custom T-Shirt" \
  --workflow "workflow-tshirt-standard" \
  --details '{"material": "Cotton", "cut_size": "Large"}'
```

Or via MQTT:

```bash
mosquitto_pub -h localhost -p 31883 -t "factory/site-01/production/request" -m '{
  "product_name": "Custom T-Shirt",
  "workflow_id": "workflow-tshirt-standard",
  "product_details": {
    "material": "Cotton",
    "cut_size": "Large",
    "stitch_type": "Straight",
    "thread_color": "Black"
  }
}'
```

### 2. Adjust Workflow Parameters

Increase timeout for slow machine:

```bash
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-tshirt-standard" \
  --step "step-3" \
  --param "timeout_seconds" \
  --value 120
```

Increase retry count for unreliable step:

```bash
python3 services/production-orchestrator/workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-5" \
  --param "retry_count" \
  --value 2
```

### 3. List Available Workflows

```bash
python3 services/production-orchestrator/workflow_manager.py list
```

### 4. Query Performance Metrics

```bash
python3 services/production-orchestrator/workflow_manager.py performance
```

Or via MQTT:

```bash
mosquitto_pub -h localhost -p 31883 -t "factory/site-01/orchestrator/performance/query" -m '{
  "action": "query",
  "response_topic": "factory/site-01/orchestrator/performance/response"
}'
```

## Workflow Coordination Flow

1. **Order Submission**: Order submitted with workflow ID or product type
2. **Workflow Selection**: Orchestrator selects appropriate workflow
3. **Order Queuing**: Order added to production queue
4. **Step Execution**: For each step in workflow:
   - Validate inputs are available
   - Find available machine of required type
   - Send command to machine via MQTT
   - Wait for machine response (with timeout)
   - Track performance metrics
   - Retry on failure (if configured)
   - Update workflow state with outputs
5. **Completion**: Publish final result

## Machine Response Format

Machines must respond on the specified `response_topic` with:

```json
{
  "status": "success",  // or "failed"
  "order_id": "uuid",
  "step_id": "step-1",
  "outputs": ["cut_fabric"],
  "elapsed_time": 5.2,
  "error": null  // or error message if failed
}
```

## Performance Tracking

The orchestrator tracks:

- **Total Operations**: Count of operations per machine
- **Failures**: Number of failed operations
- **Failure Rate**: Percentage of operations that failed
- **Average Time**: Mean completion time per machine

This data can be used to:
- Identify slow machines
- Detect machines with high error rates
- Optimize workflow timeouts
- Balance load across machines

## Dynamic Workflow Adjustment

Workflows can be adjusted at runtime based on:

1. **Machine Performance**: Increase timeouts for slow machines
2. **Error Rates**: Increase retries for unreliable operations
3. **Production Requirements**: Add/remove steps dynamically
4. **Resource Availability**: Route to different machine types

### Example: Adapting to Slow Machine

If quality check machine is taking longer:

```bash
# Increase timeout from 45s to 90s
python3 workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-5" \
  --param "timeout_seconds" \
  --value 90
```

### Example: Handling Unreliable Operation

If printing step fails frequently:

```bash
# Add retry capability
python3 workflow_manager.py adjust \
  --workflow "workflow-complete-production" \
  --step "step-4" \
  --param "retry_count" \
  --value 2
```

## Available Workflows

Check the `/workflows` directory for available workflows:

- **tshirt-standard.json**: Standard 4-step t-shirt production
- **complete-production-chain.json**: Full 7-step production with all machines
- **premium-tshirt.json**: Premium quality t-shirt
- **jacket-parallel.json**: Jacket with parallel processing
- **custom-embroidery.json**: Custom embroidery workflow
- **ecommerce-ready.json**: E-commerce packaging workflow
- **multi-color-print.json**: Multi-color printing workflow
- **quick-patch.json**: Quick 2-step patch production

## Monitoring Production

### View Order Status

Subscribe to production status:

```bash
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/production/+/status"
```

### View Machine Activity

Subscribe to machine telemetry:

```bash
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/machine/#"
```

### View Step Results

Subscribe to step completion:

```bash
mosquitto_sub -h localhost -p 31883 -t "factory/site-01/production/+/step/+/status"
```

## Error Handling

### Timeout Scenarios

If a machine doesn't respond within `timeout_seconds`:
1. Orchestrator logs timeout error
2. If `retry_count > 0`, retry the step
3. Otherwise, mark order as failed
4. Machine marked as "error" state

### Machine Failures

If a machine reports failure:
1. Error logged with details
2. If retries available, retry after 2s delay
3. Otherwise, propagate failure to order
4. Performance metrics updated

### Recovery

- Machines automatically recover when they respond successfully
- Failed orders can be resubmitted
- Workflow adjustments take effect immediately

## Best Practices

### Workflow Design

1. **Set Realistic Timeouts**: Based on machine performance data
2. **Add Retries Strategically**: For operations prone to transient failures
3. **Define Clear Dependencies**: Use `required_inputs` and `outputs`
4. **Test Workflows**: Start simple, add complexity gradually

### Performance Optimization

1. **Monitor Metrics**: Regularly check machine performance
2. **Adjust Timeouts**: Increase for consistently slow machines
3. **Balance Load**: Distribute work across multiple machines
4. **Identify Bottlenecks**: Track which steps take longest

### Production Management

1. **Use Product Types**: Group similar workflows by product type
2. **Version Workflows**: Create variants for different requirements
3. **Track Results**: Monitor success rates and adjust accordingly
4. **Plan Capacity**: Based on workflow durations and machine availability

## Troubleshooting

### Orders Not Processing

1. Check orchestrator logs
2. Verify machines are registered
3. Check MQTT broker connectivity
4. Verify workflow exists

### Machine Not Responding

1. Check machine service logs
2. Verify MQTT topics match
3. Check machine command handler
4. Increase timeout if needed

### High Failure Rate

1. Query performance metrics
2. Identify failing machine
3. Check machine logs for errors
4. Consider adding retries
5. Adjust workflow if needed

## Future Enhancements

- [ ] Parallel step execution for `parallel_group`
- [ ] Workflow versioning and rollback
- [ ] Machine capability matching
- [ ] Priority-based scheduling
- [ ] Resource reservation
- [ ] Performance-based routing
- [ ] Predictive maintenance integration
- [ ] Web UI for workflow management
