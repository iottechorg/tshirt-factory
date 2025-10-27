-- TimescaleDB Initialization Script for Sensor Data

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

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

-- Sensor telemetry table
CREATE TABLE IF NOT EXISTS sensor_telemetry (
    time TIMESTAMPTZ NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    machine_type VARCHAR(50) NOT NULL,
    sensor_name VARCHAR(100) NOT NULL,
    sensor_value DOUBLE PRECISION NOT NULL,
    runtime_state VARCHAR(50)
);

-- Convert to hypertable
SELECT create_hypertable('sensor_telemetry', 'time', if_not_exists => TRUE);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_sensor_machine_time
    ON sensor_telemetry (machine_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_type_time
    ON sensor_telemetry (machine_type, time DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_name_time
    ON sensor_telemetry (sensor_name, time DESC);

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    machine_id,
    machine_type,
    sensor_name,
    AVG(sensor_value) as avg_value,
    MIN(sensor_value) as min_value,
    MAX(sensor_value) as max_value,
    COUNT(*) as sample_count
FROM sensor_telemetry
GROUP BY bucket, machine_id, machine_type, sensor_name
WITH NO DATA;

-- Refresh policy for continuous aggregate (refresh every hour)
SELECT add_continuous_aggregate_policy('sensor_telemetry_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Data retention policy (keep raw data for 30 days)
SELECT add_retention_policy('sensor_telemetry',
    INTERVAL '30 days',
    if_not_exists => TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO factory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO factory_user;
