locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

module "resource_group" {
  source   = "./modules/resource-group"
  name     = "${local.name_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

module "network" {
  source              = "./modules/network"
  resource_group_name = module.resource_group.name
  location            = var.location
  name_prefix         = local.name_prefix
  tags                = local.common_tags
}

module "acr" {
  source              = "./modules/acr"
  resource_group_name = module.resource_group.name
  location            = var.location
  name_prefix         = local.name_prefix
  tags                = local.common_tags
}

module "aks" {
  source              = "./modules/aks"
  resource_group_name = module.resource_group.name
  location            = var.location
  name_prefix         = local.name_prefix
  kubernetes_version  = var.kubernetes_version
  node_vm_size        = var.node_vm_size
  node_min_count      = var.node_min_count
  node_max_count      = var.node_max_count
  subnet_id           = module.network.aks_subnet_id
  acr_id              = module.acr.id
  tags                = local.common_tags
}

provider "kubernetes" {
  host                   = module.aks.host
  client_certificate     = base64decode(module.aks.client_certificate)
  client_key             = base64decode(module.aks.client_key)
  cluster_ca_certificate = base64decode(module.aks.cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = module.aks.host
    client_certificate     = base64decode(module.aks.client_certificate)
    client_key             = base64decode(module.aks.client_key)
    cluster_ca_certificate = base64decode(module.aks.cluster_ca_certificate)
  }
}

resource "kubernetes_namespace_v1" "calivora" {
  metadata { name = "calivora" }
  depends_on = [module.aks]
}

resource "kubernetes_namespace_v1" "monitoring" {
  metadata { name = "monitoring" }
  depends_on = [module.aks]
}

resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  namespace        = "ingress-nginx"
  create_namespace = true
  version          = "4.11.3"
  timeout          = 900
  wait             = true
  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }
}

resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name
  version    = "65.8.1"
  timeout    = 900
  wait       = true
  values     = [file("${path.module}/monitoring/values.yaml")]
  set_sensitive {
    name  = "grafana.adminPassword"
    value = random_password.grafana.result
  }
  depends_on = [kubernetes_namespace_v1.monitoring]
}

resource "kubernetes_secret_v1" "app_config" {
  metadata {
    name      = "calivora-config"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  type = "Opaque"
  data = {
    ANTHROPIC_API_KEY = var.anthropic_api_key
    OPENAI_API_KEY    = var.openai_api_key
    GOOGLE_API_KEY    = var.google_api_key
    USDA_API_KEY      = var.usda_api_key
    DATABASE_URL      = "postgresql://foodanalyzer:${random_password.postgres.result}@postgres:5432/foodanalyzer"
  }
}

resource "kubernetes_config_map_v1" "app_config" {
  metadata {
    name      = "calivora-config"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  data = {
    LLM_PROVIDER       = var.llm_provider
    LLM_MODEL          = var.llm_model
    NUTRITION_PROVIDER = "usda"
    OFFLINE_MODE       = tostring(var.offline_mode)
    CACHE_BACKEND      = "redis"
    REDIS_URL          = "redis://redis:6379/0"
  }
}

resource "kubernetes_secret_v1" "postgres" {
  metadata {
    name      = "postgres-secret"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  data = { POSTGRES_PASSWORD = "change-me-${random_password.postgres.result}" }
  type = "Opaque"
}

resource "random_password" "postgres" {
  length  = 32
  special = false
}

resource "random_password" "grafana" {
  length  = 32
  special = false
}

resource "kubernetes_persistent_volume_claim_v1" "postgres" {
  metadata {
    name      = "postgres-data"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = "managed-csi"
    resources {
      requests = { storage = "10Gi" }
    }
  }
}

resource "kubernetes_deployment_v1" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
    labels    = { app = "postgres" }
  }
  spec {
    replicas = 1
    selector { match_labels = { app = "postgres" } }
    template {
      metadata { labels = { app = "postgres" } }
      spec {
        container {
          name  = "postgres"
          image = "postgres:16-alpine"
          port { container_port = 5432 }
          volume_mount {
            name       = "postgres-data"
            mount_path = "/var/lib/postgresql/data"
          }
          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.postgres.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }
          env {
            name  = "POSTGRES_USER"
            value = "foodanalyzer"
          }
          env {
            name  = "POSTGRES_DB"
            value = "foodanalyzer"
          }
          resources {
            requests = { cpu = "100m", memory = "256Mi" }
            limits   = { cpu = "500m", memory = "1Gi" }
          }
        }
        volume {
          name = "postgres-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.postgres.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  spec {
    selector = { app = "postgres" }
    port {
      port        = 5432
      target_port = 5432
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_deployment_v1" "redis" {
  metadata {
    name      = "redis"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
    labels    = { app = "redis" }
  }
  spec {
    replicas = 1
    selector { match_labels = { app = "redis" } }
    template {
      metadata { labels = { app = "redis" } }
      spec {
        container {
          name  = "redis"
          image = "redis:7-alpine"
          port { container_port = 6379 }
          args = ["redis-server", "--appendonly", "yes"]
          resources {
            requests = { cpu = "50m", memory = "64Mi" }
            limits   = { cpu = "250m", memory = "256Mi" }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "redis" {
  metadata {
    name      = "redis"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  spec {
    selector = { app = "redis" }
    port {
      port        = 6379
      target_port = 6379
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_deployment_v1" "app" {
  metadata {
    name      = "calivora-api"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
    labels    = { app = "calivora-api" }
  }
  spec {
    replicas = 2
    selector { match_labels = { app = "calivora-api" } }
    template {
      metadata {
        labels      = { app = "calivora-api" }
        annotations = { "prometheus.io/scrape" = "true", "prometheus.io/port" = "8000" }
      }
      spec {
        container {
          name              = "api"
          image             = var.app_image != "" ? var.app_image : "${module.acr.login_server}/calivora:latest"
          image_pull_policy = var.app_image != "" ? "IfNotPresent" : "Always"
          port { container_port = 8000 }
          env_from {
            config_map_ref { name = kubernetes_config_map_v1.app_config.metadata[0].name }
          }
          env_from {
            secret_ref { name = kubernetes_secret_v1.app_config.metadata[0].name }
          }
          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.postgres.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }
          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 15
            period_seconds        = 10
          }
          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 20
          }
          resources {
            requests = { cpu = "250m", memory = "512Mi" }
            limits   = { cpu = "1", memory = "1Gi" }
          }
        }
      }
    }
  }
  depends_on = [kubernetes_deployment_v1.postgres, kubernetes_deployment_v1.redis]
}

resource "kubernetes_service_v1" "app" {
  metadata {
    name      = "calivora-api"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
  }
  spec {
    selector = { app = "calivora-api" }
    port {
      port        = 80
      target_port = 8000
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_ingress_v1" "app" {
  metadata {
    name      = "calivora"
    namespace = kubernetes_namespace_v1.calivora.metadata[0].name
    annotations = {
      "nginx.ingress.kubernetes.io/proxy-body-size" = "10m"
      "nginx.ingress.kubernetes.io/rewrite-target"  = "/"
    }
  }
  spec {
    ingress_class_name = "nginx"
    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service_v1.app.metadata[0].name
              port { number = 80 }
            }
          }
        }
      }
    }
  }
  depends_on = [helm_release.ingress_nginx]
}

data "kubernetes_service" "ingress" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = "ingress-nginx"
  }
  depends_on = [helm_release.ingress_nginx]
}
