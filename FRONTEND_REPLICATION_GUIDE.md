# Frontend Replication Guide

## How to Create Customer-Facing Apps for ANY Factory

This guide shows you how to replicate the **tshirt-customizer** pattern for any generated factory type.

---

## 🎯 The Pattern

All customer-facing frontends follow this universal structure:

```
┌─────────────────────────────────────────────────────────┐
│              Customer Frontend Application              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐      ┌─────────────────────┐    │
│  │  Configuration   │      │   Preview Panel     │    │
│  │     Panel        │      │                     │    │
│  ├──────────────────┤      ├─────────────────────┤    │
│  │ Product options  │      │ Visual preview      │    │
│  │ Feature selection│      │ Price calculation   │    │
│  │ Customization    │      │ Factory info        │    │
│  │                  │      │ Status display      │    │
│  │ [Place Order]    │      │ [Monitor Factory]   │    │
│  └──────────────────┘      └─────────────────────┘    │
│                                                          │
└─────────────┬────────────────────────────────────────────┘
              │
              ▼ HTTP POST
┌─────────────────────────────────────────────────────────┐
│         simple_factory_simulator (API Gateway)          │
│              http://localhost:5001                      │
└─────────────┬────────────────────────────────────────────┘
              │
              ▼ MQTT
┌─────────────────────────────────────────────────────────┐
│           Generated Factory (Any Type)                  │
│   tshirt-factory-001 | automotive-plant-001 | ...      │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Existing Examples

### 1. tshirt-customizer (Angular)
```
Frontend: Angular + Material Design + Tailwind
Factory: tshirt-factory-001
Workflows: standard, premium, custom
Features: Size, color, custom text
```

### 2. vehicle-customizer (HTML/JS)
```
Frontend: HTML + JavaScript + Tailwind
Factory: automotive-plant-001
Workflows: sedan-production, suv-production
Features: Type, color, features (sunroof, leather, etc.)
```

---

## 🚀 Quick Start: Create Your Frontend

### Step 1: Choose Your Technology

**Option A: Simple HTML/JavaScript** (Like vehicle-customizer)
- ✅ No build step
- ✅ Fast prototyping
- ✅ Easy to understand
- ❌ Limited to simple apps

**Option B: Angular** (Like tshirt-customizer)
- ✅ Full framework
- ✅ TypeScript type safety
- ✅ Component architecture
- ❌ Requires build setup

**Option C: React/Vue**
- ✅ Modern frameworks
- ✅ Rich ecosystem
- ✅ Component reusability

### Step 2: Pick Your Factory

Choose from generated factories:
```bash
generated-factories/
├── tshirt-factory-001/
├── automotive-plant-001/
├── electronics-factory-001/
├── pharma-plant-001/
└── food-processing-plant-001/
```

### Step 3: Get Factory Configuration

```bash
# Read factory config to understand workflows
cat factory-configs/your-factory.json

# Key information needed:
- factory_id: "your-factory-001"
- workflows: [ {workflow_id, workflow_name, product_type} ]
- machines: [ list of machines ]
```

---

## 📝 Implementation Guide

### Method 1: HTML/JavaScript Frontend

#### 1. Create Directory Structure
```bash
mkdir -p your-customizer/src
cd your-customizer/src
```

#### 2. Create index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Product Customizer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 min-h-screen">

    <!-- Navigation -->
    <nav class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <h1 class="text-2xl font-bold text-gray-900">Your Product Customizer</h1>
                <span class="text-sm text-gray-600">Factory: <strong>your-factory-001</strong></span>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

            <!-- Configuration Panel -->
            <div class="bg-white rounded-2xl shadow-xl p-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Configure Your Product</h2>

                <!-- Your product options here -->
                <div class="mb-6">
                    <label class="block text-sm font-semibold text-gray-700 mb-3">Option 1</label>
                    <!-- Add your controls -->
                </div>

                <button onclick="placeOrder()"
                        class="w-full mt-8 px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-bold text-lg hover:from-indigo-700 hover:to-purple-700">
                    Place Order
                </button>

                <div id="order-status" class="mt-6 hidden">
                    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p class="text-green-800 font-semibold">Order placed successfully!</p>
                        <p class="text-sm text-green-700 mt-2" id="order-details"></p>
                    </div>
                </div>
            </div>

            <!-- Preview Panel -->
            <div class="bg-white rounded-2xl shadow-xl p-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Your Configuration</h2>

                <!-- Preview content -->
                <div class="bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl p-8 mb-6" style="min-height: 300px;">
                    <div class="flex items-center justify-center h-full">
                        <p class="text-gray-600">Product Preview</p>
                    </div>
                </div>

                <!-- Configuration summary -->
                <div class="space-y-4">
                    <div class="flex justify-between py-3 border-b">
                        <span class="text-gray-600">Detail 1:</span>
                        <span class="font-semibold" id="preview-detail-1">Value</span>
                    </div>
                </div>

                <!-- Factory Info -->
                <div class="mt-8 p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                    <h3 class="font-semibold text-indigo-900 mb-2">Factory Information</h3>
                    <div class="text-sm text-indigo-700 space-y-1">
                        <p>Factory ID: your-factory-001</p>
                        <p>Workflow: <span id="preview-workflow">your-workflow-id</span></p>
                        <p>Status: <span class="text-green-600 font-semibold">● Online</span></p>
                    </div>
                </div>

                <a href="http://localhost:5001" target="_blank"
                   class="block w-full mt-6 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold text-center hover:bg-gray-200">
                    Monitor Production →
                </a>
            </div>
        </div>
    </div>

    <script>
        // Configuration
        const config = {
            apiUrl: 'http://localhost:5001',
            factoryId: 'your-factory-001',
            factoryType: 'your_type',
            mqttTopicPrefix: 'factory/your-factory-001',
            workflows: {
                standard: 'your-workflow-id'
            }
        };

        async function placeOrder() {
            const order = {
                product_name: `PRODUCT-${Date.now()}`,
                product_details: {
                    // Your product details
                    workflow_id: config.workflows.standard,
                    factory_id: config.factoryId
                }
            };

            try {
                const response = await fetch(`${config.apiUrl}/production`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(order)
                });

                if (response.ok) {
                    document.getElementById('order-status').classList.remove('hidden');
                    document.getElementById('order-details').textContent =
                        `Order ID: ${order.product_name} - Production started`;
                } else {
                    alert('Failed to place order');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error connecting to factory');
            }
        }
    </script>
</body>
</html>
```

