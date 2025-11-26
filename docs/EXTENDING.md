# Extending the System: Custom Factories & Components

**Guide for creating custom factories, machines, and frontends**

---

## Table of Contents
1. [Creating Custom Factories](#creating-custom-factories)
2. [Creating Custom Machines](#creating-custom-machines)
3. [Creating Custom Frontends](#creating-custom-frontends)
4. [Extending Services](#extending-services)
5. [Custom Workflows](#custom-workflows)

---

## Creating Custom Factories

### Step 1: Create Machine Template (if needed)

Most factories can use existing templates. If you need a new machine type:

**File**: `machine-templates/my-new-machine.json`

```json
{
  "name": "Robotic Arm",
  "description": "Six-axis industrial robot for assembly",
  "machine_id_template": "robot-{number}",
  "type": "robotic_arm",
  "sensors": {
    "joint_1_angle": {
      "description": "Joint 1 angle (degrees)",
      "min": 0,
      "max": 180,
      "unit": "°",
      "update_frequency": 2000
    },
    "joint_2_angle": {
      "description": "Joint 2 angle (degrees)",
      "min": -90,
      "max": 90,
      "unit": "°",
      "update_frequency": 2000
    },
    "end_effector_force": {
      "description": "Force exerted by end effector",
      "min": 0,
      "max": 100,
      "unit": "N",
      "update_frequency": 2000
    },
    "end_effector_temperature": {
      "description": "Temperature at end effector",
      "min": 20,
      "max": 80,
      "unit": "°C",
      "update_frequency": 2000
    }
  },
  "operations": [
    {
      "name": "pick_and_place",
      "description": "Pick object and place at new location",
      "duration_seconds": 15,
      "required_sensors": ["joint_1_angle", "joint_2_angle", "end_effector_force"],
      "failure_prone": true,
      "error_description": "Part drop or collision"
    },
    {
      "name": "weld_joint",
      "description": "Weld two components",
      "duration_seconds": 30,
      "required_sensors": ["end_effector_temperature", "end_effector_force"],
      "failure_prone": true,
      "error_description": "Weld quality issue"
    }
  ],
  "failure_modes": [
    {
      "sensor": "end_effector_temperature",
      "condition": "value > 75",
      "action": "emergency_stop",
      "description": "Overtemperature shutdown"
    }
  ]
}
```

### Step 2: Create Factory Configuration

**File**: `factory-configs/my-electronics-plant.json`

```json
{
  "factory_id": "electronics-plant-001",
  "factory_name": "Electronics Manufacturing Plant",
  "factory_type": "electronics_manufacturing",
  "location": "Tokyo, Japan",
  "description": "High-precision electronics assembly plant",
  
  "machines": [
    {
      "id": "pcb-assembly-01",
      "template": "pcb-assembly.json",
      "count": 2,
      "parameters": {
        "board_type": "mixed_signal"
      }
    },
    {
      "id": "soldering-01",
      "template": "my-new-machine.json",
      "count": 1,
      "parameters": {
        "solder_type": "lead_free"
      }
    },
    {
      "id": "testing-01",
      "template": "quality-check-machine.json",
      "count": 2
    }
  ],
  
  "workflows": [
    {
      "file": "electronics-assembly.json",
      "enabled": true,
      "priority": 1
    }
  ],
  
  "production_config": {
    "max_orders_queue": 100,
    "default_success_rate": 0.98,
    "default_failure_rate": 0.02,
    "shift_duration_hours": 8,
    "orders_per_hour": 240
  },
  
  "database_config": {
    "enable_timescaledb": true,
    "telemetry_retention_days": 30,
    "enable_data_compression": true
  },
  
  "monitoring_config": {
    "enable_alerts": true,
    "alert_threshold_error_rate": 0.05,
    "enable_predictive_maintenance": false
  }
}
```

### Step 3: Create Workflow Template (if needed)

**File**: `workflows/electronics-assembly.json`

```json
{
  "workflow_id": "electronics-assembly-v1",
  "workflow_name": "Standard Electronics Assembly",
  "description": "PCB assembly, soldering, testing, and packaging",
  "version": "1.0",
  
  "steps": [
    {
      "step_number": 1,
      "name": "Component Placement",
      "machine_type": "pcb_assembly",
      "operation": "place_components",
      "parameters": {
        "precision_level": "high",
        "retry_on_fail": true
      },
      "timeout_seconds": 60,
      "next_step_on_success": 2,
      "next_step_on_failure": 3
    },
    {
      "step_number": 2,
      "name": "Soldering",
      "machine_type": "robotic_arm",
      "operation": "weld_joint",
      "parameters": {
        "solder_profile": "lead_free",
        "inspection_after": true
      },
      "timeout_seconds": 90,
      "next_step_on_success": 3,
      "next_step_on_failure": 4
    },
    {
      "step_number": 3,
      "name": "Quality Testing",
      "machine_type": "quality_check",
      "operation": "test_functionality",
      "parameters": {
        "test_duration": 30,
        "voltage_test": true
      },
      "timeout_seconds": 120,
      "next_step_on_success": 5,
      "next_step_on_failure": 6
    },
    {
      "step_number": 4,
      "name": "Rework",
      "machine_type": "robotic_arm",
      "operation": "rework_component",
      "parameters": {
        "max_rework_cycles": 2
      },
      "timeout_seconds": 180,
      "next_step_on_success": 3,
      "next_step_on_failure": 6
    },
    {
      "step_number": 5,
      "name": "Packaging",
      "machine_type": "packaging",
      "operation": "package_product",
      "timeout_seconds": 60,
      "next_step_on_success": 7,
      "next_step_on_failure": 7
    },
    {
      "step_number": 6,
      "name": "Scrap",
      "status": "failed",
      "description": "Product scrapped due to repeated failures"
    },
    {
      "step_number": 7,
      "name": "Complete",
      "status": "success",
      "description": "Manufacturing complete"
    }
  ],
  
  "error_handlers": [
    {
      "condition": "step_timeout",
      "action": "retry_step",
      "retry_count": 2,
      "retry_delay_seconds": 5
    },
    {
      "condition": "machine_error",
      "action": "skip_step",
      "next_step": 6
    }
  ]
}
```

### Step 4: Generate Factory

```bash
# Validate configuration before generation
python3 tools/factory_generator.py factory-configs/my-electronics-plant.json

# This outputs:
# ✅ Factory generated successfully in: generated-factories/electronics-plant-001
```

### Step 5: Start Factory

```bash
cd generated-factories/electronics-plant-001
docker compose up --build
```

---

## Creating Custom Machines

### Machine Lifecycle

Each machine (generated Python class) follows this pattern:

```python
from shared.base_machine import BaseMachine

class RoboticArmMachine(BaseMachine):
    """Robotic arm assembly machine"""
    
    def __init__(self, machine_id, machine_type, machine_name):
        super().__init__(machine_id, machine_type, machine_name)
        self.failure_rate = 0.02  # 2% failure rate
    
    def _initialize_sensors(self):
        """Initialize all sensors with random starting values"""
        return {
            "joint_1_angle": random.uniform(0, 180),
            "joint_2_angle": random.uniform(-90, 90),
            "end_effector_force": random.uniform(0, 100),
            "end_effector_temperature": random.uniform(20, 80)
        }
    
    def update_sensors(self):
        """Called every 2 seconds to update sensor values"""
        # Simulate sensor drift
        self.sensor_data["joint_1_angle"] += random.uniform(-2, 2)
        self.sensor_data["joint_2_angle"] += random.uniform(-1, 1)
        self.sensor_data["end_effector_force"] += random.uniform(-5, 5)
        self.sensor_data["end_effector_temperature"] += random.uniform(-0.5, 0.5)
        
        # Keep within bounds
        self.sensor_data["joint_1_angle"] = max(0, min(180, self.sensor_data["joint_1_angle"]))
    
    def validate_process_data(self, process_data):
        """Validate that operation parameters are valid"""
        required = ["operation"]
        return all(key in process_data for key in required)
    
    def process_operation(self, process_data, processing_time=None):
        """Execute an operation"""
        operation = process_data.get("operation")
        
        if operation == "pick_and_place":
            return self._pick_and_place(processing_time or 15)
        elif operation == "weld_joint":
            return self._weld_joint(processing_time or 30)
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    def _pick_and_place(self, duration):
        """Execute pick and place operation"""
        # Simulate arm movement
        time.sleep(duration / 2)
        
        # Check for failure
        if random.random() < self.failure_rate:
            self.runtime_state = "error"
            self.failed_operations += 1
            return {"success": False, "error": "Part drop detected"}
        
        self.total_operations += 1
        return {"success": True, "items_placed": 1}
    
    def _weld_joint(self, duration):
        """Execute welding operation"""
        # Simulate heating and welding
        initial_temp = self.sensor_data["end_effector_temperature"]
        self.sensor_data["end_effector_temperature"] = 700  # Heating
        
        time.sleep(duration)
        
        # Cool down
        self.sensor_data["end_effector_temperature"] = initial_temp
        
        # Check for failure
        if random.random() < self.failure_rate:
            self.runtime_state = "error"
            self.failed_operations += 1
            return {"success": False, "error": "Weld quality issue"}
        
        self.total_operations += 1
        return {"success": True, "welds": 1}
```

**Generated Code Location**: `generated-factories/{factory-id}/services/machines/{type}/`

---

## Creating Custom Frontends

### Option 1: Extend Angular Customizer

**Base**: `tshirt-customizer/` (Angular + Material Design)

**Steps**:

1. **Copy template**
```bash
cp -r tshirt-customizer electronics-customizer
cd electronics-customizer
npm install
```

2. **Update configuration**
```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5001',
  factoryId: 'electronics-plant-001'
};
```

3. **Create components**
```bash
ng generate component components/pcb-designer
ng generate component components/component-placement
ng generate component components/order-summary
```

4. **Update API service**
```typescript
// src/app/api.service.ts
export class ApiService {
  constructor(private http: HttpClient) {}
  
  placeElectronicsOrder(config: PCBConfig) {
    return this.http.post(`${environment.apiUrl}/production`, {
      product_type: 'pcb_assembly',
      parameters: config
    });
  }
  
  getMachineStatus(machineId: string) {
    return this.http.get(`${environment.apiUrl}/machines/${machineId}`);
  }
}
```

5. **Add WebSocket listener**
```typescript
// src/app/services/mqtt.service.ts
export class MqttService {
  constructor(private wsService: WebsocketService) {}
  
  subscribeToMachineStatus(machineId: string) {
    return this.wsService.subscribe(`factory/electronics-plant-001/machines/${machineId}/status`);
  }
}
```

6. **Serve frontend**
```bash
ng serve
# Open http://localhost:4200
```

### Option 2: Create HTML/JS Frontend

**Base**: `vehicle-customizer/` (Pure HTML/JavaScript)

**Steps**:

1. **Create project structure**
```
my-factory-ui/
├── index.html
├── css/
│   └── styles.css
├── js/
│   ├── api.js        (REST API wrapper)
│   ├── mqtt.js       (WebSocket MQTT client)
│   └── app.js        (Main application)
└── assets/
    └── images/
```

2. **Create HTML template**
```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>My Factory UI</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div class="container">
        <h1>My Factory Control</h1>
        
        <div class="machine-status">
            <div class="machine" id="machine-1">
                <h3>Machine 1</h3>
                <p>Status: <span class="status">Loading...</span></p>
                <p>Operations: <span class="operations">0</span></p>
            </div>
        </div>
        
        <div class="production">
            <h2>New Order</h2>
            <form id="orderForm">
                <input type="text" placeholder="Product name">
                <input type="number" placeholder="Quantity">
                <button type="submit">Place Order</button>
            </form>
        </div>
    </div>
    
    <script src="js/api.js"></script>
    <script src="js/mqtt.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

3. **Create API wrapper**
```javascript
// js/api.js
class API {
    constructor(baseUrl = 'http://localhost:5001') {
        this.baseUrl = baseUrl;
    }
    
    async getMachines() {
        const res = await fetch(`${this.baseUrl}/machines`);
        return res.json();
    }
    
    async placeOrder(productType, parameters) {
        const res = await fetch(`${this.baseUrl}/production`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_type: productType,
                parameters: parameters
            })
        });
        return res.json();
    }
    
    async getMachineStatus(machineId) {
        const res = await fetch(`${this.baseUrl}/machines/${machineId}`);
        return res.json();
    }
}
```

4. **Create MQTT WebSocket wrapper**
```javascript
// js/mqtt.js
class MQTT {
    constructor(brokerUrl = 'ws://localhost:9001') {
        this.socket = new WebSocket(brokerUrl);
        this.callbacks = {};
    }
    
    subscribe(topic, callback) {
        if (!this.callbacks[topic]) {
            this.callbacks[topic] = [];
        }
        this.callbacks[topic].push(callback);
    }
    
    onMessage(message) {
        const { topic, payload } = JSON.parse(message.data);
        if (this.callbacks[topic]) {
            this.callbacks[topic].forEach(cb => cb(payload));
        }
    }
}
```

5. **Create main application**
```javascript
// js/app.js
const api = new API();
const mqtt = new MQTT();

// Initialize
async function init() {
    const machines = await api.getMachines();
    displayMachines(machines);
    
    // Subscribe to all machine status updates
    machines.forEach(machine => {
        mqtt.subscribe(
            `factory/*/machines/${machine.machine_id}/status`,
            (payload) => updateMachineStatus(machine.machine_id, payload)
        );
    });
}

// Display functions
function displayMachines(machines) {
    const container = document.querySelector('.machine-status');
    container.innerHTML = machines.map(m => `
        <div class="machine" id="machine-${m.machine_id}">
            <h3>${m.machine_id}</h3>
            <p>Status: <span class="status">${m.runtime_state}</span></p>
            <p>Operations: <span class="operations">${m.total_operations}</span></p>
        </div>
    `).join('');
}

function updateMachineStatus(machineId, status) {
    const machine = document.getElementById(`machine-${machineId}`);
    if (machine) {
        machine.querySelector('.status').textContent = status.runtime_state;
        machine.querySelector('.operations').textContent = status.total_operations;
    }
}

// Order form handler
document.getElementById('orderForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const result = await api.placeOrder('my_product', {
        name: 'Custom Order'
    });
    alert('Order placed: ' + result.order_id);
});

