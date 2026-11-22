#######################
## Standard variables
#######################

variable "helm_values" {
  description = "Helm chart value overrides for the CRD chart. They should be passed as a list of HCL structures."
  type        = any
  default     = []
}

variable "dependency_ids" {
  description = "IDs of the other modules on which this module depends on."
  type        = map(string)
  default     = {}
}

variable "crds_chart_version" {
  description = <<-EOT
    Version of the `prometheus-operator-crds` chart.

    IMPORTANT: this must stay aligned with the Prometheus Operator version
    bundled by the `kube-prometheus-stack` chart used by this module. The CRDs
    are created here and the main chart skips them (`crds.enabled=false`), so a
    mismatch means the operator would run against an older schema.

    Chart 33.0.2 ships the CRDs of Prometheus Operator v0.95.2, which is what
    kube-prometheus-stack 93.7.0 bundles.
  EOT
  type        = string
  default     = "33.0.2"
}
