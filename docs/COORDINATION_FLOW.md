# Production Orchestrator - Machine Coordination Flow

## Complete Order Processing Flow

### Timeline View: T-Shirt Order (4 Steps)

```
Time  | Orchestrator              | Cutting Machine    | Sewing Machine     | Ironing Machine    | Printing Machine
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=0   | Receive Order             |                    |                    |                    |
      | Select Workflow           |                    |                    |                    |
      | Queue Order               |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=1   | STEP 1: Start             |                    |                    |                    |
      | Find: cutting-01 (IDLE)   |                    |                    |                    |
      | Mark: cutting-01 BUSY     |                    |                    |                    |
      | Send Command →            |                    |                    |                    |
      |                           | Receive Command    |                    |                    |
      |                           | Validate Data      |                    |                    |
      |                           | Start Processing   |                    |                    |
t=2   | Wait for response...      | Processing...      |                    |                    |
t=3   |                           | Processing...      |                    |                    |
t=4   |                           | Processing...      |                    |                    |
t=5   |                           | Processing...      |                    |                    |
t=6   |                           | Complete!          |                    |                    |
      |                           | Send Response →    |                    |                    |
      | ← Receive Response        |                    |                    |                    |
      | Status: SUCCESS           |                    |                    |                    |
      | Mark: cutting-01 IDLE     |                    |                    |                    |
      | Track: time=5.2s          |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=7   | STEP 2: Start             |                    |                    |                    |
      | Find: sewing-01 (IDLE)    |                    |                    |                    |
      | Mark: sewing-01 BUSY      |                    |                    |                    |
      | Send Command →            |                    |                    |                    |
      |                           |                    | Receive Command    |                    |
      |                           |                    | Start Processing   |                    |
t=8   | Wait for response...      |                    | Processing...      |                    |
t=9   |                           |                    | Processing...      |                    |
t=10  |                           |                    | Processing...      |                    |
t=11  |                           |                    | Processing...      |                    |
t=12  |                           |                    | Complete!          |                    |
      |                           |                    | Send Response →    |                    |
      | ← Receive Response        |                    |                    |                    |
      | Status: SUCCESS           |                    |                    |                    |
      | Mark: sewing-01 IDLE      |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=13  | STEP 3: Start             |                    |                    |                    |
      | Find: ironing-01 (IDLE)   |                    |                    |                    |
      | Mark: ironing-01 BUSY     |                    |                    |                    |
      | Send Command →            |                    |                    |                    |
      |                           |                    |                    | Receive Command    |
      |                           |                    |                    | Start Processing   |
t=14  | Wait for response...      |                    |                    | Processing...      |
t=15  |                           |                    |                    | Processing...      |
t=16  |                           |                    |                    | Processing...      |
t=17  |                           |                    |                    | Processing...      |
t=18  |                           |                    |                    | Complete!          |
      |                           |                    |                    | Send Response →    |
      | ← Receive Response        |                    |                    |                    |
      | Status: SUCCESS           |                    |                    |                    |
      | Mark: ironing-01 IDLE     |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=19  | STEP 4: Start             |                    |                    |                    |
      | Find: printing-01 (IDLE)  |                    |                    |                    |
      | Mark: printing-01 BUSY    |                    |                    |                    |
      | Send Command →            |                    |                    |                    |
      |                           |                    |                    |                    | Receive Command
      |                           |                    |                    |                    | Start Processing
t=20  | Wait for response...      |                    |                    |                    | Processing...
t=21  |                           |                    |                    |                    | Processing...
t=22  |                           |                    |                    |                    | Processing...
t=23  |                           |                    |                    |                    | Processing...
t=24  |                           |                    |                    |                    | Processing...
t=25  |                           |                    |                    |                    | Complete!
      |                           |                    |                    |                    | Send Response →
      | ← Receive Response        |                    |                    |                    |
      | Status: SUCCESS           |                    |                    |                    |
      | Mark: printing-01 IDLE    |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
t=26  | All Steps Complete!       |                    |                    |                    |
      | Publish Final Result      |                    |                    |                    |
      | Order Status: COMPLETED   |                    |                    |                    |
------|---------------------------|--------------------|--------------------|--------------------|-----------------
```

## Message Flow Diagram

