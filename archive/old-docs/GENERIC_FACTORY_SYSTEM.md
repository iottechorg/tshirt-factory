# Generic Factory Simulation Platform

## Overview

The T-Shirt Factory has evolved into a **Universal Factory Simulation Platform** that can simulate **any type of factory** through JSON configuration files. No code changes needed—define your factory, machines, and workflows entirely through JSON.

## Key Concept

Instead of hardcoded T-shirt production logic, you now have:

1. **Machine Templates** (JSON) - Define machine types with sensors, operations, and behaviors
2. **Factory Configurations** (JSON) - Define which machines, workflows, and production parameters
3. **Automatic Generation** - System generates Python code, Docker configs, and workflows

**Result**: Create automotive factories, food processing plants, electronics assembly, pharmaceutical production, or any manufacturing domain in minutes!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Factory Configuration                     │
│                         (JSON)                               │
│  - Factory type, name, description                           │
│  - Machine instances                                         │
│  - Workflows                                                 │
│  - Production parameters                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Machine Templates (JSON)                        │
│  - Sensors with update behaviors                             │
│  - Operations with durations                                 │
│  - Failure modes                                             │
│  - Telemetry configuration                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Factory Generator (Python)                      │
│  - Reads JSON configurations                                 │
│  - Generates machine Python classes                          │
│  - Creates docker-compose files                              │
│  - Generates workflows                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Running Factory Simulation                        │
│  - Machine services (containers)                             │
│  - MQTT communication                                        │
│  - Database persistence                                      │
│  - Production orchestrator                                   │
└─────────────────────────────────────────────────────────────┘
```

## What You Can Configure

### 1. Machine Templates

Define reusable machine types with:

**Sensors**:
- Type (float, integer, boolean, string)
- Value ranges
- Update behaviors (random_walk, sine_wave, static, step, conditional)
- Anomaly detection thresholds

**Operations**:
- Duration (fixed, range, or formula-based)
- Required and optional inputs
- Outputs produced
- Failure modes with probabilities
- Sensor impacts during operation

**Telemetry**:
- Publish intervals
- Custom metrics (calculated from sensors)
- Aggregations (avg, min, max, stddev over time windows)

**Maintenance**:
- Scheduled maintenance intervals
- Performance degradation over time

**Dependencies**:
- Materials consumed
- Utilities required (electricity, gas, water)
- Tools needed

### 2. Factory Configurations

Define complete factory with:

**Machines**:
- Instance IDs and names
- Template references
- Physical locations
- Configuration overrides

**Workflows**:
- Production steps
- Machine assignments
- Parallel processing
- Conditional execution
- Retry logic

**Production Config**:
- Mode (continuous, batch, on_demand, scheduled)
- Target production rates
- Shift schedules
- Quality control parameters
- Inventory simulation
- KPIs to track

**Integration**:
- MQTT broker settings
- Database connections
- Site/location identifiers

## Quick Start

### Step 1: Create Machine Template

Create `machine-templates/my-machine.json`:

```json
{
  "machine_type": "stamping",
  "machine_name": "Metal Stamping Press",
  "category": "fabrication",
  "sensors": [
    {
      "name": "hydraulic_pressure",
      "type": "float",
      "unit": "psi",
      "range": {"min": 1000, "max": 5000},
      "initial_value": "random",
      "update_behavior": {
        "type": "random_walk",
        "parameters": {"variation": 50, "bounds_check": true}
      }
    }
  ],
  "operations": [
    {
      "name": "stamp_panel",
      "duration": {"type": "fixed", "value": 5.0},
      "inputs": [{
        "name": "metal_sheet",
        "type": "material",
        "required": true
      }],
      "outputs": [{
        "name": "stamped_panel",
        "type": "product"
      }]
    }
  ],
  "telemetry_config": {
    "publish_interval": 5.0,
    "sensor_update_interval": 1.0,
    "metrics": []
  }
}
```

### Step 2: Create Factory Configuration

Create `factory-configs/my-factory.json`:

```json
{
  "factory_id": "my-factory-001",
  "factory_name": "My Manufacturing Plant",
  "factory_type": "custom",
  "description": "Custom manufacturing facility",

  "machines": [
    {
      "machine_id": "stamping-01",
      "machine_type": "stamping",
      "template_file": "machine-templates/my-machine.json",
      "instance_name": "Stamping Press #1",
      "enabled": true
    }
  ],

  "workflows": [
    {
      "workflow_id": "basic-production",
      "workflow_name": "Basic Production",
      "product_type": "stamped_part",
      "steps": [
        {
          "step_id": "step-1",
          "machine_type": "stamping",
          "operation": "stamp_panel",
          "required_inputs": ["metal_sheet"],
          "outputs": ["stamped_panel"]
        }
      ]
    }
  ],

  "production_config": {
    "mode": "continuous",
    "target_rate": {"value": 100, "unit": "units_per_hour"}
  },

  "mqtt_config": {
    "broker": "mqttbroker",
    "port": 1883,
    "site_id": "my-factory-001"
  }
}
```

### Step 3: Generate Factory

```bash
python tools/factory_generator.py factory-configs/my-factory.json
```

This generates:
```
generated-factories/my-factory-001/
├── machines/
│   └── stamping/
│       └── stamping_machine.py
├── workflows/
│   └── basic-production.json
├── docker-compose.yml
└── README.md
```

### Step 4: Run Factory

```bash
cd generated-factories/my-factory-001
docker compose up --build
```

## Real Examples

### Example 1: Automotive Assembly Plant

**Features**:
- 6 machine types (stamping, welding, painting, assembly, inspection)
- 2 workflows (sedan, SUV)
- Parallel welding operations
- Quality inspection with conditional execution
- OEE tracking

**File**: `factory-configs/automotive-assembly-plant.json`

**Machines**:
- Stamping press for body panels
- 2x Robotic welders (parallel operation)
- Automated paint booth
- Assembly line
- Quality inspection station

**Production**:
- Continuous mode
- 50 vehicles/day
- 3 shifts, 8 hours each
- 100% inspection rate

### Example 2: Food Processing Plant

**Features**:
- 6 machine types (mixing, baking, cooling, quality, packaging, labeling)
- 2 workflows (cookies, bread)
- Batch production mode
- Food safety compliance
- Inventory tracking

**File**: `factory-configs/food-processing-plant.json`

**Machines**:
- Industrial mixer
- Convection oven
- Cooling conveyor
- Quality scanner
- Automated packager
- Label applicator

**Production**:
- Batch mode
- 20 batches/day
- Time-scaled simulation (10x faster)
- Yield tracking

## Machine Template Features

### Sensor Update Behaviors

**Random Walk** (most common):
```json
{
  "update_behavior": {
    "type": "random_walk",
    "parameters": {
      "variation": 0.5,
      "bounds_check": true
    }
  }
}
```
Sensor value changes randomly within bounds.

**Sine Wave** (cyclical):
```json
{
  "update_behavior": {
    "type": "sine_wave",
    "parameters": {
      "amplitude": 10.0,
      "frequency": 0.05,
      "offset": 50.0
    }
  }
}
```
Sensor follows sine wave pattern.

**Step Changes**:
```json
{
  "update_behavior": {
    "type": "step",
    "parameters": {
      "step_size": 5.0,
      "probability": 0.1
    }
  }
}
```
Value jumps by step_size with given probability.

**Conditional**:
```json
{
  "update_behavior": {
    "type": "conditional",
    "parameters": {
      "condition": "operation_running"
    }
  }
}
```
Changes based on machine state.

### Operation Duration Types

**Fixed Duration**:
```json
{
  "duration": {
    "type": "fixed",
    "value": 30.0
  }
}
```

**Range (random)**:
```json
{
  "duration": {
    "type": "range",
    "min": 20.0,
    "max": 40.0
  }
}
```

**Formula-based**:
```json
{
  "duration": {
    "type": "formula",
    "formula": "input_quantity * 0.5 + base_time"
  }
}
```

### Failure Modes

Define realistic failures:
```json
{
  "failure_modes": [
    {
      "name": "overheating",
      "probability": 0.02,
      "conditions": {
        "temperature": {"min": 80, "max": 100}
      },
      "recovery_time": 120
    },
    {
      "name": "material_jam",
      "probability": 0.01,
      "recovery_time": 60
    }
  ]
}
```

### Custom Metrics

Calculate derived metrics:
```json
{
  "metrics": [
    {
      "name": "efficiency_index",
      "formula": "(actual_output / target_output) * 100",
      "unit": "percent"
    },
    {
      "name": "energy_per_unit",
      "formula": "total_energy / units_produced",
      "unit": "kwh_per_unit"
    }
  ]
}
```

## Factory Configuration Features

### Production Modes

**Continuous**: 24/7 production
```json
{
  "mode": "continuous",
  "target_rate": {"value": 100, "unit": "units_per_hour"}
}
```

**Batch**: Discrete batches
```json
{
  "mode": "batch",
  "target_rate": {"value": 20, "unit": "batches_per_day"}
}
```

**On-Demand**: Respond to orders
```json
{
  "mode": "on_demand"
}
```

**Scheduled**: Based on schedule
```json
{
  "mode": "scheduled",
  "shift_schedule": {
    "shifts_per_day": 2,
    "hours_per_shift": 8,
    "days_per_week": 5
  }
}
```

### Parallel Processing

Execute steps in parallel:
```json
{
  "steps": [
    {
      "step_id": "weld-front",
      "machine_id": "welding-01",
      "parallel_group": 1
    },
    {
      "step_id": "weld-rear",
      "machine_id": "welding-02",
      "parallel_group": 1
    }
  ]
}
```

Both welding operations run simultaneously.

### Conditional Steps

Execute based on conditions:
```json
{
  "step_id": "rework",
  "conditions": [
    {
      "type": "quality",
      "expression": "quality_score < 0.9"
    }
  ]
}
```

### Machine Overrides

Override template defaults per instance:
```json
{
  "machine_id": "welding-01",
  "template_file": "machine-templates/welding-machine.json",
  "overrides": {
    "sensors": {
      "temperature": {
        "range": {"min": 30, "max": 90}
      }
    },
    "telemetry_config": {
      "publish_interval": 3.0
    },
    "failure_rate": 0.05
  }
}
```

### KPI Tracking

Define custom KPIs:
```json
{
  "kpis": [
    {
      "name": "oee",
      "formula": "availability * performance * quality",
      "unit": "percent",
      "target": 85.0
    },
    {
      "name": "throughput",
      "formula": "completed_units / elapsed_hours",
      "unit": "units_per_hour",
      "target": 50.0
    }
  ]
}
```

### Inventory Simulation

Track materials:
```json
{
  "inventory": {
    "enabled": true,
    "materials": [
      {
        "name": "steel_sheet",
        "initial_quantity": 10000,
        "reorder_point": 2000,
        "reorder_quantity": 8000,
        "unit": "kg"
      }
    ]
  }
}
```

## Use Cases

### 1. Automotive Manufacturing
- Stamping, welding, painting, assembly
- Multiple product variants (sedan, SUV, truck)
- High-volume continuous production
- Strict quality requirements

### 2. Food Processing
- Mixing, baking, cooling, packaging
- Batch production
- Food safety tracking
- Expiration date management

### 3. Electronics Assembly
- PCB fabrication, component placement, soldering, testing
- High precision requirements
- Defect tracking
- Traceability

### 4. Pharmaceutical Production
- Mixing, tablet pressing, coating, packaging
- Strict compliance requirements
- Batch tracking
- Quality validation

### 5. Textile Manufacturing
- Cutting, sewing, dyeing, finishing
- Multiple product types
- Color/size variations
- Quality grading

### 6. Chemical Processing
- Mixing, heating, cooling, filtering
- Continuous flow
- Safety monitoring
- Yield optimization

## Benefits

### For Development
- **No code changes needed** - pure JSON configuration
- **Rapid prototyping** - create new factory types in minutes
- **Reusable templates** - share machine definitions across factories
- **Version control** - track factory configs in git

### For Testing
- **Realistic simulation** - sensor behaviors, failures, timing
- **Controllable randomness** - adjust failure rates, timing variations
- **Scalable** - test with 1 machine or 100
- **Reproducible** - same config = same behavior

### For Learning
- **Understand manufacturing** - see how production flows work
- **MQTT patterns** - learn IoT communication
- **Database design** - track production data
- **Monitoring** - practice with metrics and KPIs

### For Demos
- **Impressive** - show complete factory in minutes
- **Customizable** - adjust to audience needs
- **Real-time** - live MQTT messages, sensor data
- **Visualizable** - ready for dashboards

## Comparison: Before vs After

### Before (T-Shirt Factory Only)

```python
# Hardcoded Python
class CuttingMachine:
    def __init__(self):
        self.blade_temperature = 25.0
        # ... hardcoded sensors

    def cut_fabric(self, fabric):
        # ... hardcoded logic