#### 3. Configure for Your Factory

Update the `config` object:
```javascript
const config = {
    apiUrl: 'http://localhost:5001',           // API endpoint
    factoryId: 'electronics-factory-001',       // Your factory ID
    factoryType: 'electronics',
    mqttTopicPrefix: 'factory/electronics-factory-001',
    workflows: {
        smartphone: 'smartphone-pcb',           // From factory config
        iot: 'iot-sensor'
    }
};
```

---

### Method 2: Angular Frontend (Like tshirt-customizer)

#### 1. Clone tshirt-customizer as Template

```bash
cp -r tshirt-customizer electronics-customizer
cd electronics-customizer
```

#### 2. Update environment.ts

```typescript
// src/app/environments/environment.ts
export const environment = {
    production: false,
    apiUrl: 'http://localhost:5001',
    factoryId: 'electronics-factory-001',      // Your factory
    factoryType: 'electronics',
    mqttBroker: 'ws://localhost:39001',        // Your MQTT WS port
    mqttTopicPrefix: 'factory/electronics-factory-001',
    workflows: {
      smartphone: 'smartphone-pcb',             // From factory config
      iot: 'iot-sensor'
    }
};
```

#### 3. Update Component Template

Modify `src/app/product-selector/product-selector.component.html`:
```html
<!-- Replace t-shirt options with your product options -->
<div class="option-group">
    <label>Product Type</label>
    <select [(ngModel)]="productOptions.type">
        <option value="smartphone">Smartphone PCB</option>
        <option value="iot">IoT Sensor</option>
    </select>
</div>

<div class="option-group">
    <label>Specifications</label>
    <!-- Your product-specific options -->
</div>
```

#### 4. Update Component Logic

```typescript
// src/app/product-selector/product-selector.component.ts
placeOrder() {
    const order: OrderPayload = {
        product_name: this.generateProductName(),
        product_details: {
            type: this.productOptions.type,
            // Your product-specific fields
            workflow_id: environment.workflows[this.productOptions.type],
            factory_id: environment.factoryId
        }
    };

    this.apiService.placeOrder(order).subscribe({
        next: (response) => console.log('Order placed:', response),
        error: (error) => console.error('Error:', error)
    });
}
```

---

## 🏭 Factory-Specific Examples

### Electronics Factory Frontend

**Product Options:**
- PCB Type: Smartphone, IoT Sensor
- Component Quality: Standard, Premium
- Testing Level: Basic, Comprehensive

**Configuration:**
```javascript
{
    factoryId: 'electronics-factory-001',
    workflows: {
        smartphone: 'smartphone-pcb',
        iot: 'iot-sensor'
    },
    mqttPort: 39001
}
```

### Pharmaceutical Factory Frontend

**Product Options:**
- Tablet Type: Standard, Immediate Release
- Batch Size: 25000, 50000
- Coating: Standard, Premium
- Quality Grade: Pharmaceutical

**Configuration:**
```javascript
{
    factoryId: 'pharma-plant-001',
    workflows: {
        standard: 'standard-tablet',
        immediate: 'immediate-release-tablet'
    },
    mqttPort: 39001
}
```

### Food Processing Factory Frontend

