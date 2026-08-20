#!/usr/bin/env bash
# diag-k8s-resource.sh — K8s resource deep-dive (namespace optional, fuzzy match)
set -uo pipefail

usage() {
    echo "usage: $0 <resource-type> <pattern> [namespace]"
    echo "  resource-type: pod | deployment | daemonset | statefulset | service"
    echo "  pattern:       fuzzy name match (e.g. 'haproxy', 'coredns')"
    echo "  namespace:     optional, search all namespaces if omitted or empty"
    echo ""
    echo "output: $OUTDIR/k8s-resources/<type>-<ns>-<name>/"
    exit 1
}

RESOURCE_TYPE="${1:-}"
PATTERN="${2:-}"
NAMESPACE="${3:-}"

[ -z "$RESOURCE_TYPE" ] && usage
[ -z "$PATTERN" ] && usage

OUTDIR="${OUTDIR:-/tmp/kubernetes-diag}"
TS=$(date +%Y%m%d-%H%M%S)
RESDIR="$OUTDIR/k8s-resources"
mkdir -p "$RESDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[k8s-resource] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } || true
}

# Find matching resources
find_resources() {
    local type="$1"; local pattern="$2"; local ns="$3"
    if [ -n "$ns" ] && [ "$ns" != "" ]; then
        kubectl get "$type" -n "$ns" -o name 2>/dev/null | grep -i "$pattern" || true
    else
        kubectl get "$type" -A -o name 2>/dev/null | grep -i "$pattern" || true
    fi
}

echo "[k8s-resource] finding ${RESOURCE_TYPE} matching '${PATTERN}' (namespace=${NAMESPACE:-all})"

MATCHES=$(find_resources "$RESOURCE_TYPE" "$PATTERN" "$NAMESPACE")

if [ -z "$MATCHES" ]; then
    echo "[k8s-resource] no matching ${RESOURCE_TYPE} found for pattern '${PATTERN}'"
    exit 0
fi

echo "[k8s-resource] matched:"
echo "$MATCHES"

collect_one() {
    local full_name="$1"  # e.g. pod/kube-system/haproxy-jdsc-prod-k8s-01 or pod/haproxy-xxx
    local item_dir="$RESDIR/$(echo "$full_name" | tr '/' '_' | tr ':' '_')"
    mkdir -p "$item_dir"

    echo "[k8s-resource] collecting: $full_name"

    # Extract type, namespace, name from the kubectl output format
    local k_type="${full_name%%/*}"
    local rest="${full_name#*/}"
    local k_ns="" k_name=""

    # Handle formats: "type/name" (current ns) or "type/namespace/name" (cross ns with -A)
    if echo "$rest" | grep -q '/'; then
        k_ns="${rest%%/*}"
        k_name="${rest#*/}"
    else
        k_ns="${NAMESPACE:-default}"
        k_name="$rest"
    fi

    echo "  type=$k_type ns=$k_ns name=$k_name"

    # Resource yaml and describe
    run "$k_name yaml" "$item_dir/${k_type}.yaml" "kubectl get $k_type -n '$k_ns' '$k_name' -o yaml --request-timeout=10s"
    run "$k_name describe" "$item_dir/${k_type}-describe.txt" "kubectl describe $k_type -n '$k_ns' '$k_name' --request-timeout=10s"

    # Namespace events
    run "$k_ns events" "$item_dir/events-$k_ns.txt" "kubectl get events -n '$k_ns' --sort-by=.lastTimestamp --request-timeout=10s"

    # Owner topology: walk up the ownerReferences chain
    local owner_kind="" owner_name=""
    owner_kind=$(kubectl get "$k_type" -n "$k_ns" "$k_name" -o jsonpath='{.metadata.ownerReferences[0].kind}' 2>/dev/null || true)
    owner_name=$(kubectl get "$k_type" -n "$k_ns" "$k_name" -o jsonpath='{.metadata.ownerReferences[0].name}' 2>/dev/null || true)

    if [ -n "$owner_kind" ] && [ -n "$owner_name" ]; then
        local lk="${owner_kind,,}"  # lowercase: deployment, replicaset, daemonset, statefulset, job
        echo "  owner: $owner_kind/$owner_name"
        run "owner $owner_kind/$owner_name yaml" "$item_dir/owner-${owner_kind}-${owner_name}.yaml" \
            "kubectl get $lk -n '$k_ns' '$owner_name' -o yaml --request-timeout=10s"
        run "owner $owner_kind/$owner_name describe" "$item_dir/owner-${owner_kind}-${owner_name}-describe.txt" \
            "kubectl describe $lk -n '$k_ns' '$owner_name' --request-timeout=10s"
    else
        echo "  no ownerReferences (static Pod or standalone resource)"
    fi

    # Service: match via pod labels if it's a Pod
    if [ "$k_type" = "pod" ] || [ "$k_type" = "pods" ]; then
        local pod_labels
        pod_labels=$(kubectl get pod -n "$k_ns" "$k_name" -o jsonpath='{.metadata.labels}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(','.join(f'{k}={v}' for k,v in d.items()))" 2>/dev/null || true)
        if [ -n "$pod_labels" ]; then
            echo "  searching services matching labels: $pod_labels"
            local svc_match
            svc_match=$(kubectl get svc -A --selector="$pod_labels" -o name 2>/dev/null || true)
            if [ -n "$svc_match" ]; then
                echo "[k8s-resource] found related services: $svc_match"
                for svc_full in $svc_match; do
                    local svc_ns svc_name
                    svc_ns=$(echo "$svc_full" | cut -d'/' -f2)
                    svc_name=$(echo "$svc_full" | cut -d'/' -f3)
                    run "related svc $svc_name yaml" "$item_dir/service-${svc_ns}-${svc_name}.yaml" \
                        "kubectl get svc -n '$svc_ns' '$svc_name' -o yaml --request-timeout=10s"
                    run "related svc $svc_name describe" "$item_dir/service-${svc_ns}-${svc_name}-describe.txt" \
                        "kubectl describe svc -n '$svc_ns' '$svc_name' --request-timeout=10s"
                done
            fi
        fi
    fi

    # Container logs for pods
    if [ "$k_type" = "pod" ] || [ "$k_type" = "pods" ]; then
        local container_names
        container_names=$(kubectl get pod -n "$k_ns" "$k_name" -o jsonpath='{.spec.containers[*].name}' 2>/dev/null || true)
        local logs_dir="$item_dir/container-logs"
        mkdir -p "$logs_dir"
        for c in $container_names; do
            run "container $c logs" "$logs_dir/${c}.log" "kubectl logs -n '$k_ns' '$k_name' -c '$c' --tail=5000 --request-timeout=10s 2>/dev/null || true"
            run "container $c previous logs" "$logs_dir/${c}-previous.log" "kubectl logs -n '$k_ns' '$k_name' -c '$c' --previous --tail=5000 --request-timeout=10s 2>/dev/null || true"
        done
    fi
}

while IFS= read -r line; do
    [ -n "$line" ] && collect_one "$line"
done <<< "$MATCHES"

echo "[k8s-resource] done"
