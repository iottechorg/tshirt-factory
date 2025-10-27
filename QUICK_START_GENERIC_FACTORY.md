# Quick Start: Generic Factory System

Create any factory type in 3 steps using JSON configuration!

## Concept

**No more coding** - Define your entire factory in JSON:
- Machine types with sensors and operations
- Factory configuration with workflows
- Production parameters
- Auto-generate everything!

## Step 1: Define Machine Template (5 min)

Create `machine-templates/myMachine.json`:

```json
{
  "machine_type": "assembly",
  "machine_name": "Assembly Robot",
  "category": "assembly",

  "sensors": [
    {
      "name": "arm_position",
      "type": "float",
      "unit": "degrees",
      "range": {"min": 0, "max": 180},
      "initial_value": "random",
      "update_behavior": {
        "type": "random_walk",
        "parameters": {"variation": 1.0, "bounds_check": true}
      }
    },
    {
      "name": "gripper_force",
      "type": "float",
      "unit": "newtons",
      "range": {"min": 0, "max": 100},
      "initial_value": 50,
      "update_behavior": {
        "type": "random_walk",
        "parameters": {"variation": 2.0, "bounds_check": true}
      }
    }
  ],

  "operations": [
    {
      "name": "pick_and_place",
      "display_name": "Pick and Place",
      "duration": {"type": "fixed", "value": 3.0},
      "inputs": [
        {"name": "component", "type": "material", "required": true}
      ],
      "outputs": [
        {"name": "assembled_part", "type": "product"}
      ]
    }
  ],

  "telemetry_config": {
    "publish_interval": 5.0,
    "sensor_update_interval": 1.0,
    "metrics": []
  }
}
```

## Step 2: Create Factory Config (10 min)

Create `factory-configs/my-factory.json`:

```json
{
  "factory_id": "electronics-factory-001",
  "factory_name": "Electronics Assembly Plant",
  "factory_type": "electronics",
  "description": "PCB assembly and testing facility",

  "machines": [
    {
      "machine_id": "assembly-01",
      "machine_type": "assembly",
      "template_file": "machine-templates/myMachine.json",
      "instance_name": "Assembly Robot #1",
      "location": {"zone": "assembly", "line": "main", "position": "A1"},
      "enabled": true
    },
    {
      "machine_id": "assembly-02",
      "machine_type": "assembly",
      "template_file": "machine-templates/myMachine.json",
      "instance_name": "Assembly Robot #2",
      "location": {"zone": "assembly", "line": "main", "position": "A2"},
      "enabled": true
    }
  ],

  "workflows": [
    {
      "workflow_id": "pcb-assembly",
      "workflow_name": "PCB Assembly Line",
      "product_type": "pcb",
      "description": "Assemble PCB with components",

      "steps": [
        {
          "step_id": "step-1",
          "step_name": "Place IC chips",
          "machine_type": "assembly",
          "operation": "pick_and_place",
          "parameters": {"component": "ic_chip"},
          "required_inputs": ["pcb_board", "ic_chip"],
          "outputs": ["pcb_with_ic"],
          "timeout_seconds": 60
        },
        {
          "step_id": "step-2",
          "step_name": "Place capacitors",
          "machine_type": "assembly",
          "operation": "pick_and_place",
          "parameters": {"component": "capacitor"},
          "required_inputs": ["pcb_with_ic", "capacitor"],
          "outputs": ["assembled_pcb"],
          "timeout_seconds": 60
        }
      ],

      "metadata": {
        "estimated_time_minutes": 5,
        "complexity": "standard"
      }
    }
  ],

  "production_config": {
    "mode": "continuous",
    "target_rate": {"value": 200, "unit": "units_per_hour"},
    "shift_schedule": {
      "shifts_per_day": 2,
      "hours_per_shift": 8,
      "days_per_week": 5
    },
    "quality_control": {
      "enabled": true,
      "inspection_rate": 0.1,
      "rejection_threshold": 0.98
    },
    "simulation": {
      "time_scale": 5.0,
      "randomness": 0.1,
      "enable_anomalies": true,
      "anomaly_frequency": 0.2
    }
  },

  "mqtt_config": {
    "broker": "mqttbroker",
    "port": 1883,
    "site_id": "electronics-factory-001",
    "topic_prefix": "factory",
    "qos": 1
  },

  "database_config": {
    "enabled": true,
    "type": "postgresql",
    "connection": {
      "host": "postgres",
      "port": 5432,
      "database": "electronics_factory",
      "user": "factory_user",
      "password": "factory_pass"
    }
  },

  "metadata": {
    "version": "1.0.0",
    "created_date": "2025-10-27T00:00:00Z",
    "tags": ["electronics", "pcb", "assembly"]
  }
}
```

