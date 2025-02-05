# Factory Simulator

## Components

### 1. `config.py`

*   **Purpose:** Stores project configuration settings.
*   **Key Settings:** MQTT broker details, topics, default success rate, and machine names.

### 2. `machine.py`

*   **Purpose:** Defines the `Machine` class, representing a single factory machine.
*   **Key Attributes:** Machine ID, name, state, sensor data, and failure rate.
*   **Key Methods:** Simulates operation, updates sensors, and returns JSON data.

### 3. `mqtt_publisher.py`

*   **Purpose:** Handles MQTT communication with a broker.
*   **Key Methods:** Connects, publishes messages, and manages the MQTT client.

### 4. `production.py`

*   **Purpose:** Manages the production workflow and steps.
*   **Key Attributes:** Production steps, status, failure rate, and a production queue.
*   **Key Methods:** Enqueues requests, executes production steps, and publishes results.

### 5. `utils.py`

*   **Purpose:** Contains helper functions.
*   **Key Functions:** Fetches machines by ID, generates random data for products and tests, and generates consistent API response.

### 6. `managers.py`
  
* **Purpose:** Main application, setting up REST API endpoints and managing the simulator.
*   **Key Classes:**
    *   `MachineManager`: Manages machines and their data publishing.
    *   `ProductionManager`: Manages production processes.
*   **Key Routes:** REST API endpoints for managing machines, production, and tests.

### 6. `app.py`

*   **Purpose:** Main application, setting up REST API endpoints and managing the simulator.
*   **Key Routes:** REST API endpoints for managing machines, production, and tests.

### 7. `web_app/`

*   **Purpose:** Front-end web application files.
    *   `index.html`: Main HTML page with the UI.
    *   `style.css`: CSS for the UI.
    *   `script.js`: JavaScript with jQuery for REST and MQTT interactions.
    *   `test_cases.json`: JSON file defining the different test cases.

### 8. `Dockerfile`

*   **Purpose:** Instructions to build the Docker image.
*   **Key Directives:** Sets the base image, installs requirements, and starts the application.

### 9. `docker-compose.yml`

*   **Purpose:**  Defines setup for running the app in Docker.
*   **Key Sections:** Lists the docker services and docker image configuration.

## Execution

### Prerequisites

*   **Python 3.9+**
*   **Docker and Docker Compose**

### Steps

1.  **Clone the repository:**

    After clonning the repository, if your OS is ubuntu 2204, you can run `run_on_ubuntu_2204.sh` script, which will install the required docker compose libraries and start the project. If your development environment has already the docker setup, you can skip this step.

2.  **Run with Docker Compose:**
    ```bash
    sudo docker compose up --build -d
    ```

3.  **Access the Web App:**
    *   Open your web browser and go to `http://localhost:5001`.

## Functionality

### Machine Management

*   **View:** Displays machine status and sensor data in a table.
*   **Update:** Changes machine failure rates and sensor values by selecting the machine.

### Production Management

*   **Request:** Starts new production jobs with JSON data.
*   **Config:** Configures production failure rates.
*   **Random Production:** Allows continous generation of random production requests
*  **Results:** Displays the latest 10 production results in a table.

### Test Cases

*   **Run Tests:** Runs predefined and random test cases.

### Real-Time Monitoring

*   **MQTT:** Publishes real-time machine and production data via MQTT.

### Web Application Notes

*  **Dynamic Data:** Uses jQuery and AJAX to interact with the backend.
*  **MQTT:** Receives the production result in real time using paho mqtt javascript.
*  **Random Product Data:** Provides random generation of product data.
*   **Clean UI:** Provides specific buttons for clearing the console and production output.

## API Endpoints

*   **GET `/machines`**: Returns all machines and their states.
*   **PUT `/machines/<machine_id>`**: Updates a machine's failure rate.
*   **PUT `/machines/sensor/<machine_id>/<sensor_name>`**: Updates a machine's sensor value.
*   **POST `/production`**: Starts a new production process.
*   **PUT `/production/config`**: Updates the production success rate.
*   **POST `/test/<test_case>`**: Runs defined test cases.
*   **GET `/test_cases.json`**: Returns the test cases configurations.
*   **GET `/`**: Serves the frontend.

## Environment Variables
The following environment variables can be specified in `docker-compose.yml`:

*  **`MQTT_BROKER`**: Set the address for MQTT broker default is `broker.emqx.io`
*   **`MQTT_PORT`**: Set the port for MQTT default is `8083`
*   **`API_BASE_URL`**: Set the base url of rest api, default value is `http://localhost:5001`


## Issues
- Replace Development Web server with Production Server
  - Code restructuring is needed if gunicorn is the candidate. The MQTT and websocket connections fail.
  - Try flask_mqtt as an alternative to paho https://flask-mqtt.readthedocs.io/en/latest/usage.html#configure-the-mqtt-client
