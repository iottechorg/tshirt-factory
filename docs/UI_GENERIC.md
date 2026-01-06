# Generic UI usage

This document explains how the generic `customer-order-ui` and `factory_ui_simulator` work with generated factories.

1. Generate a factory:

```bash
python3 tools/factory_generator.py factory-configs/tshirt-factory.json
cd generated-factories/tshirt-factory-001
docker compose up --build
```

2. Start API / simulator (in another terminal):

```bash
cd factory_ui_simulator
python3 app.py
```

3. Start the frontend (Angular dev server):

```bash
cd customer-order-ui
npm install
npm start  # or `ng serve`
```

4. The generator publishes `factory-config.json` to MQTT as a retained message on topic `factory/{factory-id}/config`.

- `factory_ui_simulator` subscribes and applies workflows and exposes `/factory-config` and `/factory-config/generated/{factory-id}` endpoints.
- `customer-order-ui` fetches `/factory-config` and displays the machines list.
- Monitoring and orchestrator subscribe to the same MQTT config topic and update their runtime state.

Hot reload: updating the generated factory config will be republished and services will pick up changes automatically.
