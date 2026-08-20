---
name: cgda-system-startup-checklist
description: Automated comprehensive startup checklist and launcher for CGDA platform. Provides unified Python entry script with multi-phase execution workflow, cross-platform wrappers (.bat/.sh/.ps1), service monitoring, log management, and graceful shutdown. Triggers on startup/launch/start/all services commands.
version: 1.0.0
---

# CGDA System Startup Checklist Skill

## Overview
Automated comprehensive startup orchestration for the Comprehensive Geographic Data Analysis (CGDA) platform. This skill provides a unified startup checklist with multi-phase execution, cross-platform compatibility, real-time monitoring, and intelligent error recovery.

## When to Use
Use this skill when users request:
- "Start CGDA system" / "启动 CGDA 系统"
- "One-click startup" / "一键启动"
- "Full system launch" / "全系统启动"
- "How to start all services" / "如何启动所有服务"
- "Startup procedure" / "启动流程"
- "Bring up CGDA platform" / "拉起 CGDA 平台"
- Any variation containing: start, launch, boot, initialize, startup, bring up, run all

## Core Workflow

### Phase 1: Environment Pre-flight Check (5-10 seconds)
Execute parallel verification of prerequisites:

```yaml
Checklist:
  - Docker daemon running?          # docker info command
  - Port availability:              # netstat/ss check
      - 5175 (Gateway/Nginx)
      - 8000 (FastAPI Backend)
      - 6379 (Redis Broker)
      - 9100 (MinIO API)
      - 8080 (Open-Meteo)
  - Python environment:             # version >= 3.12
      - Virtual environment active?
      - Dependencies installed?
  - Project directory accessible:   # read permissions
```

**Output:** PASS/FAIL report with fix suggestions

### Phase 2: Infrastructure Services (Docker Containers)
Start foundational infrastructure in dependency order:

```bash
# Execution sequence:
1. cgda-redis       # Redis broker + result backend
2. cgda-minio       # Object storage (MinIO server + console)
3. cgda-open-meteo  # Weather data API
4. cgda-gateway     # Nginx reverse proxy + frontend serving
```

**Key Features:**
- Automatic container image pull if missing
- Health check verification after each start
- Log stream capture to project logs/
- Rollback on failure (stop previous containers)

### Phase 3: Application Layer Startup
Launch application components:

#### 3.1 FastAPI Backend
```bash
python launch.py start fastapi --host 0.0.0.0 --port 8000
```
- Async task queue initialization
- Database connection pool setup
- Algorithm catalog registration

#### 3.2 Celery Worker(s)
```bash
python launch.py start worker --concurrency 4 -l info
```
- Multi-queue support: default, business, weather_tile
- Prefetch settings optimization
- Heartbeat monitoring enabled

#### 3.3 Celery Beat Scheduler (Optional)
```bash
python launch.py start beat
```
- Periodic tasks: weather refresh, health checks
- Schedule persistence to Redis

### Phase 4: Post-start Verification
Validate all services are operational:

```python
verification_tests = [
    ("Redis ping", "redis-cli ping" == "PONG"),
    ("FastAPI health", "GET /health" == 200 OK),
    ("Gateway access", "http://localhost:5175" == reachable),
    ("MinIO API", "http://localhost:9100/minio/health/live" == 200),
    ("Open-Meteo", "http://localhost:8080/health" == 200),
    ("Worker registered", "celery inspect ping" > 0 workers),
]
```

**Success Criteria:** All tests must pass before reporting complete

### Phase 5: Summary & Access Information
Generate comprehensive startup report:

