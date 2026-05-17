# Deploying to Vultr — Step-by-Step Guide

This document walks through the exact process used to containerise and deploy the Health Insurance Claim Pipeline microservice onto **Vultr Kubernetes Engine (VKE)**.

---

## Prerequisites

| Tool | Version Used | Install |
|------|-------------|---------|
| Docker Desktop | 4.x+ | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| `kubectl` | v1.35+ | Bundled with Docker Desktop, or `brew install kubectl` |
| Docker Hub account | — | [hub.docker.com](https://hub.docker.com) |
| Vultr account | — | [vultr.com](https://www.vultr.com) |

---

## Phase 1 — Prepare the Docker Image

### 1.1 Write a production `Dockerfile`

The `Dockerfile` at the project root defines how the image is built. Key decisions made:

```dockerfile
FROM python:3.12.4-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Non-privileged runtime user (security best practice)
RUN adduser --disabled-password --gecos "" --uid 10001 appuser

# Install dependencies using build-cache mount for speed
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Copy only what the app needs (not .venv, notebooks, tests)
COPY app ./app
COPY data ./data

# Seed the SQLite database at build time (no migration step at startup)
RUN python -m app.database

USER appuser
EXPOSE 8000

# Production: no --reload, 2 workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

> [!TIP]
> The DB seeding step `RUN python -m app.database` happens at **build time**, so the container starts instantly with a fully populated SQLite database — no migration script needed.

### 1.2 Write a `.dockerignore`

Prevents unnecessary files from inflating the image context (`.venv`, notebooks, PDFs used only locally, test scripts, etc.). This keeps the final image lean.

### 1.3 Pin all dependencies in `requirements.txt`

`pip freeze` from the `.venv` was used to produce exact pinned versions. Only **production** packages were included — dev tooling like `pipreqs`, `jupyter`, and `ipython` were excluded manually.

> [!NOTE]
> `pipreqs . --force` was attempted first but crashed because it tried to decode the binary PDF files in the `data/` directory. The solution was to use `.venv/bin/pip freeze` instead and curate the output.

---

## Phase 2 — Build and Push a Multi-Platform Image

### 2.1 Why multi-platform matters

The development machine is an **Apple Silicon Mac (ARM64)**. Vultr's compute nodes run **AMD64 (x86_64) Linux**. A standard `docker build` on a Mac produces an ARM64-only image. When Kubernetes tries to pull that image onto an AMD64 node, it throws:

```
Failed to pull image: no match for platform in manifest
```

The fix is a **multi-platform manifest** — a single Docker Hub tag that contains separate image layers for each architecture. Docker automatically serves the right one based on the node's CPU.

### 2.2 Create the multi-platform builder

```bash
docker buildx create --name multiplatform --driver docker-container --bootstrap --use
```

This creates a `buildx` builder backed by a `docker-container` driver (which uses BuildKit + QEMU emulation to cross-compile AMD64 on ARM).

### 2.3 Build and push simultaneously

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --push \
  -t lee1613/llm-microservice:v1 \
  .
```

- `--platform linux/amd64,linux/arm64` — compile for both architectures in one command
- `--push` — push directly to Docker Hub (bypasses local image storage, required for multi-platform builds)
- `-t lee1613/llm-microservice:v1` — the tag on Docker Hub

> [!NOTE]
> Cross-compiling AMD64 on ARM via QEMU takes longer than a native build (~8–12 minutes vs ~2 minutes). This is a one-time cost; subsequent builds reuse cached layers.

---

## Phase 3 — Provision a Vultr Kubernetes Cluster

### 3.1 Create the cluster on Vultr

1. Log in to the [Vultr dashboard](https://my.vultr.com)
2. Navigate to **Kubernetes** → **Add Cluster**
3. Choose a region (e.g., Singapore `sgp1`)
4. Select a node plan (e.g., 2 × `vc2-2c-4gb` — 2 vCPU, 4 GB RAM each)
5. Click **Deploy Now**

Vultr provisions the control plane and both worker nodes automatically. This takes 3–5 minutes.

### 3.2 Download the kubeconfig

Once the cluster is ready:

1. Open the cluster detail page on the Vultr dashboard
2. Click **Download Config** — this saves a `.yaml` file (e.g., `vke-23d79282-....yaml`)
3. Move it to your local `~/.kube/config`:

```bash
mv ~/Downloads/vke-23d79282-3a5c-4acc-8282-1451cfdcbf69.yaml ~/.kube/config
```

### 3.3 Verify connectivity

```bash
kubectl get nodes
```

Expected output:
```
NAME                    STATUS   ROLES    AGE   VERSION
hackatho-68b60fc9ebf5   Ready    <none>   5m    v1.35.2
hackatho-c1ac45c264d6   Ready    <none>   5m    v1.35.2
```

Both nodes in `Ready` state means the cluster is fully operational.

---

## Phase 4 — Store Secrets in Kubernetes

API keys must **never** be baked into the Docker image. They are injected at runtime via Kubernetes Secrets.

### 4.1 Create the API key secret

```bash
kubectl create secret generic llm-secrets \
  --from-literal=VULTR_SERVERLESS_INFERENCE_API_KEY=<your_key> \
  --from-literal=GEMINI_API_KEY=<your_key>
```

### 4.2 Create the Docker Hub pull secret

The cluster nodes need credentials to pull the image from Docker Hub. Extract the credentials from your local Docker credential store and create a Kubernetes secret:

```bash
# Extract credentials from local keychain (macOS)
echo "https://index.docker.io/v1/" | docker-credential-desktop get > /tmp/creds.json

# Build the dockerconfigjson format
python3 -c "
import json, base64
with open('/tmp/creds.json') as f:
    cred = json.load(f)
auth = base64.b64encode(f\"{cred['Username']}:{cred['Secret']}\".encode()).decode()
config = {'auths': {'https://index.docker.io/v1/': {'auth': auth}}}
with open('/tmp/docker-auth.json', 'w') as f:
    json.dump(config, f)
"

# Create the Kubernetes secret
kubectl create secret generic dockerhub-creds \
  --from-file=.dockerconfigjson=/tmp/docker-auth.json \
  --type=kubernetes.io/dockerconfigjson

# Clean up sensitive temp files
rm /tmp/creds.json /tmp/docker-auth.json
```

---

## Phase 5 — Write and Apply the Kubernetes Manifests

The manifest file at `k8s/deployment.yaml` defines two Kubernetes resources:

### 5.1 The Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-microservice
spec:
  replicas: 2                    # One pod per node for HA
  selector:
    matchLabels:
      app: llm-microservice
  template:
    spec:
      imagePullSecrets:
        - name: dockerhub-creds  # Allows nodes to pull the private image
      containers:
        - name: api
          image: lee1613/llm-microservice:v1
          ports:
            - containerPort: 8000
          env:
            - name: VULTR_SERVERLESS_INFERENCE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: VULTR_SERVERLESS_INFERENCE_API_KEY
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: GEMINI_API_KEY
          readinessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 5
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 15
          resources:
            requests: { cpu: "250m", memory: "256Mi" }
            limits:   { cpu: "1000m", memory: "512Mi" }
```

### 5.2 The LoadBalancer Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-microservice-svc
spec:
  type: LoadBalancer         # Vultr provisions a public IP automatically
  selector:
    app: llm-microservice
  ports:
    - port: 80               # Public-facing port
      targetPort: 8000       # Container port
```

### 5.3 Apply the manifest

```bash
kubectl apply -f k8s/deployment.yaml
```

This creates both the Deployment and the Service in one command.

---

## Phase 6 — Verify the Deployment

### 6.1 Watch the rollout

```bash
kubectl rollout status deployment/llm-microservice --timeout=120s
```

Output when successful:
```
deployment "llm-microservice" successfully rolled out
```

### 6.2 Check pod status

```bash
kubectl get pods -o wide
```

```
NAME                                READY   STATUS    RESTARTS   AGE
llm-microservice-7c66bcf7df-9pss6   1/1     Running   0          2m
llm-microservice-7c66bcf7df-d88sq   1/1     Running   0          2m
```

### 6.3 Get the public IP

```bash
kubectl get service llm-microservice-svc
```

```
NAME                   TYPE           CLUSTER-IP      EXTERNAL-IP       PORT(S)
llm-microservice-svc   LoadBalancer   10.101.75.178   139.180.136.212   80:30499/TCP
```

The `EXTERNAL-IP` (`139.180.136.212`) is the public IP provisioned by Vultr's load balancer. This is your live API endpoint.

### 6.4 Smoke test

```bash
curl http://139.180.136.212/health
# → {"status": "healthy", "service": "llm-microservice"}
```

---

## Phase 7 — What Happens on Each Request

```
Client (curl / app)
      │
      ▼
Vultr Load Balancer  :80
      │
      ├─── Pod 1 (Node hackatho-68b60fc9ebf5) :8000
      └─── Pod 2 (Node hackatho-c1ac45c264d6) :8000
                │
                ├── FastAPI app
                ├── SQLite DB (baked in at build time)
                └── Vultr Serverless Inference API (Node 4 only)
```

Each request is load-balanced across the two pods. The SQLite database is embedded inside the image, so both pods are self-contained and stateless from a networking perspective.

---

## Ongoing Operations

### Update to a new version

```bash
# 1. Rebuild multi-platform and push
docker buildx build --platform linux/amd64,linux/arm64 --push -t lee1613/llm-microservice:v2 .

# 2. Update the running deployment in-place (zero downtime rolling update)
kubectl set image deployment/llm-microservice api=lee1613/llm-microservice:v2

# 3. Watch the rollout
kubectl rollout status deployment/llm-microservice
```

### View live logs

```bash
# All pods
kubectl logs -l app=llm-microservice -f

# Single pod
kubectl logs <pod-name> -f
```

### Scale

```bash
kubectl scale deployment llm-microservice --replicas=4
```

### Roll back

```bash
kubectl rollout undo deployment/llm-microservice
```

### Delete everything

```bash
kubectl delete -f k8s/deployment.yaml
kubectl delete secret llm-secrets dockerhub-creds
```
