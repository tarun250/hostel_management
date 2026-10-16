# Live demo: commit → pipeline → deployment

This is the M10 live demo. A visible UI change goes from a commit to the running cluster through GitHub Actions (test, build, Trivy scan, push to GHCR) and Argo CD (sync). Nobody runs `kubectl apply` or `helm` against the cluster.

Takes about 8 minutes. The CI run takes ~4 of them; Argo CD rolls the pods out in about a minute.

## Before the demo

The cluster must already have Argo CD and the `hostelhub` Application (setup: [`argocd/README.md`](../argocd/README.md)).

```bash
minikube start --driver=docker --memory 3000 --cpus 4   # Argo CD + HostelHub fit in 3 GB
kubectl -n argocd get applications            # hostelhub  Synced  Healthy
kubectl -n hostelhub-gitops get pods          # 2 backend, 2 frontend, postgres Running

# Terminal A: Argo CD UI on https://localhost:8443
kubectl -n argocd port-forward svc/argocd-server 8443:443

# Terminal B: the app on http://localhost:8080
kubectl -n hostelhub-gitops port-forward svc/hostelhub-frontend 8080:80

# Argo CD CLI login (password: see argocd/README.md)
argocd login localhost:8443 --username admin --insecure
```

Open http://localhost:8080 and show the current Dashboard heading, **Hostel dashboard**.

## 1. Make a visible change

In `frontend/src/pages/Dashboard.jsx`, change the `PageHeader` title:

```jsx
<PageHeader title="Hostel dashboard" ...>
```

to something new, for example:

```jsx
<PageHeader title="Hostel dashboard (live demo)" ...>
```

```bash
git add frontend/src/pages/Dashboard.jsx
git commit -m "Show live demo marker in the Dashboard heading"
git push origin main
```

## 2. Wait for the green pipeline

```bash
gh run watch --exit-status                    # pick the run for this commit
SHA=$(git rev-parse HEAD)
echo "$SHA"
```

All four jobs must be green: `Backend lint + tests`, `Frontend build`, `Build, scan (Trivy), push to GHCR`, `Deploy to kind with Helm + smoke test`. The images now exist as `ghcr.io/tarun250/hostelhub-backend:$SHA` and `ghcr.io/tarun250/hostelhub-frontend:$SHA`.

## 3. Point the GitOps values at that SHA

```bash
sed -i.bak "s/tag: .*/tag: $SHA/" helm/hostelhub/values-gitops.yaml && rm helm/hostelhub/values-gitops.yaml.bak
git diff helm/hostelhub/values-gitops.yaml      # only the two image tags change
git commit -am "Deploy ${SHA:0:7} to hostelhub-gitops via Argo CD"
git push origin main
```

This push starts another CI run too. Argo CD doesn't wait for it, because the images for `$SHA` already exist.

## 4. Watch Argo CD roll it out

Start the pod watch in a third terminal first:

```bash
kubectl get pods -n hostelhub-gitops -w
```

Argo CD polls git every ~3 minutes. To skip the wait:

```bash
argocd app get hostelhub --refresh             # Sync Status: OutOfSync from main (<new commit>)
```

New backend and frontend pods start, pass their probes, and the old ones terminate one at a time. Postgres is not touched, so the data stays. Then:

```bash
argocd app get hostelhub                        # Synced to main (<new commit>), Healthy
kubectl -n hostelhub-gitops get deploy -o wide  # IMAGES column ends in :$SHA
```

In the Argo CD UI, the `hostelhub` app shows **Synced to main (<new commit>)** and the new ReplicaSets.

## 5. Show the change

The port-forward in terminal B was bound to an old frontend pod, so stop it and start it again. Then refresh http://localhost:8080. The Dashboard heading shows the new text.

## Rehearsal (16 Oct 2026)

Run once end to end before the presentation: heading `Hostel overview` → `Hostel dashboard` in `d603539`, [green CI run](https://github.com/tarun250/hostel_management/actions/runs/39024547490) in 4m 5s, tags bumped in `4426111`, Argo CD synced and both Deployments rolled within about a minute.

| Before | After |
|---|---|
| ![before](screenshots/60-demo-before.png) | ![after](screenshots/63-demo-after.png) |

![green run](screenshots/61-demo-green-run.png)
![argocd synced](screenshots/62-demo-argocd-synced.png)

## Rolling back

Set `values-gitops.yaml` back to the previous SHA and push. The old images are still in GHCR, so no rebuild is needed.