## Step 3: Generate & Run (2 min)

```bash
# Generate factory from config
python tools/factory_generator.py factory-configs/my-factory.json

# Navigate to generated factory
cd generated-factories/electronics-factory-001

# Start factory
docker compose up --build

# In another terminal, monitor MQTT
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Send production order
mosquitto_pub -h localhost -p 31883 \
  -t "factory/electronics-factory-001/production/request" \
  -m '{"product_type": "pcb", "quantity": 10}'
```

## Example Factories

### Automotive Factory

```json
{
  "factory_type": "automotive",
  "machines": ["stamping", "welding", "painting", "assembly", "inspection"],
  "workflows": ["sedan-production", "suv-production"],
  "production_config": {
    "mode": "continuous",
    "target_rate": {"value": 50, "unit": "units_per_day"}
  }
}
```

**File**: `factory-configs/automotive-assembly-plant.json`

### Food Processing

```json
{
  "factory_type": "food_processing",
  "machines": ["mixing", "baking", "cooling", "packaging", "labeling"],
  "workflows": ["cookie-production", "bread-production"],
  "production_config": {
    "mode": "batch",
    "target_rate": {"value": 20, "unit": "batches_per_day"}
  }
}
```

**File**: `factory-configs/food-processing-plant.json`

## Common Sensor Types

```json
// Temperature sensor with sine wave
{
  "name": "temperature",
  "type": "float",
  "unit": "celsius",
  "range": {"min": 20, "max": 100},
  "initial_value": 25,
  "update_behavior": {
    "type": "sine_wave",
    "parameters": {
      "amplitude": 5.0,
      "frequency": 0.1,
      "offset": 50.0
    }
  }
}

// Pressure sensor with random walk
{
  "name": "pressure",
  "type": "float",
  "unit": "psi",
  "range": {"min": 0, "max": 150},
  "initial_value": "random",
  "update_behavior": {
    "type": "random_walk",
    "parameters": {"variation": 2.0, "bounds_check": true}
  }
}

// Boolean sensor (on/off)
{
  "name": "motor_active",
  "type": "boolean",
  "unit": "boolean",
  "range": {"values": [true, false]},
  "initial_value": false,
  "update_behavior": {
    "type": "conditional",
    "parameters": {"condition": "operation_running"}
  }
}

// Position sensor with steps
{
  "name": "conveyor_position",
  "type": "float",
  "unit": "meters",
  "range": {"min": 0, "max": 10},
  "initial_value": 0,
  "update_behavior": {
    "type": "step",
    "parameters": {
      "step_size": 0.5,
      "probability": 0.2
    }
  }
}
```

## Common Operations

```json
// Fixed duration
{
  "name": "weld_joint",
  "duration": {"type": "fixed", "value": 5.0},
  "inputs": [{"name": "metal_parts", "type": "material", "required": true}],
  "outputs": [{"name": "welded_assembly", "type": "product"}]
}

// Variable duration (range)
{
  "name": "paint_surface",
  "duration": {"type": "range", "min": 10.0, "max": 30.0},
  "inputs": [{"name": "part", "type": "material", "required": true}],
  "outputs": [{"name": "painted_part", "type": "product"}]
}

// Calculated duration
{
  "name": "cut_material",
  "duration": {
    "type": "formula",
    "formula": "cut_length / cutting_speed * 60"
  },
  "inputs": [
    {"name": "material", "type": "material", "required": true},
    {"name": "cut_length", "type": "parameter", "required": true}
  ],
  "outputs": [{"name": "cut_parts", "type": "product"}]
}
```