```
✅ CGDA System Started Successfully!
Time: 2026-07-31 14:30:25 CST
Duration: 47.3 seconds

┌─────────────────┬──────────────┬─────────────────────┐
│ Service         │ Port/Path    │ Status              │
├─────────────────┼──────────────┼─────────────────────┤
│ Gateway         │ :5175        │ ✅ Accessible       │
│ FastAPI         │ :8000        │ ✅ Healthy          │
│ Redis           │ :6379        │ ✅ Connected        │
│ MinIO API       │ :9100        │ ✅ Ready            │
│ MinIO Console   │ :9101        │ ✅ Login Available  │
│ Open-Meteo      │ :8080        │ ✅ Operational      │
│ Celery Workers  │ -            │ ✅ 4 processes      │
└─────────────────┴──────────────┴─────────────────────┘

📊 Access URLs:
  Frontend Dashboard: http://localhost:5175
  FastAPI Docs:       http://localhost:8000/docs
  MinIO Console:      http://localhost:9101
  Health Check:       http://localhost:8000/health

💡 Next Steps:
  - Visit dashboard to explore workflows
  - Submit test algorithm job
  - Monitor logs: code/backend/logs/celery_worker.log

⚠️  Troubleshooting: python launch.py status --verbose
```

## Platform-Specific Commands

### Unified Python Launcher (Recommended for All Platforms)

#### Windows (PowerShell/CMD)
```powershell
# One-line full startup
python launch.py start all

# Start specific components
python launch.py start docker
python launch.py start backend
python launch.py start worker
python launch.py start beat

# Monitoring
python launch.py monitor --follow
python launch.py logs --tail 50

# Graceful shutdown
python launch.py stop
python launch.py cleanup
```

#### Linux/macOS (Bash/Zsh)
```bash
# One-line full startup
python3 launch.py start all

# With verbose output
python3 launch.py start all -v

# Background mode
python3 launch.py start all --daemon
```

### Cross-Platform Wrapper Scripts

#### Windows Options

**Option A: Batch File (Classic CMD)**
```batch
@echo off
cd /d "%~dp0"
Env\Python312\python.exe launch.py start all
pause
```
Usage: `start.bat`

**Option B: PowerShell Script (Modern)**
```powershell
# start.ps1
$ErrorActionPreference = "Stop"
cd "$PSCommandPath\Directory"
Write-Host "Starting CGDA System..." -ForegroundColor Green
& .\Env\Python312\python.exe launch.py start all
if ($?) {
    Write-Host "✅ Start completed!" -ForegroundColor Green
} else {
    Write-Host "❌ Startup failed!" -ForegroundColor Red
}
pause
```
Usage: `powershell -ExecutionPolicy Bypass -File start.ps1`

**Option C: Enhanced Batch with Error Handling**
```batch
@echo off
setlocal enabledelayedexpansion

echo [CGDA] Starting system...
call Env\Python312\python.exe launch.py start all
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Startup failed! Check logs/
    exit /b 1
)
echo [SUCCESS] CGDA started successfully!
```

#### Linux/macOS Options

**Option A: Shell Script (POSIX compliant)**
```bash
#!/bin/sh
# start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[CGDA] Starting system..."
python3 launch.py start all

echo "✅ CGDA system started successfully!"
echo "Access URLs:"
echo "  - Dashboard: http://localhost:5175"
echo "  - API Docs:  http://localhost:8000/docs"
```
Usage: `chmod +x start.sh && ./start.sh`

**Option B: Zsh Function (for ~/.zshrc)**
```bash
# Add to ~/.zshrc
alias cgda-start='cd ~/proj/CGDA && python3 launch.py start all'
alias cgda-stop='python3 launch.py stop'
alias cgda-status='python3 launch.py status'
alias cgda-logs='tail -f code/backend/logs/*.log'
```

## Feature Reference

### Centralized Launch Command Interface

| Subcommand | Description | Options |
|------------|-------------|---------|
| `start all` | Launch everything | --daemon, --verbose |
| `start docker` | Start containers only | --force-recreate |
| `start backend` | FastAPI + dependencies | --host, --port |
| `start worker` | Celery workers | --concurrency N, --queues |
| `start beat` | Periodic tasks scheduler | - |
| `status` | Check all services | --verbose, --json |
| `monitor` | Real-time monitoring | --follow, --interval |
| `logs` | View logs | --tail N, --grep PATTERN |
| `stop` | Graceful shutdown | --timeout seconds |
| `cleanup` | Remove containers/logs | --volumes |

