# Phase 6: Fixes + Observability Stack

## Part 1 — Phase 5 bug fixes (do these first)

Two bugs were found by reading the actual code, not just the logs.

### Bug 1: Dockerfile never copied `wsgi.py` into the image
`wsgi.py` exists in the repo but the Dockerfile only copied `app/`, `app.py`,
and `.env.example`. Gunicorn's `wsgi:app` target could never be found inside
the container — this was the real cause of every "Worker failed to boot" /
"Failed to find attribute 'app'" error.

**Fix (already applied to the Dockerfile in this delivery):**
```dockerfile
COPY app/ ./app/
COPY app.py .
COPY wsgi.py .
COPY .env.example .
```

### Bug 2: ALB health check path didn't match the app's actual route
`app/routes.py` registers the blueprint with `url_prefix="/api"`, so the
health endpoint is served at **`/api/health`**, not `/health`. The ALB
target group was configured to check `/health`, which 404s — so ECS/ALB
keeps marking the target unhealthy even once the container is running fine.
(Your own `docker-compose.yml` already correctly uses `/api/health` for its
local healthcheck, confirming this.)

**Fix — run once your ECS service is back up:**
```powershell
aws elbv2 modify-target-group `
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:632295790690:targetgroup/devsecops-tg/181709b5472ed8e7 `
  --health-check-path /api/health
```

### Deploy the fix
```powershell
git add Dockerfile
git commit -m "fix: copy wsgi.py into Docker image (was missing, causing gunicorn boot failure)"
git push origin main

aws ecs update-service --cluster devsecops-cluster --service devsecops-service --desired-count 1
```

Wait for the GitHub Actions workflow to finish (~2-3 min), then confirm:
```bash
curl http://devsecops-alb-1388549252.us-east-1.elb.amazonaws.com/api/health
curl http://devsecops-alb-1388549252.us-east-1.elb.amazonaws.com/api/metrics
```
Both should return 200. The second one is what Prometheus will scrape.

---

## Part 2 — Observability stack (Prometheus, Grafana, Loki)

Your app is already instrumented — `app/utils.py` defines 5 Prometheus
metrics and `app/routes.py` exposes them at `/api/metrics`. Nothing to add
to the app itself. This stack runs **locally** via Docker Compose and
scrapes your live AWS ALB over the internet, so there's no extra AWS cost.

### File layout
```
monitoring/
├── prometheus.yml              # scrape config, points at your ALB
├── alert_rules.yml             # 4 alert rules (errors, latency, auth, uptime)
├── loki-config.yml             # single-node Loki config
├── promtail-config.yml         # ships local log file into Loki
├── fetch-logs.sh               # pulls CloudWatch logs into that file
├── logs/                       # where fetch-logs.sh writes app.log
└── grafana/
    ├── provisioning/
    │   ├── datasources/datasources.yml   # auto-adds Prometheus + Loki
    │   └── dashboards/dashboards.yml     # auto-loads the dashboard below
    └── dashboards/
        └── flask-app-overview.json       # 8-panel starter dashboard
docker-compose.monitoring.yml   # the stack itself
```

### Setup

1. Copy the `monitoring/` folder and `docker-compose.monitoring.yml` into
   your project root (alongside your existing `docker-compose.yml`).

2. Make the log-fetch script executable (Linux/Mac/WSL):
   ```bash
   chmod +x monitoring/fetch-logs.sh
   ```

3. Start the stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

4. Pull in some logs (run this once now, and again periodically):
   ```bash
   ./monitoring/fetch-logs.sh
   ```
   On Windows without WSL, run the equivalent manually:
   ```powershell
   aws logs tail /ecs/aws-devsecops-pipeline --since 10m --format short >> monitoring/logs/app.log
   ```

5. Generate some traffic so there's data to see:
   ```bash
   for i in {1..20}; do curl -s http://devsecops-alb-1388549252.us-east-1.elb.amazonaws.com/api/health > /dev/null; done
   ```

### Access

| Tool | URL | Notes |
|---|---|---|
| Prometheus | http://localhost:9090 | Check **Status → Targets**, `flask-app-aws` should show as `UP` |
| Grafana | http://localhost:3000 | Login `admin` / `admin`. Dashboard auto-loads: **AWS DevSecOps Pipeline - App Overview** |
| Loki | http://localhost:3100 | Queried through Grafana's Explore tab, not directly |

The Grafana dashboard ships with 8 panels: request rate by endpoint, p95
latency, error rate by type, auth success/failure rate, active DB
connections, total requests in the last hour, scrape health (up/down), and
a live log panel from Loki.

### Alerting

`alert_rules.yml` defines four rules out of the box:
- **HighErrorRate** — `app_errors_total` growing faster than 0.1/sec for 2 min
- **HighRequestLatencyP95** — p95 latency over 1s for 5 min
- **HighAuthFailureRate** — auth failures over 0.2/sec for 2 min (brute-force signal)
- **MetricsEndpointDown** — Prometheus can't reach `/api/metrics` for 1 min

View firing/pending alerts under Prometheus → **Alerts**. Wiring these to
Slack/email/PagerDuty is a natural next step but out of scope for this
phase — Prometheus's `alertmanager` component handles routing if you want
to extend it later.

### Stopping the stack (no AWS cost either way — this all runs locally)
```bash
docker-compose -f docker-compose.monitoring.yml down
```
Add `-v` to also wipe stored metrics/logs/dashboards state.

---

## Resume line

> "Instrumented the Flask application with Prometheus metrics (request
> rate, latency histograms, error counts, auth outcomes) and built Grafana
> dashboards for real-time observability, with Loki for centralized log
> aggregation and Prometheus alerting rules for error-rate and latency
> anomalies."
