# HostelHub

College hostel management system. Wardens register students, allot rooms, track maintenance and complaints, log visitors and keep fee status.

DevOps capstone: FastAPI + React + PostgreSQL, Docker, GitHub Actions, Trivy, Helm on Kubernetes, Argo CD, Terraform (AWS EKS), Prometheus + Grafana.

- Latest green pipeline: [Actions run](https://github.com/tarun250/hostel_management/actions/runs/38163540967)
- Images: [hostelhub-backend](https://github.com/users/tarun250/packages/container/package/hostelhub-backend), [hostelhub-frontend](https://github.com/users/tarun250/packages/container/package/hostelhub-frontend) on GHCR
- Slides: [`HostelHub-Presentation.pptx`](HostelHub-Presentation.pptx)
- Live demo script (commit → pipeline → Argo CD rollout): [`docs/demo.md`](docs/demo.md)

## Features

- Student registration with roll number, course, year, contacts
- Rooms with capacity, live availability, allocate / vacate (full rooms are rejected)
- Maintenance requests per room: OPEN -> IN_PROGRESS -> RESOLVED
- Complaints board: OPEN / IN_REVIEW / CLOSED
- Visitor log with check-in and check-out
- Fees per student and term: PENDING / PAID, overdue flag
- Dashboard: occupancy %, free beds, pending dues, open issues

## Architecture

```
                  +-------------------- Kubernetes (namespace: hostelhub) --------------------+
 browser          |                                                                           |
   |              |   Ingress hostelhub.local                                                 |
   +--------------+--->  /      -> frontend Service -> nginx (React build)  x2               |
                  |      /api   -> backend Service  -> FastAPI (uvicorn)    x2  -- HPA        |
                  |                                     |  /metrics                           |
                  |                                     v                                     |
                  |                         postgres StatefulSet + PVC                        |
                  |                                                                           |
                  |   Prometheus --(ServiceMonitor)--> backend /metrics ---> Grafana          |
                  +---------------------------------------------------------------------------+

 git push -> GitHub Actions: test -> frontend build -> docker build -> Trivy -> GHCR -> kind deploy
 Argo CD: watches helm/hostelhub on main -> syncs namespace hostelhub-gitops
 Terraform: VPC (2 public + 2 private subnets) + EKS managed node group
```

Locally, docker compose runs the same three containers. nginx in the frontend proxies `/api` to the backend.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, psycopg 3 |
| Frontend | React 19, Vite, nginx (unprivileged) |
| Database | PostgreSQL 16 |
| Tests | pytest, httpx TestClient, in-memory SQLite, ruff |
| Containers | Docker (non-root images), docker compose |
| CI/CD | GitHub Actions, GHCR, Trivy, kind |
| Kubernetes | Helm 3/4 chart, Ingress, HPA, StatefulSet, minikube |
| GitOps | Argo CD |
| Cloud | Terraform, AWS VPC, EKS |
| Monitoring | prometheus-fastapi-instrumentator, kube-prometheus-stack, Grafana |

## API

Base path `/api`. Interactive docs at `/docs`.

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Liveness, no DB |
| GET | `/ready` | Readiness, runs `SELECT 1` on the DB |
| GET | `/metrics` | Prometheus metrics |
| GET, POST | `/api/students` | List (`?search=`, `?unallocated=true`) / register |
| GET, PUT, DELETE | `/api/students/{id}` | Read / update / remove |
| GET | `/api/students/{id}/fees` | Fees of one student |
| GET, POST | `/api/rooms` | List / create rooms |
| GET | `/api/rooms/available` | Rooms with at least one free bed |
| GET, PUT, DELETE | `/api/rooms/{id}` | Read (with occupants) / update / delete (only if empty) |
| POST | `/api/rooms/{id}/allocate` | Body `{"student_id": 1}`. 409 if room full or student already housed |
| POST | `/api/rooms/{id}/deallocate` | Body `{"student_id": 1}` |
| GET, POST | `/api/maintenance` | List (`?status=`, `?room_id=`) / raise request |
| GET, PUT, DELETE | `/api/maintenance/{id}` | Read / update / delete |
| PATCH | `/api/maintenance/{id}/status` | Body `{"status": "RESOLVED"}` |
| GET, POST | `/api/complaints` | List (`?status=`) / file complaint |
| GET, PUT, DELETE | `/api/complaints/{id}` | Read / update status / delete |
| GET, POST | `/api/visitors` | List (`?inside=true`) / check in |
| POST | `/api/visitors/{id}/checkout` | Check out |
| GET, POST | `/api/fees` | List (`?status=PENDING`) / raise fee |
| PUT | `/api/fees/{id}` | Update fee |
| PUT | `/api/fees/{id}/pay` | Mark paid, optional `{"payment_ref": "UPI-123"}` |
| GET | `/api/stats/summary` | Dashboard numbers |

## Run locally (without Docker)

Needs Python 3.13, Node 22 and a PostgreSQL server on `localhost:5432`.

```bash
# 1. Database (once)
psql -d postgres -c "CREATE ROLE hostelhub WITH LOGIN PASSWORD 'hostelhub';"
psql -d postgres -c "CREATE DATABASE hostelhub OWNER hostelhub;"

# 2. Backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://hostelhub:hostelhub@localhost:5432/hostelhub
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend (terminal 2)
cd frontend
npm install
npm run dev
```

- UI: http://localhost:5173 (Vite forwards `/api` to the backend on :8000)
- API docs: http://localhost:8000/docs

If you skip `export DATABASE_URL`, the backend falls back to the same `hostelhub:hostelhub@localhost` URL. The Compose `db` container also publishes port 5432, so stop the local Postgres while Compose runs to be sure which one `psql` reaches.

## Run locally (Docker Compose)

```bash
docker compose up -d --build
docker compose ps
```

- UI: http://localhost:3000
- API docs: http://localhost:8000/docs
- Postgres: localhost:5432 (hostelhub / hostelhub)

The backend runs `alembic upgrade head` before starting. Data stays in the `hostelhub-pgdata` volume.

```bash
docker compose down        # keep data
docker compose down -v     # wipe data
```

## Tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
ruff check .
pytest -v
```

Tests use in-memory SQLite through a `get_db` override. They never touch Postgres.

## Kubernetes (Helm)

```bash
kubectl apply -f k8s/namespace.yaml
helm lint helm/hostelhub
helm upgrade --install hostelhub helm/hostelhub -n hostelhub \
  --set backend.image.repository=ghcr.io/tarun250/hostelhub-backend \
  --set backend.image.tag=<git-sha> \
  --set frontend.image.repository=ghcr.io/tarun250/hostelhub-frontend \
  --set frontend.image.tag=<git-sha> \
  --set postgres.password=<db-password>
kubectl get pods,svc,ingress -n hostelhub
```

- `values-dev.yaml`: local images (`hostelhub-backend:local`), HPA off
- `values-prod.yaml`: HPA on, ServiceMonitor on, bigger volume
- Add `<ingress-ip> hostelhub.local` to your hosts file to use the Ingress

## Kubernetes (plain manifests)

For a quick test cluster without Helm, `k8s/` has a Deployment + Service for each tier (backend and frontend run 2 replicas, the DB is a single pod on `emptyDir`):

```bash
kubectl apply -f k8s/namespace.yaml -f k8s/deployment.yaml -f k8s/service.yaml
kubectl get pods,svc -n hostelhub
```

The frontend is exposed on NodePort `30080`. The images are `hostelhub-*:local`, so load them into the cluster first (`minikube image load` / `kind load docker-image`).

## Terraform (AWS)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
aws eks update-kubeconfig --region ap-south-1 --name hostelhub-eks
terraform destroy          # when done
```

Credentials come from `aws configure` or `AWS_PROFILE`. Nothing secret is committed. See `terraform/README.md`.

## Monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml \
  --set grafana.adminPassword=<password>
helm upgrade hostelhub helm/hostelhub -n hostelhub --reuse-values --set serviceMonitor.enabled=true
kubectl create configmap hostelhub-dashboard -n monitoring \
  --from-file=monitoring/grafana-dashboard-hostelhub.json
kubectl label configmap hostelhub-dashboard -n monitoring grafana_dashboard=1
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

Dashboard panels: request rate, p50/p95/p99 latency, 5xx ratio, status classes, writes by method.

## CI/CD

`.github/workflows/ci-cd.yml` runs on push to `main`, pull requests and manual dispatch.

| Job | What it does |
|---|---|
| `test` | ruff lint + `pytest -v`. Fails the pipeline on any failure |
| `frontend-build` | `npm ci && npm run build` |
| `build-scan-push` | Builds both images tagged with the commit SHA, Trivy scan (HIGH/CRITICAL, fail on fixable), pushes to GHCR on `main` |
| `deploy-kind` | On `main`: creates a kind cluster, loads the scanned images, `helm upgrade --install`, waits for rollout, smoke-tests `/health`, `/ready` and the UI |

Images: `ghcr.io/tarun250/hostelhub-backend:<sha>` and `ghcr.io/tarun250/hostelhub-frontend:<sha>`. Only `GITHUB_TOKEN` is used.

## GitOps (Argo CD)

`argocd/application.yaml` points Argo CD at `helm/hostelhub` on `main` with `values-gitops.yaml`, automated sync, `prune` and `selfHeal`. To deploy a new version, set the image tags in `values-gitops.yaml` to a SHA that CI pushed and push; Argo CD syncs the cluster to it. The DB password is in a Secret created by hand (`existingSecret`), so it is never in git. Setup steps: [`argocd/README.md`](argocd/README.md).

## Security

- Both images run as non-root (uid 10001 backend, uid 101 nginx)
- Trivy gate on HIGH/CRITICAL. pip is removed from the backend runtime image, which drops its vendored libraries that Trivy flagged
- DB password lives in a Kubernetes Secret, passed with `--set` at deploy time

## Project layout

```
backend/     FastAPI app, Alembic migrations, pytest suite, Dockerfile
frontend/    React + Vite app, nginx config template, Dockerfile
helm/        hostelhub Helm chart
k8s/         namespace, plain deployment + service manifests
terraform/   AWS VPC + EKS
monitoring/  kube-prometheus-stack values, Grafana dashboard
argocd/      Argo CD Application + setup
docs/        live demo script, screenshots
HostelHub-Presentation.pptx   final presentation
.github/     CI/CD workflow
```

## Screenshots

All taken from real runs on my machine (Windows, Docker Desktop).

### Dashboard
![Dashboard](docs/screenshots/10-ui-dashboard.png)

Mobile width:

![Mobile](docs/screenshots/17-ui-mobile.png)

### Rooms and allocation
![Rooms](docs/screenshots/11-ui-rooms.png)

### Students
![Students](docs/screenshots/12-ui-students.png)

### Maintenance
![Maintenance](docs/screenshots/13-ui-maintenance.png)

### Complaints
![Complaints](docs/screenshots/14-ui-complaints.png)

### Visitor log
![Visitors](docs/screenshots/15-ui-visitors.png)

### Fees
![Fees](docs/screenshots/16-ui-fees.png)

### pytest output
22 tests on in-memory SQLite (never the real DB).

![pytest](docs/screenshots/01-pytest.png)

### docker compose
![compose up](docs/screenshots/02-compose-up.png)
![compose ps](docs/screenshots/03-compose-ps.png)

```bash
docker compose logs --tail=8 backend
```
![compose logs](docs/screenshots/09-compose-logs.png)

### Backend endpoints
`/health`, `/ready` (checks the DB), `/docs`:

![health](docs/screenshots/04-health-ready.png)

`/metrics` (Prometheus format):

![metrics](docs/screenshots/05-metrics.png)

Swagger UI:

![swagger](docs/screenshots/08-swagger-docs.png)

### API calls
POST → PUT → allocate room → DELETE → GET gives 404:

![crud](docs/screenshots/06-api-crud.png)

Room capacity is enforced:

![409](docs/screenshots/07-room-full-409.png)

### Trivy scan
Trivy scans each image's OS packages (Debian for the backend, Alpine for the frontend) and every installed language package (Python wheels, npm) against known CVEs. The gate fails the build on any **HIGH or CRITICAL** CVE that **has a fix available** (`--ignore-unfixed`), because unfixable ones can't be acted on.

Final result: both images have **0 HIGH/CRITICAL fixable CVEs**, exit code 0 (the CI gate uses the same flags).

![trivy backend](docs/screenshots/20-trivy-backend.png)
![trivy frontend](docs/screenshots/21-trivy-frontend.png)

**A CVE it found:** the first backend scan failed. The findings came from the `python:3.13-slim` base image, not my code:

![base image cves](docs/screenshots/26-trivy-base-image-cves.png)

Example — **CVE-2026-97689** (urllib3 2.7.0, HIGH, fixed in 2.8.0): denial of service through unbounded memory allocation in urllib3's chunk parser. This urllib3 isn't one of my dependencies: it's the copy **bundled inside pip** (`site-packages/pip/_vendor/urllib3`), as is the flagged msgpack. pip is only needed at build time, so `backend/Dockerfile` runs `pip uninstall -y pip` after installing requirements. That removes the vulnerable copies from the runtime image, and the rescan of `hostelhub-backend` came back clean (above).

Both containers run as non-root:

![non-root](docs/screenshots/22-nonroot.png)

### Helm lint
![helm lint](docs/screenshots/23-helm-lint.png)

### Terraform
`fmt` + `init` + `validate` pass:

![terraform](docs/screenshots/24-terraform-validate.png)

**plan → apply → destroy** — I don't have an AWS account, so this ran against **[Moto](https://github.com/getmoto/moto)**, an open-source AWS mock server in Docker. Terraform, the `vpc` + `eks` modules and every command are real; only the endpoint is local. No AWS Console screenshot is possible without an account.

A local, git-ignored `provider_override.tf` points the provider at Moto (dummy `test` credentials) and, because Moto doesn't implement them, turns off three things **for the mock only**: the SSM lookup of the latest EKS AMI, the EKS add-ons, and the cluster-creator access entry. That's why the mock plan is 50 resources instead of 56. `main.tf` is unchanged and applies all of them on real AWS.

`terraform plan` — non-empty, no errors:

![plan](docs/screenshots/30-terraform-plan.png)

`terraform apply` (creation lines + outputs):

![apply](docs/screenshots/31-terraform-apply.png)

`terraform output`:

![output](docs/screenshots/32-terraform-output.png)

VPC with **2 public** (+ 2 private) subnets, NAT + Internet Gateway, EKS cluster `ACTIVE`, managed node group `ACTIVE` (min 1 / desired 2 / max 3):

![vpc eks](docs/screenshots/33-vpc-eks-state.png)

`terraform destroy` — 50 destroyed, state empty afterwards:

![destroy](docs/screenshots/34-terraform-destroy.png)
![after destroy](docs/screenshots/35-after-destroy.png)

### Git history
![git log](docs/screenshots/25-git-log.png)

### CI/CD pipeline
Green run on `main`: tests → frontend build → build + Trivy + GHCR push → kind deploy + smoke test ([run](https://github.com/tarun250/hostel_management/actions/runs/38163540967)):

![actions run](docs/screenshots/50-github-actions-run.png)

Trivy step in that run: backend (Debian OS + every Python package) and frontend (Alpine) both report **0** vulnerabilities:

![trivy ci backend](docs/screenshots/27-trivy-ci-backend.png)
![trivy ci backend end](docs/screenshots/28-trivy-ci-backend-end.png)
![trivy ci frontend](docs/screenshots/29-trivy-ci-frontend.png)

GHCR packages, tagged with the commit SHA:

![ghcr backend](docs/screenshots/51-ghcr-backend.png)
![ghcr frontend](docs/screenshots/52-ghcr-frontend.png)

### Kubernetes (minikube)
Deployed with `helm upgrade --install` using the GHCR images:

![pods](docs/screenshots/40-kubectl-get-pods.png)
![svc ingress](docs/screenshots/41-kubectl-get-svc-ingress.png)
![helm list](docs/screenshots/42-helm-list.png)

App through the Ingress at `http://hostelhub.local`:

![ingress](docs/screenshots/43-ingress-browser.png)

### Prometheus + Grafana
ServiceMonitor target, both backend pods `UP`:

![targets](docs/screenshots/45-prometheus-targets.png)

Grafana dashboard with live traffic:

![grafana](docs/screenshots/46-grafana-dashboard.png)

### Argo CD
App `Synced` + `Healthy`, synced to the latest commit on `main`:

![argocd](docs/screenshots/47-argocd-app-synced.png)

### Live demo: commit → pipeline → Argo CD rollout
Rehearsal of the M10 demo ([steps](docs/demo.md)). The Dashboard heading changed in `d603539`, CI went green and pushed the images, `values-gitops.yaml` was bumped to that SHA in `4426111`, and Argo CD rolled the new pods out.

Green run for the change ([run](https://github.com/tarun250/hostel_management/actions/runs/39024547490)):

![demo green run](docs/screenshots/61-demo-green-run.png)

Argo CD synced to the new revision `4426111`:

![demo argocd](docs/screenshots/62-demo-argocd-synced.png)

App before and after (heading "Hostel overview" → "Hostel dashboard"):

![demo before](docs/screenshots/60-demo-before.png)
![demo after](docs/screenshots/63-demo-after.png)

## Known issues and limitations

- **No AWS account.** Terraform `plan`/`apply`/`destroy` ran against the Moto mock, so there is no AWS Console screenshot and the app was never on a real EKS cluster. The Kubernetes demo runs on minikube.
- The Helm release (namespace `hostelhub`) and the Argo CD app (namespace `hostelhub-gitops`) are two copies of the same chart on one minikube. Together with Prometheus and Argo CD they need more than 4 GB of memory, otherwise pods restart on failed probes.
- GitOps tag bumps in `values-gitops.yaml` are manual. CI does not write back to the repo.
- Postgres runs in the cluster as a single-replica StatefulSet. On real AWS it should be RDS (`postgres.enabled=false` + `externalDatabaseUrl`).
- There is no login. The console is meant for one warden on a trusted network.
