#!/usr/bin/env bash
# diag-core.sh — always-run node baseline collector
set -uo pipefail
OUTDIR="${1:?usage: $0 <outdir> <since> <until>}"
SINCE="${2:-8 hours ago}"
UNTIL="${3:-now}"
mkdir -p "$OUTDIR"

run() {
    local desc="$1"; local fname="$2"; shift 2
    echo "[core] $desc"
    { echo "### $*"; echo "### $(date -Iseconds)"; echo "---"; eval "$@" 2>&1; } > "$OUTDIR/$fname" || true
}

run "runtime summary" "00-runtime-summary.txt" \
    "echo node=\$(hostname); echo cgroup_fs=\$(stat -fc %T /sys/fs/cgroup 2>/dev/null); echo '--- kubelet cgroup ---'; grep -i cgroupDriver /var/lib/kubelet/config.yaml 2>/dev/null || true; echo '--- versions ---'; containerd --version 2>/dev/null; runc --version 2>/dev/null | head -5; echo '--- effective runtime ---'; crictl info 2>/dev/null | grep -iE 'SystemdCgroup|defaultRuntimeName|runtimeType|containerdEndpoint|rootDir|stateDir|PluginConfDir|PluginDirs' || true"

run "hostnamectl" "09-hostnamectl.txt" "hostnamectl"
run "uptime" "08-uptime.txt" "uptime"
run "lscpu" "10-lscpu.txt" "LC_ALL=C lscpu"
run "free" "12-free.txt" "free -h"
run "df" "13-df.txt" "df -h"
run "du key dirs" "13b-du-etcd-containerd.txt" "du -sh /var/lib/etcd /var/lib/containerd /var/lib/kubelet /var/lib/cni 2>/dev/null"
run "vmstat 60s" "06-vmstat.txt" "vmstat 1 60"
run "mpstat" "07-mpstat.txt" "mpstat -P ALL 1 10"
run "iostat" "14-iostat.txt" "iostat -x 1 5"
run "dmesg" "11-dmesg.txt" "dmesg -T"
run "dmesg grep" "11b-dmesg-grep.txt" "dmesg -T | grep -iE 'oom|kill|soft lockup|hung task|nmi|throttl|rcu_sched|read-only|I/O error|panic'"
run "timedatectl" "15-timedatectl.txt" "timedatectl status"
run "chrony tracking" "16-chronyc-tracking.txt" "chronyc tracking"
run "chrony sources" "16b-chronyc-sources.txt" "chronyc sources -v"
run "ip link" "24-ip-link-stats.txt" "ip -s link"
run "ethtool drops" "24b-ethtool-stats.txt" "for i in \$(ls /sys/class/net | grep -v lo); do echo --- \"\$i\" ---; ethtool -S \"\$i\" 2>/dev/null | grep -iE 'drop|error|discard'; done"
run "crontabs" "25-crontabs.txt" "for u in root \$(logname 2>/dev/null); do echo '--- crontab -u '\$u' ---'; crontab -u \$u -l 2>/dev/null; done; echo '--- /etc/cron.d ---'; ls -la /etc/cron.d 2>/dev/null; cat /etc/cron.d/* 2>/dev/null"
run "systemd timers" "25b-systemd-timers.txt" "systemctl list-timers --all --no-pager"
run "package history" "25c-package-history.txt" \
    "echo '--- dpkg ---'; dpkg -l 2>/dev/null | grep -iE 'containerd|runc|kubelet|kubeadm|kubectl|docker' || true; echo '--- apt logs ---'; zgrep -hiE 'containerd|runc|kubelet|kubeadm|kubectl|upgrade|install|remove|configure' /var/log/apt/history.log* /var/log/apt/term.log* /var/log/dpkg.log* 2>/dev/null | tail -300 || true; echo '--- containerd config timestamp ---'; ls -l --full-time /etc/containerd/config.toml /etc/containerd/conf.d 2>/dev/null || true"

echo "[core] done"
