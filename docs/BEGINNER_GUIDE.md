**Project Overview**

This repository implements a simulated smart T‑shirt factory with microservices, an orchestrator, machine simulators, and a web-based customizer. The project is arranged so beginners can get the full system running locally with Docker, or run individual components for development.

**Quick Purpose**: run an end-to-end factory simulation to test production workflows, explore microservices, and try the frontend customizer.

**Prerequisites**
- **Docker & Docker Compose**: required to run the full stack via `docker-compose`.
- **Python 3.8+**: needed to run individual Python services or the `simple_factory_simulator` locally.
- **Node.js (optional)**: needed only if you want to run the Angular frontend locally rather than via Docker.

**Quick Start (recommended)**
- Clone the repository and change into it:

```bash
git clone <repo-url>
cd tshirt-factory
```

- Start the full stack using the top-level Docker Compose file:

```bash
docker-compose up --build
```

- Verify services:

```bash
docker-compose ps
docker-compose logs -f
```

- Helpful checks:
  - MQTT broker in this workspace is exposed on port `31883` (used by services to exchange messages).
  - Use `docker-compose logs <service>` to check a particular service (for example `docker-compose logs production-orchestrator`).

**Run only the simulator or a single service**
- To run the lightweight web simulator or to develop machine logic locally, go to the `simple_factory_simulator` folder. It contains a `docker-compose.yml` and a Python app.

```bash
cd simple_factory_simulator
# Option A: Docker
docker-compose up --build

# Option B: local Python (install requirements first)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

- To run a single microservice for development, enter the service folder under `services/machines/<machine>` and run its `machine_service.py` (or use the service `Dockerfile` via Compose).

**Frontend / Customizer**
- The T‑shirt customizer is in `tshirt-customizer/` (Angular). It can be run via Docker Compose (if the top-level Compose defines a `frontend` service) or locally using `npm install` + `ng serve`. If you prefer Docker, the top-level `docker-compose.yml` normally provides everything needed.

**Workflows**
- Production workflows are stored as JSON in the `workflows/` folder (for example `tshirt-standard.json`, `complete-production-chain.json`). These define sequences of machine tasks the orchestrator can run.
- The orchestrator service is implemented in `services/production-orchestrator/` (`orchestrator.py`, `workflow_manager.py`). For quick orchestration scenarios consult `docs/QUICKSTART_ORCHESTRATOR.md`.

**Databases & MQTT**
- Database initialization scripts are under `infrastructure/databases/`.
- MQTT config used by the project is in `mqtt/mosquitto.conf`. When running with Docker Compose the MQTT service is configured in the Compose files; by default the workspace uses port `31883` for MQTT (check your `docker-compose` or `docker-compose.override.yml` if present).

**Troubleshooting**
- If a service won't start, check logs: `docker-compose logs -f <service>`.
- Check container status: `docker ps` / `docker inspect <container>`.
- If MQTT is unreachable, confirm the broker container is running and listening on the expected port (31883 in this workspace).

**Where to find more detail**
- Orchestrator quickstart: `docs/QUICKSTART_ORCHESTRATOR.md`.
- Microservices design: `docs/MICROSERVICES_README.md`.
- Orchestrator architecture: `docs/ORCHESTRATOR_README.md`.
- General architecture and coordination flows: `docs/ARCHITECTURE.md` and `docs/COORDINATION_FLOW.md`.
- Implementation details and developer notes: `docs/IMPLEMENTATION_SUMMARY.md`.

**Phase 2 — Future / Extension (high-level)**

Phase 2 is presented in `docs/PHASE2_ARCHITECTURE.md`. Below is a concise, beginner-friendly summary of what Phase 2 represents and how it extends the current project:

- **Scaling & Multi‑plant Orchestration**: extend the orchestrator to coordinate multiple physical or logical factory instances, enable cross‑site job routing and shared inventory management.
- **Advanced Scheduling & Optimization**: add scheduling algorithms (priority, makespan minimization, load balancing) and integrate them into the workflow manager to produce optimized production plans.
- **Predictive Maintenance & Analytics**: collect telemetry from machines, store time series metrics (e.g., using TimeScaleDB), and apply ML models to predict failures and suggest maintenance windows.
- **Cloud Integration & Remote Monitoring**: provide a cloud gateway for aggregated logs/metrics, remote dashboards, and multi‑tenant support for monitoring many factories at once.
- **Security & Identity**: strengthen authentication/authorization for services, enable TLS for MQTT and service-to-service communication, and add secrets management.
- **Extensible Machine Types & Plugins**: make machine interfaces pluggable so new machine behaviors (e.g., embroidery, embroidery‑robot, laser cutting) can be added easily via a plugin API.
- **Developer Experience**: provide richer local dev tooling (CLI to spawn demo workflows, test harnesses, and a lightweight local dashboard) to lower the onboarding overhead for new contributors.

Phase 2 is intentionally described at a high level — details and implementation choices depend on which features you prioritize. See `docs/PHASE2_ARCHITECTURE.md` for the full Phase 2 writeup and suggested milestones.

**Next steps for a beginner**
- Try the full `docker-compose up --build` run and then watch `docker-compose logs -f`.
- Open the customizer frontend (if running) and trigger a demo workflow from the UI or by posting the JSON workflow into the orchestrator API (see `docs/QUICKSTART_ORCHESTRATOR.md`).
- Explore `simple_factory_simulator/` to see how machine messages are published and how the orchestrator consumes them.

If you want, I can also:
- add a short script to launch a single end‑to‑end demo workflow,
- add explicit commands for posting a workflow to the orchestrator API,
- or update `docs/README.md` to point to this beginner guide.

---
Generated: consolidated beginner guide for local setup and Phase 2 summary.
