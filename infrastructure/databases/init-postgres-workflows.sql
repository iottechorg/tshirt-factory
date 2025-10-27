-- PostgreSQL Schema Extension for Workflows

-- Workflow definitions table
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id VARCHAR(100) PRIMARY KEY,
    workflow_name VARCHAR(200) NOT NULL,
    description TEXT,
    product_type VARCHAR(100) NOT NULL,
    workflow_definition JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create index on product_type for faster lookups
CREATE INDEX IF NOT EXISTS idx_workflows_product_type ON workflows(product_type);
CREATE INDEX IF NOT EXISTS idx_workflows_active ON workflows(is_active);

-- Update production_orders table to include workflow reference
ALTER TABLE production_orders
    ADD COLUMN IF NOT EXISTS workflow_id VARCHAR(100) REFERENCES workflows(workflow_id),
    ADD COLUMN IF NOT EXISTS workflow_state JSONB DEFAULT '{}'::jsonb;

-- Update production_steps to include more workflow details
ALTER TABLE production_steps
    ADD COLUMN IF NOT EXISTS step_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS operation VARCHAR(100),
    ADD COLUMN IF NOT EXISTS outputs JSONB;

-- Machine registry for dynamic machine discovery
CREATE TABLE IF NOT EXISTS machine_registry (
    machine_id VARCHAR(100) PRIMARY KEY,
    machine_type VARCHAR(50) NOT NULL,
    machine_name VARCHAR(100),
    status VARCHAR(50) DEFAULT 'available',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    capabilities JSONB DEFAULT '{}'::jsonb,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_machine_registry_type ON machine_registry(machine_type);
CREATE INDEX IF NOT EXISTS idx_machine_registry_status ON machine_registry(status);

-- Workflow execution metrics
CREATE TABLE IF NOT EXISTS workflow_metrics (
    metric_id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(100) REFERENCES workflows(workflow_id),
    order_id VARCHAR(100) REFERENCES production_orders(order_id),
    execution_time_seconds INTEGER,
    total_steps INTEGER,
    successful_steps INTEGER,
    failed_steps INTEGER,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflow_metrics_workflow ON workflow_metrics(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_metrics_executed ON workflow_metrics(executed_at DESC);

-- Insert default workflows
INSERT INTO workflows (workflow_id, workflow_name, description, product_type, workflow_definition, metadata) VALUES
(
    'workflow-tshirt-standard',
    'Standard T-Shirt Production',
    'Complete t-shirt production: cutting, sewing, ironing, printing',
    'tshirt',
    '{"steps": [
        {"step_id": "step-1", "machine_type": "cutting", "operation": "cut_fabric", "required_inputs": ["material", "cut_size"], "outputs": ["cut_fabric"]},
        {"step_id": "step-2", "machine_type": "sewing", "operation": "sew_pieces", "required_inputs": ["cut_fabric", "stitch_type", "thread_color"], "outputs": ["sewn_garment"]},
        {"step_id": "step-3", "machine_type": "ironing", "operation": "iron_garment", "required_inputs": ["sewn_garment", "iron_temperature_setpoint", "steam_level"], "outputs": ["ironed_garment"]},
        {"step_id": "step-4", "machine_type": "printing", "operation": "print_design", "required_inputs": ["ironed_garment", "ink_type"], "outputs": ["finished_product"]}
    ]}',
    '{"estimated_time_minutes": 20, "complexity": "standard"}'::jsonb
),
(
    'workflow-quick-patch',
    'Quick Patch Production',
    'Fast production for simple patches - cutting and printing only',
    'patch',
    '{"steps": [
        {"step_id": "step-1", "machine_type": "cutting", "operation": "cut_patch", "required_inputs": ["material", "cut_size"], "outputs": ["cut_patch"]},
        {"step_id": "step-2", "machine_type": "printing", "operation": "print_patch", "required_inputs": ["cut_patch", "ink_type"], "outputs": ["finished_patch"]}
    ]}',
    '{"estimated_time_minutes": 10, "complexity": "simple", "fast_track": true}'::jsonb
)
ON CONFLICT (workflow_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO factory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO factory_user;
