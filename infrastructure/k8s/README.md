# Kubernetes workload ownership

The Kubernetes workloads are intentionally declared in
[`terraform/main.tf`](../terraform/main.tf) rather than duplicated as raw YAML.
This keeps the AKS credentials, ACR pull role, secrets, service dependencies,
ingress, and Helm releases in one reproducible `terraform apply`.

The following independent Deployment + ClusterIP Service pairs are created:

- `calivora-api` (the FastAPI API and frontend)
- `postgres` (PostgreSQL 16 with a managed CSI volume)
- `redis` (Redis 7)

The NGINX ingress controller exposes the API and frontend through one public
Azure LoadBalancer IP. Prometheus and Grafana are installed by Terraform's Helm
provider in the `monitoring` namespace.