### Monitoring Mode

```bash
# Live dashboard-style monitoring
python launch.py monitor --follow

# Custom interval polling
python launch.py monitor --interval 5

# JSON output for scripting
python launch.py status --json > status.json
```

Example output:
```
=== CGDA System Monitor ===
Updated: 2026-07-31 14:35:12

[14:35:10] ✅ Redis      : PONG (223 clients)
[14:35:10] ✅ FastAPI    : 200 OK (12ms)
[14:35:10] ✅ Gateway    : 200 OK (45ms)
[14:35:10] ✅ MinIO      : 200 OK (89ms)
[14:35:10] ✅ Open-Meteo : 200 OK (156ms)
[14:35:10] ⚠️  Workers    : 3/4 registered (missing 1)

Status: DEGRADED - 1 worker offline since 14:32:01
Suggestion: Restart affected component
```

### Log Management

**Centralized logging strategy:**
```
Project root/
├── logs/
│   ├── startup.log          # Latest startup session
│   ├── startup.old.log      # Previous sessions (rotate)
│   └── errors.log           # Aggregated errors
│
Code/backend/logs/
├── celery_worker.log        # Worker stdout/stderr
├── celery_beat.log          # Scheduler logs
└── fastapi.access.log       # HTTP access logs
```

**Common log queries:**
```bash
# See last 100 lines of worker logs
python launch.py logs --tail 100 --worker

# Filter errors only
grep ERROR logs/celery_worker.log

# Follow startup progress
python launch.py logs --follow startup.log

# Extract error summary
python launch.py logs --grep ERROR --summary
```

### Graceful Shutdown & Cleanup

**Graceful stop (default):**
```bash
# Send SIGTERM, wait for workers to finish tasks
python launch.py stop
```

**Force kill (emergency):**
```bash
# Immediate termination
python launch.py stop --force
```

**Cleanup operations:**
```bash
# Remove containers, keep volumes
cd project_dir
python launch.py cleanup

# Full reset including data volumes (WARNING: destructive)
cd project_dir
python launch.py cleanup --volumes
```

## Troubleshooting Guide

### Common Issues & Solutions

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| "Address already in use" | Port conflict detected | Run `python launch.py status` → find conflicting PID → `taskkill /PID <id>` (Win) or `kill -9 <pid>` (Linux) |
| Docker not responding | Docker Desktop not started | Start Docker Desktop first, then retry |
| Redis connection refused | Container failed to start | Check `docker logs cgda-redis` → increase memory allocation |
| Worker not registering | Broker unavailable | Verify Redis running: `docker exec cgda-redis redis-cli ping` |
| MinIO access denied | Default credentials wrong | Use `minioadmin:minioadmin` or check `.env` configuration |
| Slow startup (>2 min) | Network/DNS issues | Set `DOCKER_DEFAULT_PLATFORM=linux/amd64` (Mac M1/M2) |
| Workers crash repeatedly | Dependency mismatch | Rebuild virtual env: `cd Env && rm -rf * && ../scripts/recreate_venv.sh` |

### Diagnostic Commands

```bash
# Full system diagnostics
python launch.py status --verbose > diagnostics.txt

# Collect logs from all containers
docker logs cgda-redis > logs/redis.log
docker logs cgda-minio >> logs/combined.log
docker logs cgda-open-meteo >> logs/combined.log

# Check process tree
# Windows:
Get-Process python | Format-Table Id, ProcessName, StartTime, WorkingSet

# Linux/macOS:
ps aux | grep -E 'celery|fastapi' | grep -v grep
```