## Workflow Patterns

### Sequential Processing

```json
{
  "steps": [
    {"step_id": "step-1", "machine_type": "cutting", "operation": "cut"},
    {"step_id": "step-2", "machine_type": "sewing", "operation": "sew"},
    {"step_id": "step-3", "machine_type": "packaging", "operation": "package"}
  ]
}
```

### Parallel Processing

```json
{
  "steps": [
    {"step_id": "front", "machine_id": "welder-01", "parallel_group": 1},
    {"step_id": "rear", "machine_id": "welder-02", "parallel_group": 1},
    {"step_id": "join", "machine_type": "welding"}
  ]
}
```

### Conditional Steps

```json
{
  "steps": [
    {"step_id": "inspect", "operation": "quality_check"},
    {
      "step_id": "rework",
      "operation": "fix_defects",
      "conditions": [
        {"type": "quality", "expression": "quality_score < 0.9"}
      ]
    }
  ]
}
```

## Production Modes

### Continuous (24/7)

```json
{
  "mode": "continuous",
  "target_rate": {"value": 100, "unit": "units_per_hour"}
}
```

### Batch Production

```json
{
  "mode": "batch",
  "target_rate": {"value": 20, "unit": "batches_per_day"}
}
```

### On-Demand

```json
{
  "mode": "on_demand"
}
```

### Scheduled

```json
{
  "mode": "scheduled",
  "shift_schedule": {
    "shifts_per_day": 3,
    "hours_per_shift": 8,
    "days_per_week": 6
  }
}
```

## Machine Overrides

Override template defaults per instance:

```json
{
  "machine_id": "welder-01",
  "template_file": "machine-templates/welding-machine.json",
  "overrides": {
    "sensors": {
      "temperature": {
        "range": {"min": 40, "max": 90}
      }
    },
    "telemetry_config": {
      "publish_interval": 3.0
    },
    "failure_rate": 0.05
  }
}
```

## Troubleshooting

### Configuration Errors

```bash
# Validate JSON syntax
python -m json.tool factory-configs/my-factory.json

# Check schema (if using validator)
python tools/validate_config.py factory-configs/my-factory.json
```

### Generation Issues

```bash
# Run with verbose output
python tools/factory_generator.py -v factory-configs/my-factory.json

# Check file paths
ls machine-templates/
ls factory-configs/
```

### Runtime Issues

```bash
# Check logs
docker logs electronics-factory-001-assembly-01

# Monitor MQTT
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Check database
docker exec -it electronics-factory-001-postgres psql -U factory_user -d electronics_factory
```

## Tips

1. **Start Simple**: Begin with 1-2 machines, 1 workflow
2. **Copy Examples**: Use existing configs as templates
3. **Test Incrementally**: Add machines one at a time
4. **Monitor MQTT**: Watch messages to understand flow
5. **Adjust Time Scale**: Use `time_scale: 10.0` for faster testing

## Next Steps

1. **Study Examples**
   - `automotive-assembly-plant.json` - Complex factory with 6 machines
   - `food-processing-plant.json` - Batch production example

2. **Customize**
   - Modify sensor ranges
   - Add operations
   - Create workflows

3. **Scale**
   - Add more machines
   - Create multiple workflows
   - Increase production rates

## Resources

- **Full Documentation**: `GENERIC_FACTORY_SYSTEM.md`
- **Schemas**: `schemas/` directory
- **Examples**: `factory-configs/` directory
- **Templates**: `machine-templates/` directory

## Summary

Create any factory in 3 steps:

1. **Define machine templates** (JSON)
2. **Create factory config** (JSON)
3. **Generate and run** (one command)

**Time: 15-20 minutes from idea to running factory!** 🏭

---

**No coding required. Just JSON configuration.** ✨
