#!/usr/bin/env python3
"""Serve a replicated static mirror using local preview ports or one localhost port."""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import mimetypes
import posixpath
import re
import socketserver
import threading
import urllib.parse
from pathlib import Path


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


LOCALHOST_PREFIX = "/_mirror"


def host_prefix(host: str) -> str:
    return f"{LOCALHOST_PREFIX}/{urllib.parse.quote(host, safe='')}"


def localhost_path(host: str, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{host_prefix(host)}{path}"


def rewrite_localhost_content(content: bytes, content_type: str, current_host: str, port_host_map: dict[int, str]) -> bytes:
    if not current_host or not is_rewritable_content(content_type):
        return content
    text = content.decode("utf-8", errors="replace")

    for port, host in sorted(port_host_map.items()):
        prefix = host_prefix(host)
        text = re.sub(rf"https?://(?:localhost|127\.0\.0\.1):{port}(/[^\"'\s<>)]*)?", lambda m: prefix + (m.group(1) or "/"), text)

    attr_pattern = r"""(?P<prefix>\b(?:href|src|action|poster|content)=["'])(?P<value>/[^/"'][^"']*)"""

    def rewrite_root_attr(match: re.Match[str]) -> str:
        value = match.group("value")
        if value.startswith(f"{LOCALHOST_PREFIX}/"):
            return match.group(0)
        return f"{match.group('prefix')}{localhost_path(current_host, value)}"

    text = re.sub(attr_pattern, rewrite_root_attr, text)

    css_pattern = r"""(?P<prefix>url\(["']?)(?P<value>/[^/"')][^"')]*)(?P<suffix>["']?\))"""
    def rewrite_root_css_url(match: re.Match[str]) -> str:
        value = match.group("value")
        if value.startswith(f"{LOCALHOST_PREFIX}/"):
            return match.group(0)
        return f"{match.group('prefix')}{localhost_path(current_host, value)}{match.group('suffix')}"

    text = re.sub(css_pattern, rewrite_root_css_url, text)

    srcset_pattern = r"""(?P<prefix>\b(?:srcset|imagesrcset)=["'])(?P<value>[^"']*)"""

    def rewrite_srcset(match: re.Match[str]) -> str:
        parts = []
        for item in match.group("value").split(","):
            stripped = item.strip()
            if not stripped:
                continue
            pieces = stripped.split(maxsplit=1)
            url = pieces[0]
            descriptor = f" {pieces[1]}" if len(pieces) > 1 else ""
            if url.startswith("/") and not url.startswith("//") and not url.startswith(f"{LOCALHOST_PREFIX}/"):
                url = localhost_path(current_host, url)
            parts.append(f"{url}{descriptor}")
        return f"{match.group('prefix')}{', '.join(parts)}"

    text = re.sub(srcset_pattern, rewrite_srcset, text)
    return text.encode("utf-8")


def is_rewritable_content(content_type: str) -> bool:
    base = content_type.split(";", 1)[0].lower()
    return base in {"text/html", "text/css", "application/javascript", "text/javascript", "application/json"}


def guess_content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(str(path))
    return content_type or "application/octet-stream"


class AggregatedLocalhostHandler(http.server.BaseHTTPRequestHandler):
    replica_dir: Path
    manifest: dict
    host_roots: dict[str, Path]
    default_host: str
    port_host_map: dict[int, str]

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        self.serve_path()

    def do_HEAD(self) -> None:
        self.serve_path(head_only=True)

    def serve_path(self, head_only: bool = False) -> None:
        parsed = urllib.parse.urlparse(self.path)
        current_host, relative_path = self.resolve_request_path(parsed.path)
        root = self.host_roots.get(current_host)
        if not root:
            self.send_error(404)
            return

        file_path = self.resolve_file(root, relative_path)
        if not file_path:
            self.send_error(404)
            return

        content_type = guess_content_type(file_path)
        content = b"" if head_only else file_path.read_bytes()
        if not head_only:
            content = rewrite_localhost_content(content, content_type, current_host, self.port_host_map)

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def resolve_request_path(self, raw_path: str) -> tuple[str, str]:
        normalized = posixpath.normpath(urllib.parse.unquote(raw_path or "/"))
        if not normalized.startswith("/"):
            normalized = "/" + normalized
        if raw_path.endswith("/") and not normalized.endswith("/"):
            normalized += "/"
        prefix = f"{LOCALHOST_PREFIX}/"
        if normalized.startswith(prefix):
            remainder = normalized[len(prefix) :]
            host, _, path = remainder.partition("/")
            return urllib.parse.unquote(host), "/" + path if path else "/"
        return self.default_host, normalized

    def resolve_file(self, root: Path, relative_path: str) -> Path | None:
        clean_path = posixpath.normpath(relative_path).lstrip("/")
        candidate = (root / clean_path).resolve()
        root_resolved = root.resolve()
        if root_resolved not in candidate.parents and candidate != root_resolved:
            return None
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists() and candidate.suffix == "":
            candidate = candidate / "index.html"
        return candidate if candidate.exists() and candidate.is_file() else None


def serve_host(port: int, directory: Path) -> None:
    handler = functools.partial(QuietHandler, directory=str(directory))
    with ReusableTCPServer(("127.0.0.1", port), handler) as server:
        server.serve_forever()


def serve_aggregated_localhost(replica_dir: Path, manifest: dict, bind: str, port: int) -> int:
    hosts = manifest.get("hosts", [])
    host_roots = {
        str(host["source_host"]): replica_dir / str(host["local_preview_root"])
        for host in hosts
        if host.get("source_host") and host.get("local_preview_root")
    }
    host_roots = {host: root for host, root in host_roots.items() if root.exists()}
    if not host_roots:
        raise SystemExit("No host preview roots found in manifest.")

    target_host = urllib.parse.urlparse(str(manifest.get("target_url", ""))).hostname
    default_host = target_host if target_host in host_roots else sorted(host_roots)[0]
    port_host_map = {
        int(host["local_port"]): str(host["source_host"])
        for host in hosts
        if host.get("local_port") is not None and host.get("source_host") in host_roots
    }

    handler = type(
        "LocalhostMirrorHandler",
        (AggregatedLocalhostHandler,),
        {
            "replica_dir": replica_dir,
            "manifest": manifest,
            "host_roots": host_roots,
            "default_host": default_host,
            "port_host_map": port_host_map,
        },
    )
    with ReusableTCPServer((bind, port), handler) as server:
        print(f"localhost aggregate -> http://{bind}:{port}/")
        print(f"default host: {default_host}")
        for host in sorted(host_roots):
            print(f"{host} -> http://{bind}:{port}{host_prefix(host)}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve replicated hosts on their assigned local ports.")
    parser.add_argument(
        "replica_dir",
        nargs="?",
        default="output/replication_test/original",
        help="Path to mirror/original, or a single static site directory.",
    )
    parser.add_argument("--port", type=int, help="Port for serving a single static site directory.")
    parser.add_argument("--bind", default="127.0.0.1", help="Bind address for single-directory serving.")
    parser.add_argument(
        "--localhost",
        action="store_true",
        help="Serve all mirrored hosts through one localhost port using /_mirror/<source-host>/ paths.",
    )
    args = parser.parse_args()

    replica_dir = Path(args.replica_dir).resolve()
    manifest_path = replica_dir / "manifest.json"
    if not manifest_path.exists():
        port = args.port or 8700
        handler = functools.partial(QuietHandler, directory=str(replica_dir))
        with ReusableTCPServer((args.bind, port), handler) as server:
            print(f"{replica_dir} -> http://{args.bind}:{port}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if args.localhost:
        return serve_aggregated_localhost(replica_dir, manifest, args.bind, args.port or 8700)

    hosts = manifest.get("hosts", [])
    if args.port and len(hosts) > 1:
        raise SystemExit("--port can only override a manifest with one host; multi-host mirrors use manifest ports.")

    threads: list[threading.Thread] = []
    for host in hosts:
        port = int(args.port or host["local_port"])
        directory = replica_dir / host["local_preview_root"]
        if not directory.exists():
            continue
        thread = threading.Thread(target=serve_host, args=(port, directory), daemon=True)
        thread.start()
        threads.append(thread)
        print(f"{host['source_host']} -> http://localhost:{port} ({directory})")

    if not threads:
        raise SystemExit("No hosts to serve.")

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
