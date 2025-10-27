-- PostgreSQL Initialization Script for Factory Database

-- Create database user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE usename = 'factory_user'
   ) THEN
      CREATE USER factory_user WITH PASSWORD 'factory_pass';
   END IF;
END
$do$;

-- Create main database
CREATE DATABASE IF NOT EXISTS factory_db;
GRANT ALL PRIVILEGES ON DATABASE factory_db TO factory_user;

-- Connect to the database
\c factory_db;

-- Machines table
CREATE TABLE IF NOT EXISTS machines (
    machine_id VARCHAR(100) PRIMARY KEY,
    machine_type VARCHAR(50) NOT NULL,
    machine_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Production orders table
CREATE TABLE IF NOT EXISTS production_orders (
    order_id VARCHAR(100) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    product_details JSONB,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Production steps table
CREATE TABLE IF NOT EXISTS production_steps (
    step_id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) REFERENCES production_orders(order_id),
    step_name VARCHAR(50) NOT NULL,
    machine_id VARCHAR(100) REFERENCES machines(machine_id),
    status VARCHAR(50) NOT NULL,
    process_data JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Machine status log table
CREATE TABLE IF NOT EXISTS machine_status_log (
    log_id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100) REFERENCES machines(machine_id),
    runtime_state VARCHAR(50) NOT NULL,
    total_operations INTEGER,
    failed_operations INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_status ON production_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON production_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_steps_order ON production_steps(order_id);
CREATE INDEX IF NOT EXISTS idx_status_log_machine ON machine_status_log(machine_id, timestamp DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO factory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO factory_user;

-- Insert sample machines
INSERT INTO machines (machine_id, machine_type, machine_name) VALUES
    ('cutting-01', 'cutting', 'Cutting Machine 01'),
    ('sewing-01', 'sewing', 'Sewing Machine 01'),
    ('ironing-01', 'ironing', 'Ironing Machine 01'),
    ('printing-01', 'printing', 'Printing Machine 01')
ON CONFLICT (machine_id) DO NOTHING;
