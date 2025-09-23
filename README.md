# Fall Prevention ETL Data Pipeline

## Docker Setup
⚙️ Requirements
- [Desktop](https://docs.docker.com/get-docker/) (Windows/macOS/Linux)
- [Docker Compose](https://docs.docker.com/compose/) v2+ (comes with Docker Desktop)


### Verify installation

```
docker --version
docker compose version
```

### Run the Docker containers
**Windows**
Usage in Git Bash (calling Git Bash explicitly):
```
./run-docker.sh
```

**Linux/macOS**
You just need to make it executable once:
```
chmod +x run-docker.sh
```

Then run it:
```
./run-docker.sh
```

### Extra Docker Compose Commands

The `run-docker.sh` script supports several commands to help manage the Docker stack. Usage:

```
./run-docker.sh [command]
```

Available commands:

- `up` (default): Start all services in detached mode
- `down`: Stop all services
- `restart`: Restart all services and wipe volumes
- `pause`: Pause all running containers
- `unpause`: Unpause all paused containers
- `ps`: Show status of containers
- `build [service]`: Build services (optionally specify service name)
- `logs [service]`: Show logs (optionally specify service name)

Example:
```
./run-docker.sh logs spark
```
This will show logs for the `spark` service.

---

### Simulator Service

The stack includes a **simulator** service that generates simulated gyroscope and accelerometer data and publishes it to MQTT (`wearable/simulator` topic).

The simulator runs automatically when you start the stack:
```
./run-docker.sh up
```

You can view its logs with:
```
./run-docker.sh logs simulator
```

The Python source is in `simulator.py`. The Dockerfile is `docker/Dockerfile.simulator`.
