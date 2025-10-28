"""
Database models and connection utilities
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from contextlib import contextmanager
from typing import Optional, Dict, List
import json
import time

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """PostgreSQL database connection manager"""

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self, retry_count: int = 5, retry_delay: int = 5):
        """Connect to database with retry logic"""
        for attempt in range(retry_count):
            try:
                logger.info(f"Attempting to connect to database (attempt {attempt + 1}/{retry_count})")
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                logger.info("Successfully connected to database")
                return True
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        logger.error(f"Failed to connect to database after {retry_count} attempts")
        return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    @contextmanager
    def get_cursor(self):
        """Get a database cursor using context manager"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def initialize_schema(self):
        """Initialize database schema"""
        with self.get_cursor() as cursor:
            # Machines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    machine_id VARCHAR(100) PRIMARY KEY,
                    machine_type VARCHAR(50) NOT NULL,
                    machine_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Production orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS production_orders (
                    order_id VARCHAR(100) PRIMARY KEY,
                    product_name VARCHAR(200) NOT NULL,
                    product_details JSONB,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # Production steps table
            cursor.execute("""
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
                )
            """)

            # Machine status log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS machine_status_log (
                    log_id SERIAL PRIMARY KEY,
                    machine_id VARCHAR(100) REFERENCES machines(machine_id),
                    runtime_state VARCHAR(50) NOT NULL,
                    total_operations INTEGER,
                    failed_operations INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            logger.info("Database schema initialized")


class TimeSeriesConnection:
    """TimescaleDB connection for sensor data"""

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self, retry_count: int = 5, retry_delay: int = 5):
        """Connect to TimescaleDB with retry logic"""
        for attempt in range(retry_count):
            try:
                logger.info(f"Attempting to connect to TimescaleDB (attempt {attempt + 1}/{retry_count})")
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                logger.info("Successfully connected to TimescaleDB")
                return True
            except Exception as e:
                logger.error(f"TimescaleDB connection attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        logger.error(f"Failed to connect to TimescaleDB after {retry_count} attempts")
        return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("TimescaleDB connection closed")

    @contextmanager
    def get_cursor(self):
        """Get a database cursor using context manager"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"TimescaleDB error: {e}")
            raise
        finally:
            cursor.close()

    def initialize_schema(self):
        """Initialize TimescaleDB schema with hypertables"""
        with self.get_cursor() as cursor:
            # Create TimescaleDB extension if not exists
            cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

            # Sensor telemetry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_telemetry (
                    time TIMESTAMPTZ NOT NULL,
                    machine_id VARCHAR(100) NOT NULL,
                    machine_type VARCHAR(50) NOT NULL,
                    sensor_name VARCHAR(100) NOT NULL,
                    sensor_value DOUBLE PRECISION NOT NULL,
                    runtime_state VARCHAR(50)
                )
            """)

            # Convert to hypertable if not already
            try:
                cursor.execute("""
                    SELECT create_hypertable('sensor_telemetry', 'time',
                                             if_not_exists => TRUE)
                """)
            except Exception as e:
                logger.warning(f"Hypertable creation skipped: {e}")

            # Create index for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_machine_time
                ON sensor_telemetry (machine_id, time DESC)
            """)

            logger.info("TimescaleDB schema initialized")

    def insert_sensor_data(self, machine_id: str, machine_type: str,
                          sensor_data: Dict, runtime_state: str):
        """Insert sensor telemetry data"""
        with self.get_cursor() as cursor:
            for sensor_name, sensor_value in sensor_data.items():
                cursor.execute("""
                    INSERT INTO sensor_telemetry
                    (time, machine_id, machine_type, sensor_name, sensor_value, runtime_state)
                    VALUES (NOW(), %s, %s, %s, %s, %s)
                """, (machine_id, machine_type, sensor_name, sensor_value, runtime_state))
