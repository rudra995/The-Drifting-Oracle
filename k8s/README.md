# Kubernetes manifests

Deployment + Service pairs for both the backend and frontend, written
against the images built by the repo's `Dockerfile`s. These describe how
the app *would* run on a Kubernetes cluster -- they are not applied to a
live cluster as part of this project (no cluster is provisioned/kept
running for a two-person portfolio project).

## To actually run these somewhere

```bash
# Build and push images to a registry the cluster can pull from, then:
kubectl apply -f k8s/backend-secret.yaml   # copy from backend-secret.example.yaml first, fill in real values
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
```

Local smoke-testing without a real cluster: `kind create cluster` or
`minikube start`, then `kubectl apply -f k8s/` after loading the locally
built images in (`kind load docker-image ...` / `minikube image load ...`).

## Design notes

- Backend readiness/liveness probes hit `/api/health` -- the same
  endpoint the app already exposes for monitoring.
- `envFrom.secretRef` keeps all Databricks/Gemini credentials out of the
  manifest itself, mirroring the `.env` / `.env.example` split used for
  local dev.
- Backend `FRONTEND_ORIGINS` is set to the frontend Service's in-cluster
  DNS name (`http://drifting-oracle-frontend`), not `localhost` -- CORS
  origins need to match how the browser actually reaches the frontend,
  which is via the frontend Service's external LoadBalancer address in
  a real deployment, not the in-cluster name. Update this to match
  whatever hostname the frontend is actually served from.
