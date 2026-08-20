---
name: testing-performance
cluster: testing
description: "Perf: k6 load/stress/spike, Locust Python, JMeter, load profiles, SLA, p50/p95/p99, flame graphs"
tags:
  - performance-test
  - k6
  - locust
  - load-test
  - testing
dependencies: []
composes: []
similar_to: []
called_by: []
authorization_required: false
scope: general
model_hint: claude-sonnet
embedding_hint: performance load test k6 locust jmeter sla latency p95 flame graph
install_source: official
install_method: download
skill_id: official_XywXgDQR
enabled_at: 1787232596717
version: 1.0.0
name_zh: Python性能优化
---

# testing-performance

## Purpose
This skill enables performance testing using tools like k6, Locust, and JMeter to simulate load, stress, and spike scenarios, measure metrics such as p50/p95/p99 latency, enforce SLAs, and generate flame graphs for bottleneck analysis.

## When to Use
Use this skill when assessing application performance under load, identifying scalability issues, validating SLAs, or optimizing code before production. Apply it in pre-release testing, CI/CD pipelines, or when debugging high-latency problems in web services or APIs.

## Key Capabilities
- Run load tests with k6 using VU (virtual users) and duration settings to simulate traffic.
- Generate reports with metrics like p50 (median), p95 (95th percentile), and p99 latency from test outputs.
- Define load profiles in Locust via Python scripts for custom user behaviors and ramp-up rates.
- Enforce SLAs by setting thresholds in JMeter and checking against results.
- Create flame graphs using integrated profiling in k6 or external tools to visualize CPU/memory usage.
- Support distributed testing across multiple machines for large-scale simulations.

## Usage Patterns
To perform a basic load test, select a tool based on scenario: use k6 for quick scripts, Locust for Python-based customization, or JMeter for complex scenarios with UI elements. Always define a test script first, then run with specified profiles. For CI/CD, integrate as a step that triggers on code changes. Include parameterization for environments (e.g., staging vs. production) and always analyze results post-run. Example: Script a k6 test for an API endpoint, then scale it with Locust for user simulation.

## Common Commands/API
For k6, run tests via CLI: `k6 run -u 50 -d 1m script.js` (sets 50 virtual users for 1 minute). Use thresholds like `--threshold p(95)<500` to enforce p95 latency under 500ms. Script example:
```javascript
import http from 'k6/http';
export default function() { http.get('https://api.example.com'); }
```
For Locust, start with: `locust -f locustfile.py --host https://api.example.com --users 100 --spawn-rate 10` (100 users, 10 per second). Locustfile snippet:
```python
from locust import HttpUser, task
class QuickUser(HttpUser):
    @task
    def endpoint(self): self.client.get("/health")
```
For JMeter, execute via: `jmeter -n -t test_plan.jmx -l results.jtl` (non-GUI mode). JMeter config in .jmx XML format includes elements like Thread Group with 50 loops and HTTP Samplers. API endpoints: If testing requires auth, set env vars like `$K6_API_KEY` in scripts (e.g., `export K6_API_KEY=your_key` before running).

## Integration Notes
Integrate this skill into workflows by wrapping commands in scripts or CI tools like GitHub Actions: e.g., `run: k6 run script.js` in a YAML step. For cloud services, pass auth via env vars (e.g., `$LOCUST_API_TOKEN`) to access protected endpoints. Combine with monitoring tools by piping outputs (e.g., k6 JSON results to Prometheus). Ensure tools are installed via package managers (e.g., `npm install -g k6` or `pip install locust`), and use Docker images for consistency (e.g., `docker run loadimpact/k6 run - < script.js`). If using APIs, endpoints like k6's cloud API require `$K6_CLOUD_TOKEN` for uploads.

## Error Handling
Check exit codes after runs: k6 returns non-zero for failures, e.g., threshold breaches. In scripts, wrap commands with try-catch for Locust (e.g., in Python: `try: run_locust() except Exception as e: log(e)`). For JMeter, parse .jtl logs for errors like "Assertion failure" and set up listeners to halt on thresholds. Common issues: Handle network errors by adding retries in scripts (e.g., k6: `http.get(url, { retries: 3 })`), and use verbose flags like `k6 run --verbose script.js` for debugging. If auth fails, verify env vars (e.g., echo `$K6_API_KEY` before execution).

## Concrete Usage Examples
1. To test an e-commerce API for 100 users over 5 minutes with k6: Write a script with a GET request, then run `k6 run -u 100 -d 5m script.js --threshold "http_req_duration{type:200} < 500"`. Analyze output for p95 latency and ensure SLA compliance.
2. For simulating user logins with Locust: Create a locustfile.py with tasks for login and browsing, then execute `locust -f locustfile.py --host https://app.example.com --users 200 --run-time 10m`. Monitor for errors and generate reports to identify bottlenecks.

## Graph Relationships
- Related to: testing (cluster), performance-test (tag), k6 (tag), locust (tag), load-test (tag)
- Connected via: testing cluster for other testing skills, e.g., unit-testing or integration-testing
- Dependencies: monitoring skills for metric analysis, deployment skills for environment setup
