output "resource_group_name" {
  value = module.resource_group.name
}

output "aks_name" {
  value = module.aks.name
}

output "acr_login_server" {
  value = module.acr.login_server
}

output "ingress_ip" {
  description = "Public IP exposed by the ingress controller."
  value       = try(data.kubernetes_service.ingress.status[0].load_balancer[0].ingress[0].ip, null)
}

output "grafana_url" {
  value = "http://${try(data.kubernetes_service.ingress.status[0].load_balancer[0].ingress[0].ip, "INGRESS_IP")}/grafana"
}