// Start application
init();
```

---

## Extending Services

### Custom Orchestrator Logic

**File**: `production-orchestrator/orchestrator.py`

```python
# Add custom production rules
class CustomOrchestrator:
    def __init__(self, factory_id):
        self.factory_id = factory_id
        self.mqtt_client = MQTTClientWrapper(...)
    
    def handle_production_request(self, request):
        """Custom production request handler"""
        product_type = request.get('product_type')
        
        # Custom routing logic
        if product_type == 'high_priority':
            workflow_name = 'express-workflow.json'
            priority = 1
        else:
            workflow_name = 'standard-workflow.json'
            priority = 0
        
        # Load and execute workflow
        self.execute_workflow(workflow_name, request, priority)
    
    def execute_workflow(self, workflow_name, parameters, priority):
        """Execute production workflow"""
        # Load workflow template
        workflow = self.load_workflow(workflow_name)
        
        # Create workflow instance
        instance = {
            'workflow_id': workflow_name,
            'parameters': parameters,
            'priority': priority,
            'steps_completed': 0,
            'status': 'running'
        }
        
        # Execute each step
        for step in workflow['steps']:
            self.execute_step(step, parameters)
```

### Custom Monitoring Rules

**File**: `monitoring-service/monitoring_service.py`

```python
# Add custom alerting
def check_machine_health(machine_id, status_data):
    """Custom health check rules"""
    runtime_state = status_data.get("runtime_state")
    total_ops = status_data.get('total_operations', 0)
    failed_ops = status_data.get('failed_operations', 0)
    
    # Rule 1: High failure rate
    if total_ops > 0:
        failure_rate = failed_ops / total_ops
        if failure_rate > 0.05:  # More than 5% failures
            logger.warning(f"⚠️ ALERT: {machine_id} high failure rate: {failure_rate:.2%}")
            # Send alert to email/SMS/Slack
            send_alert(f"{machine_id} high failure rate", "critical")
    
    # Rule 2: Machine stuck
    if runtime_state == "busy" and self.is_stuck(machine_id):
        logger.error(f"❌ ERROR: {machine_id} appears stuck")
        send_alert(f"{machine_id} stuck", "critical")
    
    # Rule 3: Predictive maintenance
    if self.should_schedule_maintenance(machine_id):
        logger.info(f"🔧 MAINTENANCE: {machine_id} due for maintenance")
        send_alert(f"{machine_id} maintenance due", "warning")
```

---

## Custom Workflows

### Workflow Structure

```json
{
  "workflow_id": "custom-complex-workflow",
  "name": "Complex Multi-Step Process",
  "steps": [
    {
      "step_number": 1,
      "name": "Parallel Processing",
      "type": "parallel",
      "machine_groups": [
        ["machine-1", "machine-2"],
        ["machine-3", "machine-4"]
      ]
    },
    {
      "step_number": 2,
      "name": "Conditional Branch",
      "type": "conditional",
      "condition": "quality_check_passed",
      "on_true": {"next": 3},
      "on_false": {"next": 4}
    },
    {
      "step_number": 3,
      "name": "Normal Path",
      "machine_type": "packaging",
      "operation": "package"
    },
    {
      "step_number": 4,
      "name": "Rework Path",
      "machine_type": "rework_station",
      "operation": "repair"
    }
  ]
}
```

---

**Next Steps**: Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.
