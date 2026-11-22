locals {
  crds_chart = {
    repository = "https://prometheus-community.github.io/helm-charts"
    name       = "prometheus-operator-crds"
  }

  helm_values = [{
    # Keep the CRDs on uninstall so a `tofu destroy` of this module does not
    # delete resources owned by the applications that use them.
    annotations = {
      "helm.sh/resource-policy" = "keep"
    }
  }]
}