## Error Recovery Procedures

### Automatic Retry Logic
The launcher includes built-in retry mechanism:

```python
# Pseudo-code behavior:
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

for service in ["redis", "minio", "open-meteo", "gateway"]:
    for attempt in range(MAX_RETRIES):
        try:
            start_service(service)
            verify_health(service, timeout=10)
            break  # Success!
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise  # Give up after final attempt
            time.sleep(RETRY_DELAY)
            log_warning(f"Retry {attempt+1}/{MAX_RETRIES} for {service}")
```

### Rollback Strategy
If any phase fails:

```bash
# Automatically triggered on failure:
echo "[ROLLBACK] Detected failure in Phase X, initiating rollback..."
python launch.py stop  # Graceful cleanup
python launch.py cleanup  # Remove partial state

# Manual intervention recommended:
cat logs/errors.log | tail -50
python launch.py status --verbose
```

## Advanced Usage

### Multi-Environment Support

**.env files per environment:**
```
.project.env          # Common settings
.project.env.dev      # Development overrides
.project.env.prod     # Production overrides
```

Select environment:
```bash
ENV=dev python launch.py start all
ENV=prod python launch.py start all
```

### Container Resource Limits

Custom resource allocation:
```bash
# Limit Redis memory
docker update --memory 512m --memory-swap 512m cgda-redis

# Increase worker concurrency
celery -A tasks worker --concurrency 8 --prefetch-multiplier 4

# Set Open-Meteo cache size
docker exec cgda-open-meteo echo "max_memory_size: 1GB" >> /etc/open-meteo.conf
```

### Integration with CI/CD

```yaml
# Example GitHub Actions snippet
name: CGDA Startup Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start system
        run: python launch.py start all --daemon
      - name: Wait for health
        run: |
          for i in {1..30}; do
            curl -s http://localhost:8000/health && exit 0
            sleep 2
          done
          exit 1
      - name: Run tests
        run: pytest tests/
```

## Version History

- **v1.0.0** (2026-07-31): Initial release
  - Unified Python launcher script (`launch.py`)
  - Cross-platform wrapper scripts (.bat/.sh/.ps1)
  - Multi-phase startup workflow with verification
  - Monitoring mode with real-time status updates
  - Comprehensive log management
  - Graceful shutdown and cleanup utilities
  - Built-in retry logic and automatic rollback
  - Platform-specific optimizations (Windows GBK, Linux systemd integration)

## Maintenance Notes

### Adding New Services
To integrate additional services into startup flow:

1. Add service to `STARTUP_SERVICES` dict in `launch.py`
2. Define health check endpoint in `check_health()`
3. Update dependency graph in `phase_durations` comments
4. Test on all target platforms

### Performance Tuning
For production deployments:

- Reduce container health check intervals from 30s → 10s
- Enable container restart policies: `--restart unless-stopped`
- Use persistent volumes for Redis cache (avoid data loss)
- Configure worker prefetch multiplier based on task type

### Security Hardening

- Never expose internal ports directly; use gateway proxy
- Rotate default MinIO credentials immediately after first start
- Use HTTPS in production: configure reverse proxy certificates
- Restrict Docker socket access: run containers with minimal privileges

---

**Author**: QoderWork Agent  
**Last Updated**: 2026-07-31  
**Compatibility**: CGDA Platform v2.0+ | Python 3.12+ | Docker 24.0+ | Windows 10/11 | Linux (Ubuntu 20.04+) | macOS 12+

**Related Skills**:
- [`cgda-system-health-check`](cgda-system-health-check): System health verification and diagnostics
- [`install-skill-dependency`](install-skill-dependency): Resolve missing Python packages or Docker images

**Quick Start**:
```bash
# Windows
cd "D:\path\to\CGDA"
python launch.py start all

# Linux/macOS
cd ~/path/to/CGDA
python3 launch.py start all

# Check status
python launch.py status
```