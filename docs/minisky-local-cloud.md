# Local Cloud Hosting & Emulation Guide (MiniSky GCP)

This document provides a comprehensive operational and architectural guide to running and testing the **Suraksha Identity Protection Platform** (`aadhar-tracker`) locally against an emulated Google Cloud Platform (GCP) stack using **MiniSky** (vendored in [`minisky_fork/`](../minisky_fork/)).

---

## 1. Overview & Objectives

In production, the Suraksha platform leverages serverless container hosting (Google Cloud Run), identity vault secret management (Google Secret Manager), and tamper-evident audit archiving (Google Cloud Storage). 

Traditional cloud testing requires GCP billing accounts, IAM credentials, Internet connectivity, and deployment delays. **MiniSky** provides a zero-cost, fully offline, sub-100ms GCP emulator written in Go that simulates GCP REST and gRPC APIs while managing local Docker containers for serverless workloads.

### Key Capabilities Tested
1. **Google Cloud Run (`run.googleapis.com`)**: Provisions dynamic Docker containers for `aadhar-tracker:latest`, maps dynamic host ports, and routes traffic.
2. **Google Secret Manager (`secretmanager.googleapis.com`)**: Stores and serves 256-bit AES master encryption keys (`APP_MASTER_ENCRYPTION_KEY`) with versioning.
3. **Google Cloud Storage (`storage.googleapis.com`)**: Auto-provisions a local `fake-gcs-server` on port 4443 to manage audit log buckets and media object uploads.
4. **Multi-Worker Concurrency**: Validates that multi-process Uvicorn containers safely share session states, CSRF tokens, and step-up elevations via SQLite.

---

## 2. Emulation Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Local Laptop Environment                        │
│                                                                        │
│   MiniSky Daemon (:8080 API Gateway & :8081 Web Dashboard)             │
│   ├── run.googleapis.com ────────────► Docker Engine (Serverless VM)    │
│   │                                    └── minisky-serverless-aadhar-  │
│   │                                        tracker (:55003 -> :8000)   │
│   │                                                                    │
│   ├── secretmanager.googleapis.com ──► In-memory Secret Store           │
│   │                                    └── APP_MASTER_ENCRYPTION_KEY   │
│   │                                                                    │
│   └── storage.googleapis.com ────────► Fake-GCS Server (:4443)         │
│                                        └── gs://suraksha-audit-logs    │
└────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown
| Component | Port | Interface | Purpose |
| :--- | :--- | :--- | :--- |
| **MiniSky API Gateway** | `:8080` | HTTP / REST | Intercepts standard GCP endpoints (`/v2/projects/*/locations/*/services`, `/v1/projects/*/secrets`, etc.) |
| **MiniSky Dashboard** | `:8081` | Web GUI | Visual control plane for inspecting services, logs, secrets, and storage buckets |
| **Suraksha Container** | `:55003` | HTTP / REST | Live Docker container running FastAPI, Verhoeff validator, and WhatsApp DLP |
| **Fake-GCS Server** | `:4443` | HTTP / GCS REST | Emulated Google Cloud Storage backend spun up on demand |

---

## 3. Prerequisites & Setup

### Requirements
- **macOS (Darwin ARM64 / Intel)** or **Linux (x86_64 / arm64)**
- **Docker Desktop** installed and running
- **Python 3.11+** with `uv`
- **cURL** and **jq** (or Python `json.tool`)

### MiniSky Installation & Availability
The MiniSky binary and source are pre-bundled directly within the repository in [`minisky_fork/`](../minisky_fork/):

```bash
# Verify pre-built binary
./minisky_fork/minisky version
```

---

## 4. Step-by-Step Deployment & Testing Workflow

### Step 1: Start the MiniSky Daemon