**Product Options:**
- Product Type: Cookies, Bread
- Flavor: Chocolate Chip, Oatmeal, Sourdough
- Batch Size: Small, Medium, Large
- Packaging: Standard, Premium

**Configuration:**
```javascript
{
    factoryId: 'food-processing-plant-001',
    workflows: {
        cookies: 'cookie-production',
        bread: 'bread-production'
    },
    mqttPort: 39001
}
```

---

## 🔧 Common Features to Implement

### 1. Product Configuration
```javascript
// Always include
- Product type/variant selection
- Size/quantity options
- Color/flavor choices
- Custom features/add-ons
```

### 2. Preview Panel
```javascript
// Standard preview elements
- Visual representation (image/icon)
- Configuration summary
- Price calculation
- Estimated production time
- Factory status
```

### 3. Order Placement
```javascript
// Standard order payload
{
    product_name: "UNIQUE-ID",
    product_details: {
        // Your product fields
        workflow_id: "workflow-id-from-config",
        factory_id: "factory-id"
    }
}
```

### 4. Status Display
```javascript
// Show order confirmation
- Order ID
- Selected configuration
- Production status
- Link to monitoring dashboard
```

---

## 📊 API Integration

### Endpoints Used

```bash
# Place order
POST http://localhost:5001/production
Content-Type: application/json

{
  "product_name": "PRODUCT-123",
  "product_details": { ... }
}

# Get factory status
GET http://localhost:5001/machines

# Update configuration (optional)
PUT http://localhost:5001/production/config
```

### MQTT Integration (Optional)

```javascript
// For real-time updates
const client = mqtt.connect(config.mqttBroker);

client.subscribe(`${config.mqttTopicPrefix}/production/status`);

client.on('message', (topic, message) => {
    const data = JSON.parse(message.toString());
    // Update UI with production status
});
```

---

## 🎨 UI/UX Best Practices

### Design Consistency
- Use Tailwind CSS for consistent styling
- Follow the 2-column layout pattern
- Gradient backgrounds for modern look
- Card-based components with shadows

### User Experience
- Clear product selection
- Visual feedback (checkmarks, highlights)
- Real-time price updates
- Order confirmation messages
- Link to production monitoring

### Responsive Design
```css
/* Use Tailwind responsive classes */
grid-cols-1 lg:grid-cols-2  /* Mobile: 1 col, Desktop: 2 cols */
px-4 sm:px-6 lg:px-8       /* Responsive padding */
```

---

## ✅ Checklist for New Frontend

- [ ] Choose technology stack
- [ ] Identify target factory
- [ ] Read factory configuration
- [ ] List product options/workflows
- [ ] Create directory structure
- [ ] Copy template (tshirt or vehicle)
- [ ] Update configuration
- [ ] Customize product options
- [ ] Update preview panel
- [ ] Implement order placement
- [ ] Add factory information
- [ ] Test with running factory
- [ ] Document usage

---

## 🧪 Testing Your Frontend

### 1. Start Factory
```bash
cd generated-factories/your-factory-001
docker compose up --build
```

### 2. Start API
```bash
cd simple_factory_simulator
export MQTT_PORT=31883  # Your factory's MQTT port
export MQTT_WS_PORT=39001
python3 app.py
```

### 3. Open Frontend
```bash
# HTML: Open in browser
open your-customizer/src/index.html

# Angular: Run dev server
cd your-customizer
ng serve
```

### 4. Test Order Flow
1. Configure product
2. Place order
3. Check console for API response
4. Monitor MQTT topics
5. Verify in dashboard

---

## 📚 Resources

### Templates
- **[tshirt-customizer/](tshirt-customizer/)** - Angular template
- **[vehicle-customizer/](vehicle-customizer/)** - HTML/JS template

### Documentation
- **[Factory Configs](factory-configs/)** - All factory configurations
- **[MIGRATION_TO_JSON_BASED.md](MIGRATION_TO_JSON_BASED.md)** - Platform overview
- **[simple_factory_simulator/README.md](simple_factory_simulator/README.md)** - API documentation

### Tools
- **Tailwind CSS:** https://tailwindcss.com/docs
- **Fetch API:** https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- **MQTT.js:** https://github.com/mqttjs/MQTT.js

---

## 🚀 Next Steps

1. **Pick a factory type** you want to create a frontend for
2. **Copy the vehicle-customizer** as a starting template
3. **Customize** the product options for your factory
4. **Test** with the generated factory
5. **Share** your frontend with the community!

---

## 💡 Pro Tips

1. **Start Simple** - Begin with HTML/JS, upgrade to framework later
2. **Reuse Components** - Copy working parts from existing frontends
3. **Follow the Pattern** - Configuration panel + Preview panel
4. **Test Often** - Run factory and API while developing
5. **Document** - Add README with factory ID and workflows

---

**Ready to create your own frontend? Start with the vehicle-customizer template and customize it for your factory!**

🎉 **You now have everything you need to build customer-facing apps for ANY factory type!**
