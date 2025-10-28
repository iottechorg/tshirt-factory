# Vehicle Customizer Frontend

## Customer-Facing Interface for Automotive Factory

A modern, responsive web application for ordering custom vehicles from the automotive assembly plant.

---

## 🎯 Purpose

This frontend allows customers to:
- Configure vehicle specifications (type, color, features)
- Place orders directly to the automotive factory
- Monitor production status
- View real-time factory information

---

## 🏭 Connected Factory

**Factory:** `automotive-plant-001` (Generated from `factory-configs/automotive-assembly-plant.json`)

**Workflows Supported:**
- `sedan-production` - Standard sedan assembly
- `suv-production` - SUV assembly

---

## 🚀 Quick Start

### 1. Start the Automotive Factory

```bash
# Generate factory (if not already done)
python3 tools/factory_generator.py factory-configs/automotive-assembly-plant.json

# Start factory services
cd generated-factories/automotive-plant-001
docker compose up --build
```

### 2. Start simple_factory_simulator (API)

```bash
cd simple_factory_simulator

# Configure for automotive factory
export MQTT_BROKER=localhost
export MQTT_PORT=31883
export MQTT_WS_PORT=39001

# Start API
python3 app.py
```

### 3. Open Vehicle Customizer

```bash
# Option 1: Open directly in browser
open vehicle-customizer/src/index.html

# Option 2: Serve with simple HTTP server
cd vehicle-customizer/src
python3 -m http.server 8080
# Then open: http://localhost:8080
```

---

## 🎨 Features

### Vehicle Configuration
- **Type Selection:** Sedan or SUV
- **Color Selection:** 8 colors (Black, White, Red, Blue, Silver, Gray, Green, Yellow)
- **Features:**
  - Panoramic Sunroof ($2,000)
  - Leather Interior ($3,000)
  - GPS Navigation (Standard)
  - Premium Sound System ($1,500)

### Real-Time Preview
- Selected configuration summary
- Dynamic price calculation
- Estimated production time
- Factory status indicator

### Order Placement
- Direct API integration with factory
- Real-time order confirmation
- Production monitoring link

---

## 🔧 Configuration

Edit configuration in `index.html`:

```javascript
const config = {
    apiUrl: 'http://localhost:5001',        // API endpoint
    factoryId: 'automotive-plant-001',      // Target factory
    factoryType: 'automotive',
    mqttTopicPrefix: 'factory/automotive-plant-001',
    workflows: {
        sedan: 'sedan-production',
        suv: 'suv-production'
    }
};
```

---

## 📊 API Integration

### Place Order Endpoint

```javascript
POST http://localhost:5001/production

Body:
{
  "product_name": "SEDAN-1730123456789",
  "product_details": {
    "vehicle_type": "sedan",
    "color": "black",
    "features": {
      "sunroof": true,
      "leather": false,
      "navigation": true,
      "premium_sound": true
    },
    "workflow_id": "sedan-production",
    "factory_id": "automotive-plant-001"
  }
}
```

### Response

```json
{
  "message": "Production request added to queue"
}
```

---

## 🎨 Design Features

- **Modern Tailwind CSS** - Utility-first styling
- **Gradient Backgrounds** - Professional appearance
- **Responsive Layout** - Works on all devices
- **Interactive Elements** - Hover effects and transitions
- **Visual Feedback** - Checkmarks and status indicators

---

## 🔄 Based on tshirt-customizer Pattern

This frontend follows the same pattern as `tshirt-customizer`:

```
Frontend Structure:
├── Configuration Panel (Left)
│   ├── Product selection
│   ├── Options/Features
│   └── Place Order button
│
└── Preview Panel (Right)
    ├── Visual preview
    ├── Configuration summary
    ├── Price calculation
    └── Factory information
```

---

## 🚀 Extending to Other Factories

This same pattern can be replicated for:

- **Electronics Customizer** → `electronics-factory-001`
- **Pharmaceutical Portal** → `pharma-plant-001`
- **Food Ordering** → `food-processing-plant-001`

See [FRONTEND_REPLICATION_GUIDE.md](../FRONTEND_REPLICATION_GUIDE.md) for step-by-step instructions.

---

## 📦 Dependencies

- **Tailwind CSS** (CDN) - Styling
- **Vanilla JavaScript** - No framework required
- **Fetch API** - HTTP requests

**No build step required!** Pure HTML/CSS/JavaScript.

---

## 🧪 Testing

### Test Order Flow

1. Open `vehicle-customizer/src/index.html`
2. Configure vehicle (type, color, features)
3. Click "Place Order"
4. Check order status message
5. Click "Monitor Production" to view in dashboard

### Verify Factory Integration

```bash
# Monitor MQTT messages
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Check production queue
curl http://localhost:5001/production
```

---

## 🎯 Future Enhancements

- [ ] 3D vehicle preview
- [ ] Real-time production status updates via MQTT
- [ ] Order history
- [ ] Multiple vehicle models
- [ ] Price breakdown
- [ ] Delivery date calculator
- [ ] Customer authentication
- [ ] Payment integration

---

## 📚 Related Documentation

- **[../tshirt-customizer/](../tshirt-customizer/)** - Original pattern implementation
- **[FRONTEND_REPLICATION_GUIDE.md](../FRONTEND_REPLICATION_GUIDE.md)** - How to create similar frontends
- **[MIGRATION_TO_JSON_BASED.md](../MIGRATION_TO_JSON_BASED.md)** - Platform overview

---

**Version 1.0** - Vehicle Customizer for Automotive Factory
