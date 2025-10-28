"""
Base Machine class for all factory machines
"""
import json
import random
import time
import logging
from typing import Dict, Optional
from abc import ABC, abstractmethod
from uuid import uuid4

logger = logging.getLogger(__name__)


class BaseMachine(ABC):
    """Abstract base class for all factory machines"""

    def __init__(self, machine_id: str, machine_type: str, machine_name: str):
        self.machine_id = machine_id
        self.machine_type = machine_type
        self.machine_name = machine_name
        self.is_running = False
        self.runtime_state = "idle"  # idle, busy, error, maintenance
        self.process_data = {}
        self.sensor_data = self._initialize_sensors()
        self.failure_rate = 0.01
        self.total_operations = 0
        self.failed_operations = 0
        self.uptime_seconds = 0
        self.last_maintenance = time.time()

    @abstractmethod
    def _initialize_sensors(self) -> Dict:
        """Initialize machine-specific sensors - must be implemented by subclasses"""
        pass

    @abstractmethod
    def update_sensors(self):
        """Update sensor values - must be implemented by subclasses"""
        pass

    @abstractmethod
    def validate_process_data(self, process_data: Dict) -> bool:
        """Validate process data for this machine type"""
        pass

    def get_status(self) -> Dict:
        """Get current machine status"""
        return {
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "machine_name": self.machine_name,
            "runtime_state": self.runtime_state,
            "is_running": self.is_running,
            "failure_rate": self.failure_rate,
            "total_operations": self.total_operations,
            "failed_operations": self.failed_operations,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": time.time()
        }

    def get_telemetry(self) -> Dict:
        """Get current telemetry data (sensors + process data)"""
        return {
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "sensor_data": self.sensor_data,
            "process_data": self.process_data,
            "runtime_state": self.runtime_state,
            "timestamp": time.time()
        }

    def update_sensor_value(self, sensor_name: str, value: float) -> bool:
        """Update a specific sensor value"""
        if sensor_name in self.sensor_data:
            try:
                self.sensor_data[sensor_name] = float(value)
                logger.info(f"[{self.machine_id}] Updated sensor '{sensor_name}' to {value}")
                return True
            except ValueError:
                logger.error(f"[{self.machine_id}] Invalid value for sensor '{sensor_name}': {value}")
                return False
        else:
            logger.warning(f"[{self.machine_id}] Sensor '{sensor_name}' not found")
            return False

    def set_process_data(self, process_data: Dict):
        """Set process data for the current operation"""
        if self.validate_process_data(process_data):
            self.process_data = process_data
            logger.info(f"[{self.machine_id}] Process data set: {process_data}")
        else:
            logger.error(f"[{self.machine_id}] Invalid process data: {process_data}")
            raise ValueError(f"Invalid process data for {self.machine_type}")

    def process_operation(self, process_data: Dict, processing_time: int = None) -> Dict:
        """
        Process an operation with the given data
        Returns: dict with status and result
        """
        try:
            self.set_process_data(process_data)
            self.runtime_state = "busy"
            self.total_operations += 1

            # Simulate processing time
            if processing_time is None:
                processing_time = random.randint(4, 7)

            logger.info(f"[{self.machine_id}] Starting operation (estimated time: {processing_time}s)")
            time.sleep(processing_time)

            # Simulate potential failure
            random_value = random.uniform(0, 1)
            if random_value < self.failure_rate:
                self.failed_operations += 1
                self.runtime_state = "error"
                logger.warning(f"[{self.machine_id}] Operation failed!")
                return {
                    "status": "failed",
                    "machine_id": self.machine_id,
                    "machine_type": self.machine_type,
                    "process_data": self.process_data,
                    "error": "Operation failed due to machine error",
                    "timestamp": time.time()
                }
            else:
                self.runtime_state = "idle"
                logger.info(f"[{self.machine_id}] Operation completed successfully")
                return {
                    "status": "success",
                    "machine_id": self.machine_id,
                    "machine_type": self.machine_type,
                    "process_data": self.process_data,
                    "timestamp": time.time()
                }

        except Exception as e:
            self.failed_operations += 1
            self.runtime_state = "error"
            logger.error(f"[{self.machine_id}] Error during operation: {e}")
            return {
                "status": "failed",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type,
                "error": str(e),
                "timestamp": time.time()
            }

    def set_failure_rate(self, rate: float):
        """Update the machine's failure rate"""
        if 0 <= rate <= 1:
            self.failure_rate = rate
            logger.info(f"[{self.machine_id}] Failure rate set to {rate}")
        else:
            logger.error(f"[{self.machine_id}] Invalid failure rate: {rate}")

    def start(self):
        """Start the machine"""
        self.is_running = True
        self.runtime_state = "idle"
        logger.info(f"[{self.machine_id}] Machine started")

    def stop(self):
        """Stop the machine"""
        self.is_running = False
        self.runtime_state = "idle"
        logger.info(f"[{self.machine_id}] Machine stopped")

    def to_json(self) -> str:
        """Convert machine state to JSON"""
        return json.dumps({
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "machine_name": self.machine_name,
            "is_running": self.is_running,
            "runtime_state": self.runtime_state,
            "process_data": self.process_data,
            "sensor_data": self.sensor_data,
            "failure_rate": self.failure_rate,
            "total_operations": self.total_operations,
            "failed_operations": self.failed_operations
        })
