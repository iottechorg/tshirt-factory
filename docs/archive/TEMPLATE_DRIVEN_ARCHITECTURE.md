# Template-Driven Architecture - Complete Refactoring

## Problem Statement

The original codebase had hardcoded T-shirt factory assumptions throughout:
- `production_automation.py`: Hardcoded materials = ["cotton", "polyester"], sizes = ["XS", "S", "M"]
- Both `test_case_generator.py` files: Searched for sensors by name ("temperature", "pressure"), generated hardcoded condition types ("high_temperature", "low_pressure")
- Not truly factory-agnostic despite claims

## Solution: Pure Template-Driven Architecture

### Core Principle
**Everything is derived from JSON schemas and template files. Zero hardcoded assumptions.**

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Factory Definition Files                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  factory-config-schema.json  ←  Defines factory structure   │
│  machine-template-schema.json ← Defines machine structure   │
│                                                               │
│  factory-configs/*.json       ←  Factory instances          │
│  machine-templates/*.json     ←  Machine type definitions   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Template-Driven Generators                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  TemplateDrivenTestGenerator  ←  Reads templates            │
│    • Loads all machine templates                             │
│    • Extracts sensors with min/max ranges                    │
│    • Generates test cases for each sensor extreme            │
│    • Zero hardcoded sensor names                             │
│                                                               │
│  ProductionAutomation         ←  Reads workflows             │
│    • Extracts parameters from workflow steps                 │
│    • Generates random production requests                    │
│    • Factory-specific product details                        │
│                                                               │
│  AutomationConfigGenerator    ←  Reads workflows             │
│    • Extracts all workflow parameters                        │
│    • Returns generic parameter dictionaries                  │
│    • Used by production automation                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified/Created

### 1. **shared/template_driven_test_generator.py** [NEW]
**Purpose**: Generate test cases purely from machine template specifications

**Key Features**:
- Loads all machine templates from `machine-templates/` directory
- Extracts sensor specifications (name, min, max, unit)
- Generates test cases:
  - Normal operation: 1 test with production request
  - Sensor extremes: 2 tests per sensor (min + max value)
  - Production tests: Random production requests
- **Zero hardcoded sensor names** - discovers sensors from templates
- Works with ANY factory type

... (archived original content)
