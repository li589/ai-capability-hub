---
name: cgda-system-health-check
description: Automated system health verification across all CGDA components. Checks FastAPI, Redis, Gateway, MinIO, and Open-Meteo services with diagnostic reports and troubleshooting suggestions. Triggers on status/health/check commands for CGDA platform monitoring.
version: 1.0.0
---

# CGDA System Health Check Skill

## Overview
Automated comprehensive health verification for the Comprehensive Geographic Data Analysis (CGDA) platform. This skill extracts and enhances the `show_status()` workflow pattern from `cgda-launch.py`, providing intelligent multi-service diagnostics with cross-platform compatibility (Windows/Linux/macOS).

## When to Use
Use this skill when users request:
- "Check CGDA system status" / "CGDA 系统状态检查"
- "Are all services healthy?" / "服务都正常吗？"
- "System health check" / "健康检查"
- "What's the status of all components?" / "所有组件状态如何？"
- "Troubleshoot CGDA startup issues" / "启动问题排查"
- Any variation containing: health, status, check, verify, monitor

## Core Workflow

### Step 1: Multi-Service Parallel Detection
Execute concurrent checks for all critical components:
- **FastAPI Backend** (`http://localhost:8000/health`)
  - Verify JSON response with `"status": "ok"`
  - Measure response time
  
- **Redis Broker** (`redis-cli ping`)
  - Test connection via Docker container (`cgda-redis`)
  - Verify PONG response
  - Check connected clients count
  
- **Nginx Gateway** (`http://localhost:5175/health`)
  - Confirm gateway accessibility
  - Validate upstream proxy status
  
- **MinIO Object Storage** (`http://localhost:9100/minio/health/live`)
  - Check API health endpoint
  - Verify HTTP 200 response
  
- **Open-Meteo Weather Service** (`http://localhost:8080/health`)
  - Validate weather API availability
  
### Step 2: Status Report Generation
Generate human-readable diagnostic report using ASCII character set:
```
✅ = Healthy service
❌ = Failed/unavailable
⚠️ = Degraded performance (slow response)
ℹ️ = Additional context
```

Report structure:
- Service name + Docker container status
- Response metrics (HTTP code, latency, connection count)
- Timestamp of last successful check
- Overall system health percentage

### Step 3: Intelligent Diagnostics & Recommendations
For each failing/degraded service:
- Provide specific error cause analysis
- Suggest targeted restart command
- Offer common solutions based on failure pattern
- Link to relevant documentation sections

## Technical Features

### Cross-Platform Compatibility
- Windows GBK console support (uses ✓/✗ fallback when emoji unsupported)
- UTF-8 detection and encoding handling
- PowerShell/bash auto-detection for shell commands
- Path normalization for Windows/Linux differences

### Performance Optimization
- Concurrent HTTP requests via async/aiohttp
- Connection pooling for Redis/MongoDB
- Timeout-aware retries (3 attempts with exponential backoff)
- Result caching for repeated checks (10-second TTL)

### Diagnostic Depth Levels
- **Quick mode**: Basic connectivity + HTTP codes
- **Standard mode**: Connection metrics + latency measurement (default)
- **Verbose mode**: Full stack traces, container logs, environment variables

## Usage Examples

### Example 1: Quick Status Check
**User input**: "帮我检查一下 CGDA 系统状态"

**Skill response**:
```
🏥 CGDA System Health Report
Generated: 2026-07-31 14:23:45 CST
Overall Status: ✅ 85% Healthy (5/6 services)

┌─────────────────┬────────┬──────────────┬──────────────┐
│ Service         │ State  │ Metrics      │ Notes        │
├─────────────────┼────────┼──────────────┼──────────────┤
│ FastAPI         │ ✅ OK  │ 200ms        │ v2.1.3       │
│ Redis           │ ✅ OK  │ PONG | 223   │ Connected    │
│ Gateway         │ ✅ OK  │ 200 OK       │ Upstream OK  │
│ MinIO           │ ⚠️ SLOW│ 200 | 850ms  │ High latency │
│ Open-Meteo      │ ✅ OK  │ 200 OK       │ Fresh data   │
│ Celery Worker   │ ❌ XON │ Not found    │ Need manual  │
└─────────────────┴────────┴──────────────┴──────────────┘

⚠️  Recommended Actions:
1. Start Celery Worker: python launch.py start worker
2. Monitor MinIO: May need resource allocation check

💡 Run 'python launch.py status --verbose' for full details
```

### Example 2: Detailed Troubleshooting
**User input**: "CGDA 启动有问题，请详细诊断"

**Skill response**:
```
🔍 Deep Diagnostic Analysis...

[FAIL] Celery Worker Process
  Cause: No Python process listening on port range 8000-9000
  Evidence: ps aux | grep celery → no matching processes found
  
[RECOMMENDATION] 
  Execute: cd project_dir && python launch.py start worker
  Alternative: docker exec -it cgda-worker celery -A tasks worker -l info
  
[INFO] Redis shows high client count (223)
  Interpretation: Many pending tasks in queue
  Suggestion: Increase worker concurrency: --concurrency 4

📊 Related logs available at:
   Code/backend/logs/celery_worker.log
   Docker logs: docker logs cgda-celery-worker
```

## Command Reference

### Built-in Launcher Commands
```bash
# Quick status check
python launch.py status

# Verbose diagnostics
python launch.py status --verbose

# Start all services
python launch.py start all

# Start specific component
python launch.py start worker
python launch.py start beat
python launch.py start fastapi

# Stop everything gracefully
python launch.py stop
```

### Platform-Specific Notes

#### Windows (PowerShell/CMD)
- Always use double quotes for paths with spaces
- Enable UTF-8: `chcp 65001` before running scripts
- Admin privileges may be needed for Docker operations

#### Linux/macOS (Bash/Zsh)
- Shell scripts `./start.sh` work natively
- Use `sudo` only if ports 5175/8000 are reserved

#### Docker Desktop
- Ensure Docker daemon is running: `docker info`
- Check container health: `docker ps --filter name=cgda-*`
- View logs: `docker logs cgda-[service-name]`

## Edge Cases & Error Handling

| Scenario | Behavior | User Guidance |
|----------|----------|---------------|
| Docker not running | Skip container checks, flag as unavailable | "Start Docker Desktop first" |
| Port conflict | Detect and list conflicting PIDs | "Kill process: taskkill /PID [id]" |
| Network timeout | Retry 3x, then mark as degraded | "Check firewall rules" |
| Partial failure | Report healthy/fail ratios | "Focus troubleshooting on failed items" |
| Empty results | Return "no data available" message | "Run full system startup first" |

## Maintenance Notes

### Updating Service Endpoints
When adding new services to CGDA:
1. Add health check URL/port to `check_services()` function
2. Update report table template with new column
3. Test on all three platforms (Win/Linux/Mac)

### Performance Tuning
For large deployments:
- Reduce timeout thresholds from 5s → 2s per service
- Use parallel batch checks instead of sequential
- Cache results longer during development sessions

### Security Considerations
- Never expose internal network topology in reports
- Sanitize log output (remove API keys, passwords)
- Use read-only credentials for health endpoints

## Version History

- **v1.0.0** (2026-07-31): Initial release
  - Extracted from cgda-launch.py show_status() pattern
  - Added cross-platform compatibility layer
  - Implemented intelligent diagnosis recommendations
  - Support for 5 core services + extensible architecture

---

**Author**: QoderWork Agent  
**Last Updated**: 2026-07-31  
**Compatibility**: CGDA Platform v2.0+ | Python 3.12+ | Docker 24.0+