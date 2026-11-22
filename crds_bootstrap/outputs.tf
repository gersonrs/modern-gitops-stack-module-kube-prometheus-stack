output "id" {
  description = "ID to pass other modules in order to refer to this module as a dependency."
  value       = resource.null_resource.this.id
}

output "crds_chart_version" {
  description = "Version of the prometheus-operator-crds chart that was installed."
  value       = var.crds_chart_version
}