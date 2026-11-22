resource "null_resource" "dependencies" {
  triggers = var.dependency_ids
}

data "utils_deep_merge_yaml" "values" {
  input = [for i in concat(local.helm_values, var.helm_values) : yamlencode(i)]
}

# The Prometheus Operator CRDs (ServiceMonitor, PodMonitor, PrometheusRule,
# Prometheus, Alertmanager, ...) must exist before any module creates one of
# those objects. Applications such as cert-manager, which are installed before
# kube-prometheus-stack, would otherwise fail on the first apply because their
# ServiceMonitor has no CRD yet.
#
# Installing them here, ahead of everything else, lets every module enable its
# ServiceMonitor from the very first apply. The main kube-prometheus-stack
# chart is configured with `crds.enabled=false` so there is a single owner for
# these objects.
resource "helm_release" "crds" {
  name       = "prometheus-operator-crds"
  repository = local.crds_chart.repository
  chart      = local.crds_chart.name
  version    = var.crds_chart_version

  namespace        = "kube-system"
  create_namespace = false
  atomic           = true
  timeout          = 600

  values = [data.utils_deep_merge_yaml.values.output]

  depends_on = [
    resource.null_resource.dependencies,
  ]

  lifecycle {
    # The chart only contains CRDs. Ignore drift on them so an external schema
    # change (for example an operator upgrade done out of band) does not make
    # every plan noisy.
    ignore_changes = [values]
  }
}

resource "null_resource" "this" {
  depends_on = [
    resource.helm_release.crds,
  ]
}