```

**Limitations**:
- Only T-shirt production
- Code changes for new machines
- Fixed workflows
- Single factory type

### After (Universal Platform)

```json
{
  "machine_type": "cutting",
  "sensors": [...],
  "operations": [...]
}
```

**Capabilities**:
- **Any manufacturing domain**
- **Zero code changes**
- **Infinite machine types**
- **Unlimited factory configurations**

## File Structure

```
tshirt-factory/
├── schemas/                           # JSON schemas
│   ├── machine-template-schema.json
│   └── factory-config-schema.json
│
├── machine-templates/                 # Reusable machine definitions
│   ├── welding-machine.json
│   ├── painting-machine.json
│   ├── assembly-machine.json
│   └── ... (add unlimited types)
│
├── factory-configs/                   # Complete factory definitions
│   ├── automotive-assembly-plant.json
│   ├── food-processing-plant.json
│   ├── electronics-factory.json
│   └── ... (add unlimited factories)
│
├── tools/
│   ├── factory_generator.py          # Generate factory from JSON
│   └── create_machine.py              # Create machine template
│
└── generated-factories/               # Generated factory outputs
    ├── automotive-plant-001/
    ├── food-processing-001/
    └── ...
```

## Advanced Features

### Time Scaling

Run simulations faster or slower:
```json
{
  "simulation": {
    "time_scale": 10.0
  }
}
```
- `1.0` = real-time
- `10.0` = 10x faster
- `0.1` = 10x slower (detailed observation)

### Anomaly Injection

Test fault handling:
```json
{
  "simulation": {
    "enable_anomalies": true,
    "anomaly_frequency": 0.5
  }
}
```

### Machine Degradation

Simulate wear over time:
```json
{
  "maintenance": {
    "degradation": {
      "enabled": true,
      "rate": 0.001,
      "affects": ["speed", "precision"]
    }
  }
}
```

### Formula-Based Logic

Use formulas for dynamic behavior:
- **Duration**: `"formula": "length * speed_factor + setup_time"`
- **Consumption**: `"formula": "power * time * efficiency"`
- **Metrics**: `"formula": "(good_parts / total_parts) * 100"`

## Next Steps

1. **Explore Examples**
   - Study `automotive-assembly-plant.json`
   - Study `food-processing-plant.json`

2. **Create Your Factory**
   - Define machine templates
   - Create factory configuration
   - Generate and run

3. **Add Integrations**
   - Connect to cloud platforms (AWS IoT, Azure)
   - Build custom dashboards
   - Add analytics

4. **Scale**
   - Add more machines
   - Create complex workflows
   - Simulate large facilities

## Resources

- **Schemas**: `schemas/` - JSON schema definitions
- **Examples**: `factory-configs/` - Complete factory examples
- **Templates**: `machine-templates/` - Machine type definitions
- **Generator**: `tools/factory_generator.py` - Factory generation tool

## Summary

You now have a **universal factory simulation platform** that can model ANY manufacturing process through JSON configuration:

✅ **Define machines** with sensors, operations, failures
✅ **Configure factories** with workflows, production parameters
✅ **Generate code** automatically from JSON
✅ **Run simulations** with realistic behaviors
✅ **Scale infinitely** - add unlimited machines and factories

**Time to create a new factory type: 30-60 minutes** (including testing)

---

**Transform from T-Shirt Factory → Universal Manufacturing Platform** 🏭🚀
