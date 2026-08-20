#!/usr/bin/env python3
"""Upload a static mirror and install its generated Nginx config."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path


def run(cmd: list[str], dry_run: bool) -> None:
    printable = " ".join(shlex.quote(part) for part in cmd)
    print(printable)
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy a replication-agent static mirror over SSH.")
    parser.add_argument("--mirror-dir", required=True, help="Path to the mirror original directory.")
    parser.add_argument("--ssh-host", required=True, help="Remote SSH host or IP.")
    parser.add_argument("--ssh-user", default="root", help="Remote SSH user.")
    parser.add_argument("--ssh-port", type=int, default=22, help="Remote SSH port.")
    parser.add_argument("--remote-root", help="Remote base root. Defaults to deployment.base_root from manifest/config.")
    parser.add_argument("--remote-nginx-conf", default="/etc/nginx/sites-available/static_mirror.conf")
    parser.add_argument("--enable-nginx-site", action="store_true", help="Symlink config into sites-enabled.")
    parser.add_argument("--reload-nginx", action="store_true", help="Run nginx -t and reload nginx after upload.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mirror_dir = Path(args.mirror_dir).resolve()
    manifest_path = mirror_dir / "manifest.json"
    nginx_conf = mirror_dir / "nginx" / "mirror.conf"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    if not nginx_conf.exists():
        raise FileNotFoundError(f"nginx config not found: {nginx_conf}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    remote_root = args.remote_root or manifest.get("deployment_base_root") or "/srv/mirror/original"
    remote = f"{args.ssh_user}@{args.ssh_host}"
    ssh_base = ["ssh", "-p", str(args.ssh_port), remote]
    rsync_base = ["rsync", "-az", "--delete", "-e", f"ssh -p {args.ssh_port}"]

    mkdir_cmd = "mkdir -p " + " ".join(
        shlex.quote(path) for path in [remote_root, Path(args.remote_nginx_conf).parent.as_posix()]
    )
    run(ssh_base + [mkdir_cmd], args.dry_run)
    run(rsync_base + [str(mirror_dir / "hosts") + "/", f"{remote}:{remote_root.rstrip('/')}/hosts/"], args.dry_run)
    run(rsync_base + [str(nginx_conf), f"{remote}:{args.remote_nginx_conf}"], args.dry_run)

    if args.enable_nginx_site:
        enabled = "/etc/nginx/sites-enabled/" + Path(args.remote_nginx_conf).name
        run(ssh_base + ["ln", "-sfn", args.remote_nginx_conf, enabled], args.dry_run)
    if args.reload_nginx:
        run(ssh_base + ["nginx", "-t"], args.dry_run)
        run(ssh_base + ["systemctl", "reload", "nginx"], args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
