#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$ROOT_DIR/terraform"
BOOTSTRAP_DIR="$TF_DIR/bootstrap"

command -v terraform >/dev/null || { echo "terraform is required."; exit 1; }
command -v az >/dev/null || { echo "Azure CLI (az) is required."; exit 1; }
command -v kubectl >/dev/null || { echo "kubectl is required."; exit 1; }
command -v docker >/dev/null || { echo "Docker is required to build the API image."; exit 1; }

test -f "$TF_DIR/terraform.tfvars" || {
  echo "Copy terraform/terraform.tfvars.example to terraform/terraform.tfvars and fill it in."
  exit 1
}
test -f "$BOOTSTRAP_DIR/terraform.tfvars" || {
  echo "Copy terraform/bootstrap/terraform.tfvars.example to terraform/bootstrap/terraform.tfvars and fill it in."
  exit 1
}

terraform -chdir="$BOOTSTRAP_DIR" init -input=false
terraform -chdir="$BOOTSTRAP_DIR" apply -auto-approve -input=false \
  -var-file=terraform.tfvars

STATE_RG="$(terraform -chdir="$BOOTSTRAP_DIR" output -raw resource_group_name)"
STATE_STORAGE="$(terraform -chdir="$BOOTSTRAP_DIR" output -raw storage_account_name)"
STATE_CONTAINER="$(terraform -chdir="$BOOTSTRAP_DIR" output -raw container_name)"

cat > "$TF_DIR/backend.tf" <<EOF
terraform {
  backend "azurerm" {
    resource_group_name  = "$STATE_RG"
    storage_account_name = "$STATE_STORAGE"
    container_name       = "$STATE_CONTAINER"
    key                  = "calivora.tfstate"
  }
}
EOF

terraform -chdir="$TF_DIR" init -upgrade -input=false
terraform -chdir="$TF_DIR" apply -target=module.resource_group -target=module.acr \
  -auto-approve -input=false -var-file=terraform.tfvars

ACR_LOGIN_SERVER="$(terraform -chdir="$TF_DIR" output -raw acr_login_server)"
az acr login --name "${ACR_LOGIN_SERVER%%.*}"
docker build -t "$ACR_LOGIN_SERVER/calivora:latest" "$ROOT_DIR"
docker push "$ACR_LOGIN_SERVER/calivora:latest"

terraform -chdir="$TF_DIR" apply -auto-approve -input=false -var-file=terraform.tfvars

AKS_NAME="$(terraform -chdir="$TF_DIR" output -raw aks_name)"
AKS_RG="$(terraform -chdir="$TF_DIR" output -raw resource_group_name)"
az aks get-credentials --resource-group "$AKS_RG" --name "$AKS_NAME" --overwrite-existing
kubectl -n calivora rollout status deployment/calivora-api --timeout=10m

echo "Deployment complete."
echo "Ingress IP: $(terraform -chdir="$TF_DIR" output -raw ingress_ip)"
echo "Grafana:    $(terraform -chdir="$TF_DIR" output -raw grafana_url)"
