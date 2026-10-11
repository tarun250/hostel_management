# Argo CD (GitOps)

Argo CD watches `helm/hostelhub` on `main` and keeps the `hostelhub-gitops` namespace in sync with it, using `values-gitops.yaml`.

## Setup

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deploy/argocd-server

# DB secret, created by hand so the password never goes into git
kubectl create namespace hostelhub-gitops
kubectl -n hostelhub-gitops create secret generic hostelhub-db \
  --from-literal=POSTGRES_USER=hostelhub \
  --from-literal=POSTGRES_PASSWORD=<password> \
  --from-literal=DATABASE_URL=postgresql+psycopg://hostelhub:<password>@hostelhub-postgres:5432/hostelhub

kubectl apply -f argocd/application.yaml
kubectl -n argocd get applications
```

UI: `kubectl -n argocd port-forward svc/argocd-server 8443:443`, user `admin`, password from
`kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d`.

## GitOps flow

1. Push code to `main` → CI tests, scans and pushes `ghcr.io/tarun250/hostelhub-*:<sha>`.
2. Set that `<sha>` as the image tags in `helm/hostelhub/values-gitops.yaml` and push.
3. Argo CD sees the new commit, renders the chart and rolls the Deployments to the new images. Nobody runs `kubectl` or `helm` against the cluster.
4. `selfHeal` reverts manual changes in the cluster; `prune` deletes resources removed from git.
