#!/usr/bin/env python3
"""Generate the Grafana dashboards shipped by the kube-prometheus-stack module.

Run from the module root:

    python3 tools/generate_dashboards.py

The generated JSON is committed, so the chart has no Python dependency at
deploy time. Edit this script and re-run it instead of hand-editing the JSON.

Dashboards are split in two groups:

  CORE      — one per application deployed by examples/*/main.tf, plus the
              stack-wide views. Always enabled, because those applications are
              always present and kube-prometheus-stack is installed after them.
  OPTIONAL  — one per application from examples/*/apps.tf. Enabled by the
              caller through the `dashboards` variable, since those apps are
              not always deployed.
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "charts" / "kube-prometheus-stack" / "dashboards"

DS = {"type": "prometheus", "uid": "${datasource}"}


# --------------------------------------------------------------------------
# Panel helpers
# --------------------------------------------------------------------------
def templating(extra=None):
    variables = [
        {
            "current": {},
            "hide": 0,
            "includeAll": False,
            "label": "Datasource",
            "multi": False,
            "name": "datasource",
            "options": [],
            "query": "prometheus",
            "refresh": 1,
            "regex": "",
            "skipUrlSync": False,
            "type": "datasource",
        }
    ]
    if extra:
        variables.extend(extra)
    return {"list": variables}


def ns_variable():
    return {
        "current": {},
        "datasource": DS,
        "definition": "label_values(kube_pod_info, namespace)",
        "hide": 0,
        "includeAll": True,
        "allValue": ".*",
        "label": "Namespace",
        "multi": True,
        "name": "namespace",
        "options": [],
        "query": {"query": "label_values(kube_pod_info, namespace)", "refId": "var-namespace"},
        "refresh": 2,
        "regex": "",
        "skipUrlSync": False,
        "sort": 1,
        "type": "query",
    }


def target(expr, legend="", ref="A", instant=False):
    t = {"datasource": DS, "expr": expr, "refId": ref, "editorMode": "code", "range": not instant}
    if legend:
        t["legendFormat"] = legend
    if instant:
        t["instant"] = True
        t["range"] = False
    return t


def ts(title, targets, x, y, w=12, h=8, unit="short", desc="", stack=False, fill=10):
    return {
        "type": "timeseries",
        "title": title,
        "description": desc,
        "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "lineWidth": 2,
                    "fillOpacity": fill,
                    "showPoints": "never",
                    "spanNulls": True,
                    "stacking": {"mode": "normal" if stack else "none", "group": "A"},
                    "axisPlacement": "auto",
                },
                "color": {"mode": "palette-classic"},
            },
            "overrides": [],
        },
        "options": {
            "legend": {"displayMode": "table", "placement": "bottom",
                       "calcs": ["mean", "max", "lastNotNull"]},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
        "targets": targets,
    }


def stat(title, targets, x, y, w=4, h=4, unit="short", desc="", thresholds=None):
    steps = thresholds or [{"color": "green", "value": None}]
    return {
        "type": "stat",
        "title": title,
        "description": desc,
        "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": steps},
                "mappings": [],
            },
            "overrides": [],
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "auto",
            "orientation": "auto",
            "textMode": "auto",
            "wideLayout": True,
        },
        "targets": targets,
    }


def gauge(title, targets, x, y, w=6, h=6, unit="percent", desc="", thresholds=None):
    steps = thresholds or [
        {"color": "green", "value": None},
        {"color": "#EAB839", "value": 70},
        {"color": "red", "value": 85},
    ]
    return {
        "type": "gauge",
        "title": title,
        "description": desc,
        "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "min": 0,
                "max": 100,
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": steps},
            },
            "overrides": [],
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
        },
        "targets": targets,
    }


def table(title, targets, x, y, w=24, h=8, desc="", unit="short"):
    return {
        "type": "table",
        "title": title,
        "description": desc,
        "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "custom": {"align": "auto", "cellOptions": {"type": "auto"}, "inspect": False},
            },
            "overrides": [],
        },
        "options": {
            "showHeader": True,
            "sortBy": [{"displayName": "Value", "desc": True}],
            "footer": {"show": False, "reducer": ["sum"], "fields": ""},
        },
        "transformations": [],
        "targets": targets,
    }


def dashboard(uid, title, panels, description="", tags=None, variables=None):
    return {
        "__inputs": [],
        "__requires": [],
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard",
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": tags or ["modern-gitops-stack"],
        "templating": templating(variables),
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": title,
        "description": description,
        "uid": uid,
        "version": 1,
        "weekStart": "",
    }


def write(name, dash):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dash, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {name}.json ({len(dash['panels'])} panels)")


# --------------------------------------------------------------------------
# Stack-wide views (CORE)
# --------------------------------------------------------------------------
def build_stack_overview():
    ns = ns_variable()
    panels = [
        stat("Nodes Ready",
             [target('count(kube_node_status_condition{condition="Ready",status="true"})', "ready", instant=True)],
             0, 0, w=4, h=4, desc="Nodes reporting Ready.",
             thresholds=[{"color": "red", "value": None}, {"color": "green", "value": 1}]),
        stat("Namespaces",
             [target("count(count by (namespace) (kube_pod_info))", "namespaces", instant=True)],
             4, 0, w=4, h=4, desc="Namespaces currently running pods."),
        stat("Pods Running",
             [target('sum(kube_pod_status_phase{phase="Running"} == 1)', "running", instant=True)],
             8, 0, w=4, h=4, desc="Pods in the Running phase.",
             thresholds=[{"color": "red", "value": None}, {"color": "green", "value": 1}]),
        stat("Pods Not Running",
             [target('sum(kube_pod_status_phase{phase=~"Pending|Failed|Unknown"} == 1)', "bad", instant=True)],
             12, 0, w=4, h=4, desc="Pods Pending, Failed or Unknown. Should normally be 0.",
             thresholds=[{"color": "green", "value": None}, {"color": "#EAB839", "value": 1},
                         {"color": "red", "value": 5}]),
        stat("Container Restarts",
             [target("sum(increase(kube_pod_container_status_restarts_total[$__range]))", "restarts", instant=True)],
             16, 0, w=4, h=4, desc="Total container restarts in the selected range.",
             thresholds=[{"color": "green", "value": None}, {"color": "#EAB839", "value": 5},
                         {"color": "red", "value": 20}]),
        stat("OOMKilled",
             [target('sum(increase(kube_pod_container_status_terminated_reason{reason="OOMKilled"}[$__range]))',
                     "oom", instant=True)],
             20, 0, w=4, h=4, desc="Containers killed for exceeding their memory limit.",
             thresholds=[{"color": "green", "value": None}, {"color": "red", "value": 1}]),

        ts("CPU usage by namespace",
           [target('sum by (namespace) (rate(container_cpu_usage_seconds_total{namespace=~"$namespace",container!=""}[5m]))',
                   "{{namespace}}")],
           0, 4, w=12, h=8, unit="cores", desc="CPU cores consumed per namespace.", stack=True),
        ts("Memory usage by namespace",
           [target('sum by (namespace) (container_memory_working_set_bytes{namespace=~"$namespace",container!=""})',
                   "{{namespace}}")],
           12, 4, w=12, h=8, unit="bytes", desc="Working set memory per namespace.", stack=True),

        ts("Pods by phase",
           [target('sum by (phase) (kube_pod_status_phase{namespace=~"$namespace"} == 1)', "{{phase}}")],
           0, 12, w=8, h=7, desc="Pod count per lifecycle phase."),
        ts("Restarts by namespace",
           [target('sum by (namespace) (increase(kube_pod_container_status_restarts_total{namespace=~"$namespace"}[1h]))',
                   "{{namespace}}")],
           8, 12, w=8, h=7, desc="Container restarts over the last hour per namespace."),
        ts("Pods waiting for a reason",
           [target('sum by (reason) (kube_pod_container_status_waiting_reason{namespace=~"$namespace"})', "{{reason}}")],
           16, 12, w=8, h=7,
           desc="Containers stuck waiting, grouped by reason (CrashLoopBackOff, ImagePullBackOff, ...)."),

        table("Pods not Running or with restarts",
              [target('kube_pod_status_phase{namespace=~"$namespace",phase!="Running"} == 1 or '
                      'kube_pod_container_status_restarts_total{namespace=~"$namespace"} > 0',
                      "{{namespace}} / {{pod}}", instant=True)],
              0, 19, w=24, h=9,
              desc="Quick triage list: pods that are not Running or that restarted at least once."),
    ]
    return dashboard(
        "mg-stack-overview", "Modern GitOps Stack — Overview", panels,
        description="Entry point for the stack: cluster capacity, workload health and the namespaces that need attention.",
        tags=["modern-gitops-stack", "overview"], variables=[ns],
    )


def build_cluster():
    panels = [
        gauge("CPU utilisation",
              [target('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', "cpu", instant=True)],
              0, 0, w=6, h=7, desc="Average CPU busy percentage across all nodes."),
        gauge("Memory utilisation",
              [target("(1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes)) * 100",
                      "mem", instant=True)],
              6, 0, w=6, h=7, desc="Memory in use across all nodes."),
        gauge("Filesystem utilisation (/)",
              [target('max((1 - node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / '
                      'node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}) * 100)',
                      "disk", instant=True)],
              12, 0, w=6, h=7, desc="Worst-case root filesystem usage. This stack fills disks quickly."),
        stat("Allocatable CPU",
             [target('sum(kube_node_status_allocatable{resource="cpu"})', "cpu", instant=True)],
             18, 0, w=3, h=7, unit="cores", desc="Total allocatable CPU cores."),
        stat("Allocatable memory",
             [target('sum(kube_node_status_allocatable{resource="memory"})', "mem", instant=True)],
             21, 0, w=3, h=7, unit="bytes", desc="Total allocatable memory."),

        ts("CPU usage per node",
           [target('100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', "{{instance}}")],
           0, 7, w=12, h=8, unit="percent", desc="Busy CPU percentage per node."),
        ts("Memory usage per node",
           [target("(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100", "{{instance}}")],
           12, 7, w=12, h=8, unit="percent", desc="Used memory percentage per node."),

        ts("Filesystem usage per node",
           [target('(1 - node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / '
                   'node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}) * 100', "{{instance}}")],
           0, 15, w=12, h=8, unit="percent",
           desc="Root filesystem usage. Above 85% the cluster starts evicting pods."),
        ts("Disk I/O per node",
           [target('sum by (instance) (rate(node_disk_read_bytes_total[5m]))', "{{instance}} read", ref="A"),
            target('sum by (instance) (rate(node_disk_written_bytes_total[5m]))', "{{instance}} write", ref="B")],
           12, 15, w=12, h=8, unit="Bps", desc="Read and write throughput per node."),

        ts("Network throughput per node",
           [target('sum by (instance) (rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br.*"}[5m]))',
                   "{{instance}} rx", ref="A"),
            target('sum by (instance) (rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|br.*"}[5m]))',
                   "{{instance}} tx", ref="B")],
           0, 23, w=12, h=8, unit="Bps",
           desc="Network traffic per node, loopback and virtual interfaces excluded."),
        ts("Load average per node",
           [target('node_load1', "{{instance}} 1m", ref="A"),
            target('node_load5', "{{instance}} 5m", ref="B")],
           12, 23, w=12, h=8, desc="Unix load average. Compare against the node CPU count."),

        ts("PVC capacity by namespace",
           [target('sum by (namespace) (kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace=~".+"})',
                   "{{namespace}}")],
           0, 31, w=12, h=8, unit="bytes", desc="Requested storage per namespace. Watch this on a small disk."),
        ts("PVCs not Bound",
           [target('sum by (namespace) (kube_persistentvolumeclaim_status_phase{phase!="Bound"})', "{{namespace}}")],
           12, 31, w=12, h=8, desc="PVCs stuck Pending. Usually a StorageClass or capacity problem."),
    ]
    return dashboard(
        "mg-cluster", "Modern GitOps Stack — Cluster", panels,
        description="Node-level capacity: CPU, memory, disk, network and persistent volume usage.",
        tags=["modern-gitops-stack", "cluster"],
    )


def build_workloads():
    ns = ns_variable()
    panels = [
        table("Deployments not fully available",
              [target('(kube_deployment_spec_replicas{namespace=~"$namespace"} - '
                      'kube_deployment_status_replicas_available{namespace=~"$namespace"}) > 0',
                      "{{namespace}} / {{deployment}}", instant=True)],
              0, 0, w=12, h=8, desc="Deployments where available replicas are below the desired count."),
        table("StatefulSets not fully ready",
              [target('(kube_statefulset_replicas{namespace=~"$namespace"} - '
                      'kube_statefulset_status_replicas_ready{namespace=~"$namespace"}) > 0',
                      "{{namespace}} / {{statefulset}}", instant=True)],
              12, 0, w=12, h=8, desc="StatefulSets where ready replicas are below the desired count."),

        ts("CPU by workload",
           [target('sum by (namespace, pod) (rate(container_cpu_usage_seconds_total{namespace=~"$namespace",container!=""}[5m]))',
                   "{{namespace}}/{{pod}}")],
           0, 8, w=12, h=9, unit="cores", desc="CPU per pod. Use it to spot noisy neighbours."),
        ts("Memory by workload",
           [target('sum by (namespace, pod) (container_memory_working_set_bytes{namespace=~"$namespace",container!=""})',
                   "{{namespace}}/{{pod}}")],
           12, 8, w=12, h=9, unit="bytes", desc="Working set memory per pod."),

        ts("CPU throttling",
           [target('sum by (namespace, pod) (rate(container_cpu_cfs_throttled_periods_total{namespace=~"$namespace"}[5m])) / '
                   'sum by (namespace, pod) (rate(container_cpu_cfs_periods_total{namespace=~"$namespace"}[5m])) * 100',
                   "{{namespace}}/{{pod}}")],
           0, 17, w=12, h=8, unit="percent",
           desc="Percentage of throttled CFS periods. Sustained values mean the CPU limit is too low."),
        ts("Container restarts",
           [target('sum by (namespace, pod) (increase(kube_pod_container_status_restarts_total{namespace=~"$namespace"}[1h]))',
                   "{{namespace}}/{{pod}}")],
           12, 17, w=12, h=8, desc="Restarts in the last hour per pod."),

        ts("Pods Pending by namespace",
           [target('sum by (namespace) (kube_pod_status_phase{phase="Pending"} == 1)', "{{namespace}}")],
           0, 25, w=8, h=7,
           desc="Pending pods. On a small node this usually means CPU or memory pressure."),
        ts("Failed jobs (1h)",
           [target('sum by (namespace) (increase(kube_job_status_failed[1h]))', "{{namespace}}")],
           8, 25, w=8, h=7, desc="Jobs that failed in the last hour."),
        ts("Container OOMKilled (1h)",
           [target('sum by (namespace, pod) (increase(kube_pod_container_status_terminated_reason{reason="OOMKilled"}[1h]))',
                   "{{namespace}}/{{pod}}")],
           16, 25, w=8, h=7, desc="Containers killed for exceeding their memory limit."),
    ]
    return dashboard(
        "mg-workloads", "Modern GitOps Stack — Workloads", panels,
        description="Deployment and StatefulSet health, resource consumption and restart reasons across namespaces.",
        tags=["modern-gitops-stack", "workloads"], variables=[ns],
    )


# --------------------------------------------------------------------------
# Per-application dashboards
# --------------------------------------------------------------------------
def app_dashboard(uid, title, namespaces, description="", pods_regex=".*", extra_panels=None):
    """Dashboard scoped to one application.

    The first nine panels use kube-state-metrics and cAdvisor series that exist
    for any workload, so they are populated regardless of whether the
    application exports its own metrics.
    """
    ns_re = "|".join(namespaces)
    base = f'namespace=~"{ns_re}",pod=~"{pods_regex}"'
    panels = [
        stat("Pods Running",
             [target(f'sum(kube_pod_status_phase{{{base},phase="Running"}} == 1)', "running", instant=True)],
             0, 0, w=4, h=4,
             thresholds=[{"color": "red", "value": None}, {"color": "green", "value": 1}]),
        stat("Pods Not Running",
             [target(f'sum(kube_pod_status_phase{{{base},phase=~"Pending|Failed|Unknown"}} == 1)', "bad", instant=True)],
             4, 0, w=4, h=4,
             thresholds=[{"color": "green", "value": None}, {"color": "#EAB839", "value": 1},
                         {"color": "red", "value": 3}]),
        stat("Restarts (1h)",
             [target(f"sum(increase(kube_pod_container_status_restarts_total{{{base}}}[1h]))", "restarts", instant=True)],
             8, 0, w=4, h=4,
             thresholds=[{"color": "green", "value": None}, {"color": "#EAB839", "value": 3},
                         {"color": "red", "value": 10}]),
        stat("CPU",
             [target(f'sum(rate(container_cpu_usage_seconds_total{{{base},container!=""}}[5m]))', "cpu", instant=True)],
             12, 0, w=6, h=4, unit="cores"),
        stat("Memory",
             [target(f'sum(container_memory_working_set_bytes{{{base},container!=""}})', "mem", instant=True)],
             18, 0, w=6, h=4, unit="bytes"),

        ts("CPU by pod",
           [target(f'sum by (pod) (rate(container_cpu_usage_seconds_total{{{base},container!=""}}[5m]))', "{{pod}}")],
           0, 4, w=12, h=8, unit="cores", desc="CPU per pod of this application."),
        ts("Memory by pod",
           [target(f'sum by (pod) (container_memory_working_set_bytes{{{base},container!=""}})', "{{pod}}")],
           12, 4, w=12, h=8, unit="bytes", desc="Working set memory per pod of this application."),

        ts("Network throughput",
           [target(f'sum(rate(container_network_receive_bytes_total{{{base}}}[5m]))', "receive", ref="A"),
            target(f'sum(rate(container_network_transmit_bytes_total{{{base}}}[5m]))', "transmit", ref="B")],
           0, 12, w=12, h=8, unit="Bps", desc="Network traffic for this application's pods."),
        ts("Restarts by pod",
           [target(f'sum by (pod) (increase(kube_pod_container_status_restarts_total{{{base}}}[1h]))', "{{pod}}")],
           12, 12, w=12, h=8, desc="Restarts in the last hour."),
    ]
    if extra_panels:
        panels.extend(extra_panels)
    panels.append(table(
        "Pods",
        [target(f'kube_pod_status_phase{{namespace=~"{ns_re}",pod=~"{pods_regex}"}} == 1',
                "{{namespace}} / {{pod}}", instant=True)],
        0, 20, w=24, h=8, desc="Pod status overview for this application.",
    ))
    return dashboard(uid, title, panels, description=description,
                     tags=["modern-gitops-stack", "application"])


# --------------------------------------------------------------------------
# CORE dashboards: one per application in examples/*/main.tf (except Argo CD,
# which ships its own dashboard from its own module).
# --------------------------------------------------------------------------
def build_core():
    write("stack-overview", build_stack_overview())
    write("cluster", build_cluster())
    write("workloads", build_workloads())

    write("kube-prometheus-stack", app_dashboard(
        "mg-kube-prometheus-stack", "Modern GitOps Stack — Prometheus Stack",
        ["kube-prometheus-stack"],
        description="Prometheus, Alertmanager, Grafana, the Operator and kube-state-metrics."))
    write("cert-manager", app_dashboard(
        "mg-cert-manager", "Modern GitOps Stack — cert-manager", ["cert-manager"],
        description="cert-manager controller, webhook and cainjector health."))
    write("metrics-server", app_dashboard(
        "mg-metrics-server", "Modern GitOps Stack — Metrics Server", ["kube-system"],
        pods_regex="metrics-server.*",
        description="Metrics Server health, source of the HPA and kubectl top metrics."))
    write("metallb", app_dashboard(
        "mg-metallb", "Modern GitOps Stack — MetalLB", ["metallb-system"],
        description="MetalLB controller and speaker, which provide the LoadBalancer IPs."))
    write("istio", app_dashboard(
        "mg-istio", "Modern GitOps Stack — Istio", ["istio-system"],
        description="Istio control plane: istiod, ingress gateway, ztunnel and CNI."))
    write("kiali", app_dashboard(
        "mg-kiali", "Modern GitOps Stack — Kiali", ["istio-system"], pods_regex="kiali.*",
        description="Kiali service mesh console and its operator."))
    write("traefik", app_dashboard(
        "mg-traefik", "Modern GitOps Stack — Traefik", ["management"], pods_regex="traefik.*",
        description="Traefik ingress controller traffic and health."))
    write("keycloak", app_dashboard(
        "mg-keycloak", "Modern GitOps Stack — Keycloak", ["management"], pods_regex="keycloak.*",
        description="Keycloak identity provider health and resource usage."))
    write("postgresql", app_dashboard(
        "mg-postgresql", "Modern GitOps Stack — PostgreSQL", ["database"],
        description="PostgreSQL health, plus connections and transactions when postgres_exporter is enabled.",
        extra_panels=[
            ts("Database connections",
               [target('pg_stat_database_numbackends{namespace="database"}', "{{datname}}")],
               0, 20, w=12, h=8, desc="Active backends per database (needs postgres_exporter)."),
            ts("Transactions per second",
               [target('rate(pg_stat_database_xact_commit{namespace="database"}[5m])', "{{datname}} commit", ref="A"),
                target('rate(pg_stat_database_xact_rollback{namespace="database"}[5m])', "{{datname}} rollback", ref="B")],
               12, 20, w=12, h=8, desc="Commit and rollback rate (needs postgres_exporter)."),
        ]))
    write("minio", app_dashboard(
        "mg-minio", "Modern GitOps Stack — MinIO", ["minio"],
        description="MinIO object storage, plus S3 traffic when MinIO metrics are enabled.",
        extra_panels=[
            ts("S3 request rate",
               [target('sum by (api) (rate(minio_s3_requests_total{namespace="minio"}[5m]))', "{{api}}")],
               0, 20, w=12, h=8, desc="S3 API requests per second (needs MinIO metrics)."),
            ts("Bucket usage",
               [target('minio_bucket_usage_total_bytes{namespace="minio"}', "{{bucket}}")],
               12, 20, w=12, h=8, unit="bytes", desc="Bytes stored per bucket (needs MinIO metrics)."),
        ]))
    write("loki", app_dashboard(
        "mg-loki", "Modern GitOps Stack — Loki", ["loki-stack"],
        description="Loki distributor, ingester, querier and Promtail."))
    write("thanos", app_dashboard(
        "mg-thanos", "Modern GitOps Stack — Thanos", ["thanos"],
        description="Thanos query, store, compactor and object storage uploads.",
        extra_panels=[
            ts("Last successful object storage upload",
               [target('thanos_objstore_bucket_last_successful_upload_time{namespace="thanos"}', "{{bucket}}")],
               0, 20, w=12, h=8, unit="s", desc="Timestamp of the last successful upload per bucket."),
            ts("Query request rate",
               [target('sum by (handler) (rate(thanos_query_http_requests_total{namespace="thanos"}[5m]))', "{{handler}}")],
               12, 20, w=12, h=8, desc="Thanos Query requests per second."),
        ]))


# --------------------------------------------------------------------------
# OPTIONAL dashboards: one per application in examples/*/apps.tf.
# --------------------------------------------------------------------------
def build_optional():
    write("kafka", app_dashboard(
        "mg-kafka", "Modern GitOps Stack — Kafka", ["ingestion"],
        description="Strimzi Kafka brokers, entity operator and Cruise Control.",
        extra_panels=[
            ts("Messages in per topic",
               [target('sum by (topic) (rate(kafka_topic_partition_current_offset{namespace="ingestion"}[5m]))', "{{topic}}")],
               0, 20, w=12, h=8, desc="Produced messages per second per topic (needs kafka-exporter)."),
            ts("Consumer lag",
               [target('sum by (consumergroup) (kafka_consumergroup_lag{namespace="ingestion"})', "{{consumergroup}}")],
               12, 20, w=12, h=8, desc="Consumer group lag (needs kafka-exporter)."),
        ]))
    write("kafka-ui", app_dashboard(
        "mg-kafka-ui", "Modern GitOps Stack — Kafka UI", ["ingestion"], pods_regex="kafka-ui.*",
        description="Kafka UI web console."))
    write("schema-registry", app_dashboard(
        "mg-schema-registry", "Modern GitOps Stack — Schema Registry", ["ingestion"],
        pods_regex="schema-registry.*",
        description="Confluent Schema Registry and its oauth2-proxy sidecar."))
    write("zookeeper", app_dashboard(
        "mg-zookeeper", "Modern GitOps Stack — ZooKeeper", ["zookeeper"],
        description="ZooKeeper ensemble used by NiFi."))
    write("nifi", app_dashboard(
        "mg-nifi", "Modern GitOps Stack — NiFi", ["nifi"],
        description="NiFi cluster nodes and the NiFiKop operator."))
    write("pinot", app_dashboard(
        "mg-pinot", "Modern GitOps Stack — Pinot", ["datastore"],
        description="Pinot controller, broker, server, minion and its ZooKeeper."))
    write("trino", app_dashboard(
        "mg-trino", "Modern GitOps Stack — Trino", ["processing"], pods_regex="trino.*",
        description="Trino coordinator and workers."))
    write("spark", app_dashboard(
        "mg-spark", "Modern GitOps Stack — Spark", ["processing"], pods_regex="spark.*",
        description="Spark operator and Spark application pods."))
    write("hive-metastore", app_dashboard(
        "mg-hive-metastore", "Modern GitOps Stack — Hive Metastore", ["metastore"],
        description="Hive Metastore service and its schema initialisation jobs."))
    write("kuberay", app_dashboard(
        "mg-kuberay", "Modern GitOps Stack — KubeRay", ["mlops"],
        description="KubeRay operator and Ray cluster head/worker pods."))
    write("airflow", app_dashboard(
        "mg-airflow", "Modern GitOps Stack — Airflow", ["orchestrator"],
        description="Airflow scheduler, workers, triggerer, DAG processor and API server."))
    write("jupyterhub", app_dashboard(
        "mg-jupyterhub", "Modern GitOps Stack — JupyterHub", ["jupyterhub"],
        description="JupyterHub hub, proxy, user scheduler and single-user servers."))
    write("mlflow", app_dashboard(
        "mg-mlflow", "Modern GitOps Stack — MLflow", ["mlflow"],
        description="MLflow tracking server and its oauth2-proxy sidecar."))
    write("qdrant", app_dashboard(
        "mg-qdrant", "Modern GitOps Stack — Qdrant", ["qdrant"],
        description="Qdrant vector database cluster."))


if __name__ == "__main__":
    print("== core ==")
    build_core()
    print("== optional ==")
    build_optional()