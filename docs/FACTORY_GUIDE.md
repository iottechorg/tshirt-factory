# Factory Guide

This guide consolidates the essential steps and reference material for creating and defining factories.

## Quick Links
- Step-by-step generation & run: `docs/HOW_TO_USE.md`
- Technical reference for JSON: `docs/EXTENDING.md`
- Examples: `factory-configs/`, `machine-templates/`, `workflows/`

## 1 — Plan
- Choose machine types from `machine-templates/` or create new templates.
- Define workflows in `workflows/` (stages, routing on pass/fail).
- Decide production parameters (orders/hour, shift length, default success rates).

## 2 — Create or reuse machine templates
- Add `machine-templates/my-machine.json` following `schemas/machine-template-schema.json`.
- Include `sensors` with `min`, `max`, `unit`, and `update_frequency`.

## 3 — Create factory config
- Copy a template:

```bash
cp factory-configs/tshirt-factory.json factory-configs/my-factory.json
```
- Edit fields: `factory_id`, `factory_name`, `machines` (id, template, count), `workflows`, and `production_config`.
- Validate JSON:

```bash
python3 -m json.tool factory-configs/my-factory.json > /dev/null && echo "✓ Valid"
```

## 4 — Generate

```bash
python3 tools/factory_generator.py factory-configs/my-factory.json
```

This produces `generated-factories/{factory-id}/` with a Docker Compose stack and service code.

## 5 — Run

```bash
cd generated-factories/my-factory-001
docker compose up --build
```

## 6 — Validate & Monitor
- Check logs: `docker compose logs -f`
- MQTT topics: `mosquitto_sub -h localhost -t 'factory/#' -v`
- REST API (factory UI simulator): `GET /machines`, `POST /production`

## Best Practices
- Keep machine templates minimal and schema-compliant.
- Use template-driven sensor ranges so test generation covers extremes.
- Reuse workflows where possible and parameterize product details in factory config.

## Where to go next
- Customize behavior: `docs/EXTENDING.md`
- Understand architecture: `docs/ARCHITECTURE.md`
- One-page cheatsheet: `docs/QUICK_REFERENCE.md`
