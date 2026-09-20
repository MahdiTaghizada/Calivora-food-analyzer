$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
$Tf = Join-Path $ScriptDir "terraform"
$Bootstrap = Join-Path $Tf "bootstrap"

function Invoke-Terraform {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Directory,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & terraform "-chdir=$Directory" @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Terraform command failed in $Directory with exit code $LASTEXITCODE."
    }
}

foreach ($tool in @("terraform", "az", "kubectl", "docker")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "$tool is required and was not found on PATH."
    }
}
if (-not (Test-Path (Join-Path $Tf "terraform.tfvars"))) {
    throw "Copy infrastructure\terraform\terraform.tfvars.example to infrastructure\terraform\terraform.tfvars and fill it in."
}
if (-not (Test-Path (Join-Path $Bootstrap "terraform.tfvars"))) {
    throw "Copy infrastructure\terraform\bootstrap\terraform.tfvars.example to infrastructure\terraform\bootstrap\terraform.tfvars and fill it in."
}

Invoke-Terraform $Bootstrap @("init", "-input=false")
Invoke-Terraform $Bootstrap @("apply", "-auto-approve", "-input=false", "-var-file=terraform.tfvars")
$StateRg = & terraform "-chdir=$Bootstrap" output -raw resource_group_name
$StateStorage = & terraform "-chdir=$Bootstrap" output -raw storage_account_name
$StateContainer = & terraform "-chdir=$Bootstrap" output -raw container_name

@"
terraform {
  backend "azurerm" {
    resource_group_name  = "$StateRg"
    storage_account_name = "$StateStorage"
    container_name       = "$StateContainer"
    key                  = "calivora.tfstate"
  }
}
"@ | Set-Content (Join-Path $Tf "backend.tf")

Invoke-Terraform $Tf @("init", "-upgrade", "-reconfigure", "-input=false")
Invoke-Terraform $Tf @("apply", "-target=module.resource_group", "-target=module.acr", "-auto-approve", "-input=false", "-var-file=terraform.tfvars")
$AcrLoginServer = & terraform "-chdir=$Tf" output -raw acr_login_server
az acr login --name ($AcrLoginServer -split "\.")[0]
docker build -t "$AcrLoginServer/calivora:latest" $Root
docker push "$AcrLoginServer/calivora:latest"
Invoke-Terraform $Tf @("apply", "-auto-approve", "-input=false", "-var-file=terraform.tfvars")

$AksName = & terraform "-chdir=$Tf" output -raw aks_name
$AksRg = & terraform "-chdir=$Tf" output -raw resource_group_name
az aks get-credentials --resource-group $AksRg --name $AksName --overwrite-existing
kubectl -n calivora rollout status deployment/calivora-api --timeout=10m
Write-Host "Deployment complete."
$IngressIp = & terraform "-chdir=$Tf" output -raw ingress_ip
$GrafanaUrl = & terraform "-chdir=$Tf" output -raw grafana_url
Write-Host "Ingress IP: $IngressIp"
Write-Host "Grafana:    $GrafanaUrl"