### Step 1: Cutting

```
┌─────────────┐                                      ┌─────────────┐
│ Orchestrator│                                      │  Cutting-01 │
└──────┬──────┘                                      └──────┬──────┘
       │                                                    │
       │ 1. Check workflow: need "cutting" machine         │
       │    ↓                                               │
       │ 2. Find available: cutting-01 (idle)              │
       │    ↓                                               │
       │ 3. Mark cutting-01 as BUSY                        │
       │    ↓                                               │
       │ MQTT: factory/site-01/machine/cutting/cutting-01/command
       ├───────────────────────────────────────────────────>│
       │ {                                                  │
       │   "command": "process",                            │
       │   "process_data": {                                │
       │     "operation": "cut_fabric",                     │
       │     "material": "Cotton",                          │
       │     "cut_size": "Medium"                           │
       │   },                                               │
       │   "order_id": "uuid-123",                          │
       │   "step_id": "step-1",                             │
       │   "response_topic": "factory/.../response"         │
       │ }                                                  │
       │                                                    │
       │ 4. Wait for response (timeout: 60s)               │
       │    ↓                                               │
       │    ... waiting ...                                 │ Validate data
       │                                                    │ Set state: BUSY
       │                                                    │ Process operation
       │                                                    │ ... working ...
       │                                                    │ ... working ...
       │                                                    │ Complete!
       │                                                    │
       │ MQTT: factory/site-01/production/uuid-123/step/step-1/response
       │<───────────────────────────────────────────────────┤
       │ {                                                  │
       │   "status": "success",                             │
       │   "machine_id": "cutting-01",                      │
       │   "machine_type": "cutting",                       │
       │   "elapsed_time": 5.2,                             │
       │   "timestamp": 1234567890                          │
       │ }                                                  │
       │                                                    │
       │ 5. Receive response                                │
       │    ↓                                               │
       │ 6. Mark cutting-01 as IDLE                        │
       │    ↓                                               │
       │ 7. Track performance: 5.2s, success               │
       │    ↓                                               │
       │ 8. Update workflow state: cut_fabric = true       │
       │    ↓                                               │
       │ 9. Proceed to STEP 2                              │
       │                                                    │
```

## Error Handling & Retry Flow

### Scenario: Machine Failure with Retry

```
┌─────────────┐                                      ┌─────────────┐
│ Orchestrator│                                      │ Printing-01 │
└──────┬──────┘                                      └──────┬──────┘
       │                                                    │
       │ ATTEMPT 1                                         │
       │ Send Command ─────────────────────────────────────>│
       │ Wait...                                            │ Processing...
       │                                                    │ ERROR!
       │ Response: FAILED ←────────────────────────────────┤
       │                                                    │
       │ Check retry_count: 2 (retries available)          │
       │ Log: "Step failed, retrying (1/2)"                │
       │ Wait 2 seconds...                                 │
       │                                                    │
       │ ATTEMPT 2                                         │
       │ Send Command ─────────────────────────────────────>│
       │ Wait...                                            │ Processing...
       │                                                    │ ERROR!
       │ Response: FAILED ←────────────────────────────────┤
       │                                                    │
       │ Check retry_count: 1 (retry available)            │
       │ Log: "Step failed, retrying (2/2)"                │
       │ Wait 2 seconds...                                 │
       │                                                    │
       │ ATTEMPT 3                                         │
       │ Send Command ─────────────────────────────────────>│
       │ Wait...                                            │ Processing...
       │                                                    │ SUCCESS!
       │ Response: SUCCESS ←───────────────────────────────┤
       │                                                    │
       │ Log: "Step succeeded on attempt 3"                │
       │ Continue to next step                             │
       │                                                    │
```

### Scenario: Timeout

```
┌─────────────┐                                      ┌─────────────┐
│ Orchestrator│                                      │  Machine    │
└──────┬──────┘                                      └──────┬──────┘
       │                                                    │
       │ Send Command ─────────────────────────────────────>│
       │                                                    │ (Machine hung)
       │ Wait for response (timeout: 60s)                  │ (No response)
       │ ... 10s ...                                        │
       │ ... 20s ...                                        │
       │ ... 30s ...                                        │
       │ ... 40s ...                                        │
       │ ... 50s ...                                        │
       │ ... 60s ...                                        │
       │                                                    │
       │ TIMEOUT!                                           │
       │ Mark machine as ERROR                              │
       │ Log: "Timeout waiting for response"               │
       │                                                    │
       │ Check retry_count: 1 (retry available)            │
       │ Retry the operation                               │
       │                                                    │
```