Launch the daemon in background mode:
```bash
./minisky_fork/minisky start
# Or from the directory:
# cd minisky_fork && ./minisky start
```
*Expected Output:*
```
MiniSky Daemon started successfully.
API Gateway: http://localhost:8080
Dashboard:   http://localhost:8081
```

To stop the daemon when testing concludes:
```bash
./minisky stop
```

---

### Step 2: Build the Production Container Image

Build the multi-stage, non-root Docker image:
```bash
cd /Users/dpcubed/projects/aadhar-tracker
docker build -t aadhar-tracker:latest .
```

*Key Dockerfile Details:*
- Base: `python:3.11-slim`
- Non-root user: `appuser` (UID 10001, GID 10001)
- Persistence volume: `/app/data` owned by `appuser`
- Healthcheck: Probes `http://localhost:${PORT:-8000}/livez` every 20 seconds.

---

### Step 3: Deploy Service to Emulated Cloud Run

Submit a standard GCP Cloud Run v2 REST creation payload to the MiniSky API Gateway:

```bash
curl -s -X POST "http://localhost:8080/v2/projects/local-dev-project/locations/asia-south1/services?serviceId=aadhar-tracker" \
  -H "Content-Type: application/json" \
  -d '{
    "template": {
      "containers": [{
        "image": "aadhar-tracker:latest",
        "ports": [{"containerPort": 8000}],
        "env": [
          {"name": "PORT", "value": "8000"},
          {"name": "WORKERS", "value": "2"},
          {"name": "ENVIRONMENT", "value": "production"},
          {"name": "DATABASE_URL", "value": "sqlite+aiosqlite:////app/data/suraksha.db"},
          {"name": "SESSION_DB_PATH", "value": "/app/data/sessions.db"}
        ]
      }]
    }
  }'
```

*Response:*
```json
{
  "done": false,
  "name": "projects/local-dev-project/locations/asia-south1/operations/operation-1794223681-kxw40up8"
}
```

Wait 3 seconds for container instantiation, then discover the mapped port:
```bash
docker ps --filter "name=minisky"
```
*Example Output:*
```
CONTAINER ID   IMAGE                   STATUS         PORTS                       NAMES
dba57b9717aa   aadhar-tracker:latest   Up (healthy)   127.0.0.1:55003->8000/tcp   minisky-serverless-aadhar-tracker
```
*(Here the host port is `55003`)*.

---

### Step 4: Validate Container Health Probes

```bash
curl -i http://127.0.0.1:55003/livez
```

*Expected HTTP Response:*
```http
HTTP/1.1 200 OK
date: Mon, 09 Nov 2026 11:28:14 GMT
server: uvicorn
content-type: application/json
x-frame-options: DENY
x-content-type-options: nosniff
strict-transport-security: max-age=63072000; includeSubDomains; preload
content-security-policy: default-src 'self'; ...

{"status":"alive","timestamp":"2026-11-09T11:28:15.369695+00:00"}
```

---

### Step 5: Emulate Google Secret Manager

Configure encryption keys in MiniSky's Secret Manager shim:

```bash
# 1. Create Secret Resource
curl -X POST "http://localhost:8080/v1/projects/local-dev-project/secrets?secretId=APP_MASTER_ENCRYPTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"replication":{"automatic":{}}}'

# 2. Add Secret Version (Base64-encoded 256-bit AES Key)
curl -X POST "http://localhost:8080/v1/projects/local-dev-project/secrets/APP_MASTER_ENCRYPTION_KEY:addVersion" \
  -H "Content-Type: application/json" \
  -d '{"payload":{"data":"MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="}}'

# 3. Read Secret Version Payload
curl -s "http://localhost:8080/v1/projects/local-dev-project/secrets/APP_MASTER_ENCRYPTION_KEY/versions/latest:access"
```

---

### Step 6: Emulate Google Cloud Storage (Audit Logs)

Provision an emulated GCS bucket and upload an immutable audit log blob:

```bash
# 1. Create Regional Bucket in asia-south1
curl -X POST "http://localhost:8080/storage/v1/b?project=local-dev-project" \
  -H "Content-Type: application/json" \
  -d '{"name":"suraksha-audit-logs","location":"asia-south1"}'

# 2. Upload Audit Event Blob
curl -X POST "http://localhost:8080/upload/storage/v1/b/suraksha-audit-logs/o?uploadType=media&name=audit-2026-11-09.json" \
  -H "Content-Type: application/json" \
  -d '{"event":"identity_canary_test","timestamp":"2026-11-09T16:58:25Z","subject":"citizen@suraksha.in","status":"SUCCESS"}'

# 3. Download and Verify Object
curl -s "http://localhost:8080/storage/v1/b/suraksha-audit-logs/o/audit-2026-11-09.json?alt=media"
```

---

### Step 7: Execute End-to-End Canary & DLP Workflows

Execute complete tracking flows against the emulated Cloud Run container:

```bash
PORT=55003

# 1. Authenticate Citizen
AUTH_RESP=$(curl -s "http://127.0.0.1:$PORT/api/v1/auth/callback?email=citizen@suraksha.in&full_name=Aarav+Sharma")
TOKEN=$(echo "$AUTH_RESP" | python3 -c 'import sys, json; print(json.load(sys.stdin)["data"]["session_id"])')
echo "Citizen Token: $TOKEN"

# 2. Fetch Sandbox Canary Presets
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PORT/api/v1/identity-assistance/canary-presets" | python3 -m json.tool

# 3. Execute Canary Exposure Test (UIDAI Sandbox #1: Standard)
curl -s -X POST "http://127.0.0.1:$PORT/api/v1/identity-assistance/canary-test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"preset_id":"aadhaar_sandbox_1"}' | python3 -m json.tool

# 4. Execute WhatsApp DLP Simulation
curl -s -X POST "http://127.0.0.1:$PORT/api/v1/integrations/whatsapp/simulate-share" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_text": "Sharing Aadhaar 9999 4105 7058 and PAN ABCDE1234F for office verification",
    "sender_phone": "+919876543210",
    "recipient_phone": "HR Vendor WhatsApp Group",
    "channel": "whatsapp_group"
  }' | python3 -m json.tool

# 5. Verify Ingested Incidents via RLS-isolated Query
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PORT/api/v1/incidents" | python3 -m json.tool
```

---

## 5. Architectural Findings & Container Hardening

### Multi-Worker Session Synchronization
- **Challenge**: In a multi-worker container (`uvicorn --workers 2`), the OS kernel load-balances incoming connections across worker child processes. In-memory session dictionaries caused alternating requests to fail authentication with `"Invalid or expired session"`.
- **Resolution**:
  - Implemented SQLite session persistence in [`packages/security/sessions.py`](file:///Users/dpcubed/projects/aadhar-tracker/packages/security/sessions.py).
  - Maintained in-memory L1 cache with write-through to table `user_sessions`.
  - Added cross-process step-up elevation synchronization (`update_step_up`).
  - Added automatic schema creation and directory initialization (`/app/data/sessions.db`).

### SQLite File Locking in Multi-Worker Containers
- **Challenge**: Concurrent worker startup triggered `sqlite3.OperationalError: table users already exists` during `Base.metadata.create_all`.
- **Resolution**: Wrapped table creation in [`services/api/database.py`](file:///Users/dpcubed/projects/aadhar-tracker/services/api/database.py) with `checkfirst=True` and ignored duplicate table creation errors, allowing multiple workers to safely share the same SQLite database file.

---

## 6. Cleanup Commands

To cleanly remove the emulated Cloud Run container and stop MiniSky:
```bash
# Remove Cloud Run container
docker rm -f minisky-serverless-aadhar-tracker

# Stop MiniSky daemon
./minisky_fork/minisky stop
# Or: cd minisky_fork && ./minisky stop
```