## Workflow State Management

### How Workflow State Evolves

```
Initial State:
{
  "material": "Cotton",
  "cut_size": "Medium",
  "stitch_type": "Straight",
  "thread_color": "Blue",
  "iron_temperature_setpoint": 150,
  "steam_level": "Medium",
  "ink_type": "Water-based"
}

After Step 1 (Cutting):
{
  "material": "Cotton",
  "cut_size": "Medium",
  ...
  "cut_fabric": true  ← NEW OUTPUT
}

After Step 2 (Sewing):
{
  "material": "Cotton",
  ...
  "cut_fabric": true,
  "sewn_garment": true  ← NEW OUTPUT
}

After Step 3 (Ironing):
{
  ...
  "cut_fabric": true,
  "sewn_garment": true,
  "ironed_garment": true  ← NEW OUTPUT
}

After Step 4 (Printing):
{
  ...
  "cut_fabric": true,
  "sewn_garment": true,
  "ironed_garment": true,
  "finished_product": true  ← NEW OUTPUT
}

All outputs produced → Order Complete!
```

## MQTT Topic Structure

### Command Flow
```
Orchestrator → Machine
Topic: factory/site-01/machine/{type}/{id}/command
Example: factory/site-01/machine/cutting/cutting-01/command
```

### Response Flow
```
Machine → Orchestrator
Topic: factory/site-01/production/{order_id}/step/{step_id}/response
Example: factory/site-01/production/uuid-123/step/step-1/response
```

### Status Updates
```
Orchestrator → Monitoring
Topic: factory/site-01/production/{order_id}/status
Topic: factory/site-01/production/{order_id}/step/{step_id}/status
Topic: factory/site-01/production/{order_id}/result
```

## Performance Tracking

### Data Collected Per Machine

```python
{
  "cutting-01": {
    "total_ops": 45,        # Total operations performed
    "failures": 2,          # Failed operations
    "total_time": 227.5,    # Total processing time (seconds)
    "avg_time": 5.06        # Average time per operation
  }
}
```

### Usage

```bash
# Query current performance
python3 workflow_manager.py performance

# Output:
Machine: cutting-01
  Operations: 45
  Failures: 2 (4.4%)
  Avg Time: 5.06s

Machine: sewing-01
  Operations: 42
  Failures: 1 (2.4%)
  Avg Time: 4.87s

# Use this to optimize workflows!
# If avg_time is high → increase timeout
# If failure rate is high → add retries
```

## Parallel Execution (Future Enhancement)

### Current: Sequential

```
Step 1 (cutting) → Step 2 (sewing) → Step 3 (ironing) → Step 4 (printing)
Total: ~20 seconds
```

### Future: Parallel Groups

```
                    ┌→ Step 1a (cut front)  ─┐
Parallel Group 1: ──┤                         ├→ Parallel Group 2
                    └→ Step 1b (cut back)   ─┘

                    ┌→ Step 2a (print front) ─┐
Parallel Group 2: ──┤                         ├→ Step 3 (sew together)
                    └→ Step 2b (print back)  ─┘

Total: ~15 seconds (30% faster!)
```

Already supported in workflow definition via `parallel_group`:
```json
{
  "step_id": "step-1a",
  "operation": "cut_front",
  "parallel_group": 1,  ← Same group = run in parallel
  ...
}
```

## Summary

The orchestrator provides **true sequential coordination**:

1. ✅ **Reads workflow** from JSON
2. ✅ **Starts first machine** via MQTT command
3. ✅ **Waits for response** (not simulated!)
4. ✅ **Machine completes work** and responds
5. ✅ **Orchestrator receives** response
6. ✅ **Starts next machine** in sequence
7. ✅ **Repeats** until all steps complete
8. ✅ **Handles failures** with retry logic
9. ✅ **Tracks performance** for optimization
10. ✅ **Allows adjustment** of timeouts and retries

This is a production-ready workflow orchestration system!
