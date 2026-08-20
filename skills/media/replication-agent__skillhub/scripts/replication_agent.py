#!/usr/bin/env python3
"""Static multi-host website replication agent.

The agent mirrors authorized root-domain hosts into static files. It preserves
URL paths, assigns one localhost port per mirrored host, and emits deployment
and Nginx artifacts.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import dataclasses
import functools
import hashlib
import html
import http.server
import json
import mimetypes
import os
import posixpath
import re
import signal
import shutil
import socketserver
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock, Thread
from typing import Any

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "replication-agent/0.1"
TRACKING_PARAMS = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"}
PAGE_REUSABLE_STATUSES = {"replicated", "unchanged", "asset_saved"}
RESOURCE_REUSABLE_STATUSES = {"saved", "unchanged"}
PAGE_EXTENSIONS = {"", ".html", ".htm", ".php", ".asp", ".aspx"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".avi"}
STATIC_RESOURCE_EXTENSIONS = {
    ".css",
    ".js",
    ".mjs",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".avif",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
    ".mp3",
    ".wav",
    ".ogg",
    ".pdf",
}
ASSET_ATTRS = {
    "script": ["src"],
    "img": ["src"],
    "iframe": ["src"],
    "source": ["src"],
    "video": ["src", "poster"],
    "audio": ["src"],
    "track": ["src"],
}
GENERIC_ASSET_ATTRS = {
    "data-src",
    "data-srcset",
    "imagesrcset",
    "data-bg",
    "data-background",
    "data-poster",
    "data-lazy-src",
    "data-original",
}
LINK_RESOURCE_RELS = {
    "stylesheet",
    "icon",
    "shortcut icon",
    "apple-touch-icon",
    "mask-icon",
    "preload",
    "modulepreload",
}


@dataclasses.dataclass
class DomainPolicy:
    root_domain: str
    include_subdomains: bool = True
    include: list[str] = dataclasses.field(default_factory=list)
    exclude: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CrawlPolicy:
    respect_robots: bool = True
    max_pages_per_host: int = 5000
    max_depth: int = 50
    rate_limit_per_host: float = 0.4
    render_dynamic_pages: bool = True
    dynamic_render_mode: str = "always"
    require_browser_render: bool = False
    dynamic_wait_ms: int = 1500
    dynamic_network_idle_timeout_ms: int = 5000
    dynamic_scroll_rounds: int = 4
    dynamic_click_rounds: int = 2
    dynamic_click_limit: int = 20
    dynamic_timeout_seconds: int = 30
    download_videos: bool = True
    download_documents: bool = True
    max_asset_size_mb: int = 200
    max_assets_per_host: int = 0
    timeout_seconds: int = 30
    revalidate_completed_on_resume: bool = True
    retry_failed_on_resume: bool = True
    terminal_http_statuses: list[int] = dataclasses.field(default_factory=lambda: [404, 410])
    max_attempts_per_page: int = 3
    worker_count: int = 3


@dataclasses.dataclass
class StaticPolicy:
    preserve_paths: bool = True
    runtime_database: bool = False
    external_link_policy: str = "keep_original"
    query_strategy: str = "record_and_map_when_needed"


@dataclasses.dataclass
class LocalPreview:
    port_start: int = 8300
    host_port_map: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Deployment:
    generate_nginx: bool = True
    base_root: str = "/srv/mirror/original"
    target_host_map: dict[str, str] = dataclasses.field(default_factory=dict)
    target_base_domain: str | None = None
    scheme: str = "https"
    inject_runtime_link_rewriter: bool = True


@dataclasses.dataclass
class QualityPolicy:
    min_page_success_rate: float = 0.95
    min_resource_success_rate: float = 0.98
    max_unresolved_internal_links: int = 0
    max_residual_resources: int = 0
    require_visual_pass: bool = False


@dataclasses.dataclass
class AuthorizationPolicy:
    require_ack: bool = True
    authorized: bool = False
    statement: str = ""


@dataclasses.dataclass
class Viewport:
    name: str
    width: int
    height: int


@dataclasses.dataclass
class VisualPolicy:
    enabled: bool = False
    sample_pages: int = 20
    diff_threshold: float = 0.02
    full_page: bool = True
    wait_ms: int = 1000
    use_vision_model: bool = False
    vision_api_url: str | None = None
    vision_api_key_env: str = "VISION_API_KEY"
    vision_model: str | None = None
    viewports: list[Viewport] = dataclasses.field(
        default_factory=lambda: [
            Viewport("desktop", 1365, 900),
            Viewport("mobile", 390, 844),
        ]
    )


@dataclasses.dataclass
class ReplicationConfig:
    site_id: str
    target_url: str
    out_dir: Path
    domain_policy: DomainPolicy
    crawl_policy: CrawlPolicy = dataclasses.field(default_factory=CrawlPolicy)
    static_policy: StaticPolicy = dataclasses.field(default_factory=StaticPolicy)
    local_preview: LocalPreview = dataclasses.field(default_factory=LocalPreview)
    deployment: Deployment = dataclasses.field(default_factory=Deployment)
    visual_policy: VisualPolicy = dataclasses.field(default_factory=VisualPolicy)
    quality_policy: QualityPolicy = dataclasses.field(default_factory=QualityPolicy)
    authorization_policy: AuthorizationPolicy = dataclasses.field(default_factory=AuthorizationPolicy)
    force_refresh: bool = False


@dataclasses.dataclass
class HostState:
    source_host: str
    local_port: int
    deploy_host: str
    pages_seen: set[str] = dataclasses.field(default_factory=set)
    pages_done: set[str] = dataclasses.field(default_factory=set)
    assets_seen: set[str] = dataclasses.field(default_factory=set)
    assets_done: set[str] = dataclasses.field(default_factory=set)
    last_request_at: float = 0.0
    request_lock: RLock = dataclasses.field(default_factory=RLock, repr=False)


@dataclasses.dataclass
class CrawlItem:
    url: str
    host: str
    depth: int
    status: str = "discovered"
    discovered_from: str | None = None
    local_preview_url: str | None = None
    deploy_url: str | None = None
    local_preview_path: str | None = None
    deploy_path: str | None = None
    status_code: int | None = None
    content_hash: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    attempts: int = 0
    error: str | None = None
    discovered_at: str = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_checked_at: str | None = None
    updated_at: str = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclasses.dataclass
class ResourceItem:
    url: str
    host: str
    page_url: str
    public_path: str
    status: str = "discovered"
    content_type: str | None = None
    size: int | None = None
    content_hash: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    error: str | None = None
    last_checked_at: str | None = None
    updated_at: str = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclasses.dataclass
class RenderResult:
    html: str
    final_url: str
    status_code: int | None
    content_hash: str
    screenshot_path: str | None
    discovered_urls: list[str]
    resource_urls: list[str]


@dataclasses.dataclass
class PageRecord:
    url: str
    source_host: str
    source_path: str
    local_preview_url: str
    deploy_url: str
    local_preview_path: str
    deploy_path: str
    status_code: int | None
    content_hash: str | None
    render_mode: str
    internal_links: int
    external_links: int
    assets: int
    status: str
    screenshot_path: str | None = None
    error: str | None = None


class ReplicationAgent:
    def __init__(self, config: ReplicationConfig):
        self.config = config
        self.out_dir = config.out_dir
        self.original_dir = self.out_dir / "original"
        self.hosts_dir = self.original_dir / "hosts"
        self.snapshots_dir = self.original_dir / "snapshots"
        self.nginx_dir = self.original_dir / "nginx"
        self.hosts: dict[str, HostState] = {}
        self.queue: deque[tuple[str, int]] = deque()
        self.robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self.crawl_table: dict[str, CrawlItem] = {}
        self.resource_table: dict[str, ResourceItem] = {}
        self.rewrite_map: dict[str, dict[str, Any]] = {}
        self.page_records: list[PageRecord] = []
        self.asset_records: list[dict[str, Any]] = []
        self.link_records: list[dict[str, Any]] = []
        self.query_records: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.unresolved_internal_links: list[dict[str, str]] = []
        self.residual_static_refs: list[dict[str, str]] = []
        self.visual_records: list[dict[str, Any]] = []
        self._playwright: Any = None
        self._browser: Any = None
        self._last_progress_flush_at = 0.0
        self._progress_flush_interval_seconds = 30.0
        self._state_lock = RLock()
        self._write_lock = RLock()
        self._active_page_hosts: dict[str, int] = {}

    def run(self) -> None:
        try:
            self.ensure_authorized()
            self.original_dir.mkdir(parents=True, exist_ok=True)
            self.hosts_dir.mkdir(parents=True, exist_ok=True)
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)
            self.nginx_dir.mkdir(parents=True, exist_ok=True)

            if not self.config.force_refresh:
                self.load_previous_state()
            had_previous_crawl_table = bool(self.crawl_table)

            for item in sorted(self.crawl_table.values(), key=lambda entry: (entry.depth, entry.url)):
                canonical_url = self.canonicalize_crawl_url(item.url)
                if canonical_url != item.url:
                    canonical_item = self.crawl_table.get(canonical_url)
                    if not canonical_item or canonical_item.status in {"queued", "fetching", "discovered"}:
                        self.enqueue_page(canonical_url, item.depth, discovered_from=item.discovered_from)
                    self.update_crawl_item(
                        item.url,
                        status="canonicalized",
                        error=None,
                        last_checked_at=datetime.now(timezone.utc).isoformat(),
                    )
                    continue
                if item.status == "canonicalized":
                    continue
                if item.status == "fetch_failed" and not self.config.crawl_policy.retry_failed_on_resume:
                    continue
                if item.status in PAGE_REUSABLE_STATUSES and not self.config.crawl_policy.revalidate_completed_on_resume:
                    state = self.ensure_host(item.host)
                    if self.page_outputs_exist(item):
                        state.pages_seen.add(item.url)
                        state.pages_done.add(item.url)
                        continue
                self.enqueue_page(item.url, item.depth, discovered_from=item.discovered_from)

            start = normalize_url(self.config.target_url)
            if not start:
                raise ValueError(f"Invalid target URL: {self.config.target_url}")
            self.enqueue_page(start, depth=0, discovered_from=None)
            should_scan_sitemaps = (
                self.config.force_refresh
                or self.config.crawl_policy.revalidate_completed_on_resume
                or not had_previous_crawl_table
            )
            if should_scan_sitemaps:
                self.enqueue_sitemap_urls(start)

            self.consume_page_queue()

            if self.config.crawl_policy.revalidate_completed_on_resume:
                self.check_previous_resources()
            self.repair_missing_local_static_refs()
            self.verify_internal_link_completeness()
            self.verify_static_resource_localization()
            self.write_manifests()
            self.write_deployment_doc()
            self.write_nginx_configs()
            if self.config.visual_policy.enabled:
                self.run_visual_validation()
                self.write_manifests()
        except KeyboardInterrupt:
            self.errors.append({"type": "interrupted", "error": "Replication interrupted by user or supervisor."})
            self.flush_progress_tables(force=True)
            self.write_manifests()
            raise
        finally:
            self.close_browser()

    def ensure_authorized(self) -> None:
        policy = self.config.authorization_policy
        if not policy.require_ack or policy.authorized:
            return
        raise PermissionError(
            "Replication requires explicit authorization. Set authorization_policy.authorized=true "
            "in the config or pass --ack-authorized after confirming you may mirror this site."
        )

    def consume_page_queue(self) -> None:
        worker_count = max(1, int(self.config.crawl_policy.worker_count))
        if worker_count == 1:
            while True:
                next_item = self.pop_next_page()
                if next_item is None:
                    break
                url, depth = next_item
                try:
                    self.fetch_page(url, depth)
                finally:
                    self.finish_page(url)
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures: dict[concurrent.futures.Future[None], tuple[str, int]] = {}
            while True:
                while len(futures) < worker_count:
                    next_item = self.pop_next_page()
                    if next_item is None:
                        break
                    url, depth = next_item
                    futures[executor.submit(self.fetch_page, url, depth)] = (url, depth)
                if not futures:
                    break
                done, _ = concurrent.futures.wait(
                    futures,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                for future in done:
                    url, _ = futures.pop(future)
                    try:
                        future.result()
                    except Exception as exc:
                        self.record_page_failure(url, "worker_failed", str(exc))
                    finally:
                        self.finish_page(url)

    def pop_next_page(self) -> tuple[str, int] | None:
        with self._state_lock:
            while self.queue:
                selected_index = self.select_next_queue_index()
                if selected_index:
                    self.queue.rotate(-selected_index)
                url, depth = self.queue.popleft()
                if selected_index:
                    self.queue.rotate(selected_index)
                host = urllib.parse.urlparse(url).hostname or ""
                state = self.hosts.get(host)
                if state is None:
                    continue
                item = self.crawl_table.get(url)
                if item and item.attempts >= self.config.crawl_policy.max_attempts_per_page and item.status not in PAGE_REUSABLE_STATUSES:
                    self.update_crawl_item(url, status="max_attempts_exceeded", error=item.error or "retry limit reached")
                    continue
                if url in state.pages_done:
                    continue
                if len(state.pages_done) >= self.config.crawl_policy.max_pages_per_host:
                    self.update_crawl_item(url, status="skipped_page_limit")
                    continue
                state.pages_done.add(url)
                self._active_page_hosts[host] = self._active_page_hosts.get(host, 0) + 1
                return url, depth
        return None

    def select_next_queue_index(self) -> int:
        for index, (url, _) in enumerate(self.queue):
            host = urllib.parse.urlparse(url).hostname or ""
            if host and host not in self._active_page_hosts:
                return index
        return 0

    def finish_page(self, url: str) -> None:
        host = urllib.parse.urlparse(url).hostname or ""
        if not host:
            return
        with self._state_lock:
            count = self._active_page_hosts.get(host, 0)
            if count <= 1:
                self._active_page_hosts.pop(host, None)
            else:
                self._active_page_hosts[host] = count - 1

    def load_previous_state(self) -> None:
        manifest = self.read_previous_json("manifest.json")
        for host_item in manifest.get("hosts", []):
            host = str(host_item.get("source_host") or "")
            if not host:
                continue
            port_value = host_item.get("local_port")
            try:
                local_port = int(port_value) if port_value is not None else None
            except (TypeError, ValueError):
                local_port = None
            configured_deploy_host = self.deploy_host(host)
            manifest_deploy_host = str(host_item.get("deploy_host") or "")
            deploy_host = configured_deploy_host if self.configured_deploy_mapping_enabled() else (manifest_deploy_host or configured_deploy_host)
            self.register_host(host, local_port=local_port, deploy_host=deploy_host)

        crawl_data = self.read_previous_json("crawl_table.json")
        crawl_fields = {field.name for field in dataclasses.fields(CrawlItem)}
        for raw in crawl_data.get("items", []):
            if not isinstance(raw, dict):
                continue
            values = {key: value for key, value in raw.items() if key in crawl_fields}
            if not values.get("url") or not values.get("host"):
                continue
            try:
                item = CrawlItem(**values)
            except TypeError:
                continue
            if item.status == "fetching":
                item.status = "fetch_failed"
                item.error = item.error or "stale_fetching_reset_on_resume"
            self.crawl_table[item.url] = item
            if self.is_allowed_host(item.host):
                self.ensure_host(item.host)
            self.rewrite_map[item.url] = {
                "source_url": item.url,
                "source_host": item.host,
                "source_path": urllib.parse.urlparse(item.url).path or "/",
                "local_preview_url": item.local_preview_url or self.public_url(item.url, "local"),
                "deploy_url": item.deploy_url or self.public_url(item.url, "deploy"),
                "local_preview_path": item.local_preview_path,
                "deploy_path": item.deploy_path,
                "status": item.status,
            }

        resource_data = self.read_previous_json("resource_table.json")
        resource_fields = {field.name for field in dataclasses.fields(ResourceItem)}
        for raw in resource_data.get("items", []):
            if not isinstance(raw, dict):
                continue
            values = {key: value for key, value in raw.items() if key in resource_fields}
            if not values.get("url") or not values.get("host") or not values.get("public_path"):
                continue
            try:
                item = ResourceItem(**values)
            except TypeError:
                continue
            self.resource_table[item.url] = item
            if self.is_allowed_host(item.host):
                self.ensure_host(item.host)

        rewrite_data = self.read_previous_json("rewrite_map.json")
        for raw in rewrite_data.get("items", []):
            if isinstance(raw, dict) and raw.get("source_url"):
                self.rewrite_map[str(raw["source_url"])] = raw
        self.rebuild_page_records_from_crawl_table()

    def rebuild_page_records_from_crawl_table(self) -> None:
        self.page_records = []
        for item in sorted(self.crawl_table.values(), key=lambda entry: (entry.host, entry.depth, entry.url)):
            if item.status not in {"replicated", "unchanged"}:
                continue
            if not self.page_outputs_exist(item):
                continue
            parsed = urllib.parse.urlparse(item.url)
            self.page_records.append(
                PageRecord(
                    url=item.url,
                    source_host=item.host,
                    source_path=parsed.path or "/",
                    local_preview_url=item.local_preview_url or self.public_url(item.url, "local"),
                    deploy_url=item.deploy_url or self.public_url(item.url, "deploy"),
                    local_preview_path=item.local_preview_path,
                    deploy_path=item.deploy_path,
                    status_code=item.status_code,
                    content_hash=item.content_hash,
                    render_mode=getattr(item, "render_mode", None) or "http",
                    internal_links=0,
                    external_links=0,
                    assets=0,
                    status="unchanged" if item.status == "unchanged" else "verified",
                )
            )

    def read_previous_json(self, name: str) -> dict[str, Any]:
        path = self.original_dir / name
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def check_previous_resources(self) -> None:
        for item in list(self.resource_table.values()):
            if item.status not in RESOURCE_REUSABLE_STATUSES:
                continue
            state = self.ensure_host(item.host)
            if item.url in state.assets_done:
                continue
            if not self.asset_outputs_exist(item):
                self.download_asset_ref(item.url, item.page_url)
                continue
            self.download_asset_ref(item.url, item.page_url)

    def enqueue_sitemap_urls(self, start_url: str) -> None:
        host = urllib.parse.urlparse(start_url).hostname or ""
        for sitemap_url in discover_sitemaps(start_url, self.config.crawl_policy.timeout_seconds):
            try:
                status, _, body = self.request(sitemap_url)
            except Exception as exc:
                self.errors.append({"type": "sitemap_error", "url": sitemap_url, "error": str(exc)})
                continue
            if status != 200:
                continue
            for loc in parse_sitemap_locations(body):
                normalized = normalize_url(loc)
                parsed = urllib.parse.urlparse(normalized)
                if normalized and self.is_allowed_host(parsed.hostname or ""):
                    self.ensure_host(parsed.hostname or "")
                    if is_probable_page_url(normalized):
                        self.enqueue_page(normalized, 0, discovered_from=sitemap_url)
                    else:
                        self.download_asset_ref(normalized, sitemap_url)
            if host not in self.hosts:
                self.ensure_host(host)

    def should_render_dynamic_page(self, url: str, depth: int, body: bytes) -> bool:
        policy = self.config.crawl_policy
        if not policy.render_dynamic_pages:
            return False
        mode = policy.dynamic_render_mode.lower()
        is_start_url = normalize_url(url) == normalize_url(self.config.target_url)
        if mode == "always":
            return True
        if mode == "first_page":
            return is_start_url
        if mode != "auto":
            return True
        if is_start_url:
            return True
        text = body[:250000].decode("utf-8", errors="ignore").lower()
        dynamic_markers = (
            "data-src",
            "data-srcset",
            "loading=\"lazy\"",
            "aria-expanded=\"false\"",
            "data-state=\"closed\"",
            "__next_data__",
            "window.__",
            "hydrate",
            "intersectionobserver",
            "requestanimationframe",
        )
        return any(marker in text for marker in dynamic_markers)

    def fetch_page(self, url: str, depth: int) -> None:
        canonical_url = self.canonicalize_crawl_url(url)
        if canonical_url != url:
            previous = self.crawl_table.get(url)
            self.enqueue_page(canonical_url, depth, discovered_from=previous.discovered_from if previous else None)
            self.update_crawl_item(
                url,
                status="canonicalized",
                error=None,
                last_checked_at=datetime.now(timezone.utc).isoformat(),
            )
            self.flush_progress_tables()
            return
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        state = self.ensure_host(host)
        with self._state_lock:
            state.pages_done.add(url)
        previous = self.crawl_table.get(url)
        self.update_crawl_item(url, status="fetching", attempts=(previous.attempts + 1 if previous else 1))

        if self.config.crawl_policy.respect_robots and not self.can_fetch(url):
            self.record_page_failure(url, "blocked_by_robots")
            return

        try:
            status, headers, body = self.request(url, headers=self.conditional_headers(previous))
        except urllib.error.HTTPError as exc:
            if exc.code in self.config.crawl_policy.terminal_http_statuses:
                self.record_page_failure(url, f"http_{exc.code}", str(exc), status_code=exc.code)
            else:
                self.record_page_failure(url, "fetch_failed", str(exc), status_code=exc.code)
            return
        except Exception as exc:
            self.record_page_failure(url, "fetch_failed", str(exc))
            return

        if status == 304 and previous and self.page_outputs_exist(previous):
            self.record_unchanged_page(url, previous, status, previous.content_hash)
            return
        if status == 304:
            try:
                status, headers, body = self.request(url)
            except urllib.error.HTTPError as exc:
                if exc.code in self.config.crawl_policy.terminal_http_statuses:
                    self.record_page_failure(url, f"http_{exc.code}", str(exc), status_code=exc.code)
                else:
                    self.record_page_failure(url, "fetch_failed", str(exc), status_code=exc.code)
                return
            except Exception as exc:
                self.record_page_failure(url, "fetch_failed", str(exc))
                return

        content_type = headers.get("content-type", "").split(";")[0].lower()
        if not is_html_response(url, content_type):
            self.save_asset(url, current_page_url=url, body=body, content_type=content_type)
            self.update_crawl_item(
                url,
                status="asset_saved",
                status_code=status,
                content_hash=sha256_hex(body),
                etag=headers.get("etag") or (previous.etag if previous else None),
                last_modified=headers.get("last-modified") or (previous.last_modified if previous else None),
                last_checked_at=datetime.now(timezone.utc).isoformat(),
            )
            return

        render_result: RenderResult | None = None
        render_mode = "http"
        screenshot_path: str | None = None
        if self.should_render_dynamic_page(url, depth, body):
            render_result = self.render_dynamic_page(url)
            if render_result:
                body = render_result.html.encode("utf-8")
                content_type = "text/html"
                content_hash = render_result.content_hash
                status = render_result.status_code or status
                render_mode = "browser"
                screenshot_path = render_result.screenshot_path
                for discovered in render_result.discovered_urls:
                    normalized = normalize_url(discovered)
                    parsed_discovered = urllib.parse.urlparse(normalized)
                    if normalized and self.is_allowed_host(parsed_discovered.hostname or ""):
                        self.enqueue_page(normalized, depth + 1, discovered_from=url)
                for resource_url in render_result.resource_urls:
                    if is_static_resource_url(resource_url):
                        self.download_asset_ref(resource_url, url)
            elif self.config.crawl_policy.require_browser_render:
                self.record_page_failure(url, "render_failed", "Playwright render returned no result.")
                return
            else:
                content_hash = sha256_hex(body)
        else:
            content_hash = sha256_hex(body)

        if previous and previous.content_hash == content_hash and self.page_outputs_exist(previous):
            self.record_unchanged_page(url, previous, status, content_hash, headers=headers)
            return

        self.save_snapshot(url, body)
        html_text = render_result.html if render_result else decode_body(body, headers)
        soup = BeautifulSoup(html_text, "html5lib")

        page_links = self.collect_and_rewrite_links(soup, url, depth)
        assets = self.collect_and_rewrite_assets(soup, url)

        self.inject_runtime_asset_rewriter(soup, url)
        self.inject_base_comment(soup, url)
        self.write_page_variants(url, soup)

        source_path = parsed.path or "/"
        record = PageRecord(
            url=url,
            source_host=host,
            source_path=source_path,
            local_preview_url=self.public_url(url, mode="local"),
            deploy_url=self.public_url(url, mode="deploy"),
            local_preview_path=str(self.output_page_path(url, "local_preview").relative_to(self.original_dir)),
            deploy_path=str(self.output_page_path(url, "site").relative_to(self.original_dir)),
            status_code=status,
            content_hash=content_hash,
            render_mode=render_mode,
            internal_links=page_links["internal"],
            external_links=page_links["external"],
            assets=assets,
            status="verified",
            screenshot_path=screenshot_path,
        )
        self.page_records.append(record)
        self.update_crawl_item(
            url,
            status="replicated",
            local_preview_url=record.local_preview_url,
            deploy_url=record.deploy_url,
            local_preview_path=record.local_preview_path,
            deploy_path=record.deploy_path,
            status_code=status,
            content_hash=content_hash,
            etag=headers.get("etag"),
            last_modified=headers.get("last-modified"),
            error=None,
            last_checked_at=datetime.now(timezone.utc).isoformat(),
        )
        self.flush_progress_tables(force=True)

    def collect_and_rewrite_links(self, soup: BeautifulSoup, page_url: str, depth: int) -> dict[str, int]:
        internal = 0
        external = 0
        for tag in soup.find_all("a", href=True):
            original_href = str(tag["href"])
            if original_href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = normalize_url(urllib.parse.urljoin(page_url, original_href))
            if not absolute:
                continue
            parsed = urllib.parse.urlparse(absolute)
            target_host = parsed.hostname or ""
            if self.is_allowed_host(target_host):
                internal += 1
                self.ensure_host(target_host)
                self.link_records.append({"from": page_url, "to": absolute, "type": "internal"})
                if depth + 1 <= self.config.crawl_policy.max_depth and is_probable_page_url(absolute):
                    self.enqueue_page(absolute, depth + 1, discovered_from=page_url)
                elif is_static_resource_url(absolute):
                    self.download_asset_ref(absolute, page_url)
                tag["data-replication-original-href"] = original_href
                tag["data-replication-local-href"] = self.public_url(absolute, mode="local")
                tag["data-replication-deploy-href"] = self.public_url(absolute, mode="deploy")
                tag["href"] = self.rewrite_link_for_mode(absolute, page_url, mode="deploy")
            else:
                external += 1
                self.link_records.append({"from": page_url, "to": absolute, "type": "external"})
        return {"internal": internal, "external": external}

    def collect_and_rewrite_assets(self, soup: BeautifulSoup, page_url: str) -> int:
        count = 0
        for tag in soup.find_all(True):
            for attr in ASSET_ATTRS.get(tag.name, []):
                value = tag.get(attr)
                if isinstance(value, str) and self.should_download_asset(value):
                    local = self.download_asset_ref(value, page_url)
                    if local:
                        tag[attr] = local
                        tag.attrs.pop("integrity", None)
                        tag.attrs.pop("crossorigin", None)
                        count += 1
            for attr in GENERIC_ASSET_ATTRS:
                value = tag.get(attr)
                if not isinstance(value, str) or not self.should_download_asset(value):
                    continue
                if attr.endswith("srcset"):
                    rewritten, rewritten_count = self.rewrite_srcset(value, page_url)
                    tag[attr] = rewritten
                    count += rewritten_count
                else:
                    local = self.download_asset_ref(value, page_url)
                    if local:
                        tag[attr] = local
                        count += 1
            if tag.get("style"):
                rewritten_style = self.rewrite_css(str(tag["style"]).encode("utf-8"), page_url, urllib.parse.urlparse(page_url).hostname or "")
                tag["style"] = rewritten_style.decode("utf-8", errors="replace")
            if tag.name == "link" and tag.get("href"):
                rel = normalize_rel(tag.get("rel"))
                as_attr = str(tag.get("as", "")).lower()
                if rel.intersection(LINK_RESOURCE_RELS) or as_attr in {"style", "script", "font", "image"}:
                    local = self.download_asset_ref(str(tag["href"]), page_url)
                    if local:
                        tag["href"] = local
                        tag.attrs.pop("integrity", None)
                        tag.attrs.pop("crossorigin", None)
                        count += 1
            if tag.get("srcset"):
                rewritten, rewritten_count = self.rewrite_srcset(str(tag["srcset"]), page_url)
                tag["srcset"] = rewritten
                count += rewritten_count
            if tag.name == "meta" and tag.get("content"):
                prop = tag.get("property") or tag.get("name")
                if prop in {"og:image", "twitter:image"}:
                    local = self.download_asset_ref(str(tag["content"]), page_url)
                    if local:
                        tag["content"] = local
                        count += 1
            if tag.name == "style" and tag.string:
                rewritten_css = self.rewrite_css(str(tag.string).encode("utf-8"), page_url, urllib.parse.urlparse(page_url).hostname or "")
                tag.string.replace_with(rewritten_css.decode("utf-8", errors="replace"))
        return count

    def inject_runtime_link_rewriter(self, soup: BeautifulSoup) -> None:
        if not self.config.deployment.inject_runtime_link_rewriter:
            return
        host_map = {
            state.source_host: state.deploy_host
            for state in self.hosts.values()
            if state.deploy_host and state.deploy_host != state.source_host
        }
        target_base = self.config.deployment.target_base_domain
        if not host_map and not target_base:
            return
        if soup.find("script", attrs={"data-replication-runtime": "link-rewriter"}):
            return
        payload = json.dumps(
            {
                "scheme": self.config.deployment.scheme,
                "rootDomain": self.config.domain_policy.root_domain,
                "targetBaseDomain": target_base,
                "hostMap": host_map,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).replace("</", "<\\/")
        script = soup.new_tag("script")
        script["data-replication-runtime"] = "link-rewriter"
        script.string = f"""
(function() {{
  var config = {payload};
  function mappedHost(hostname) {{
    if (!hostname) return "";
    if (config.hostMap && config.hostMap[hostname]) return config.hostMap[hostname];
    if (config.targetBaseDomain && config.rootDomain) {{
      if (hostname === config.rootDomain) return config.targetBaseDomain;
      var suffix = "." + config.rootDomain;
      if (hostname.slice(-suffix.length) === suffix) {{
        return hostname.slice(0, -config.rootDomain.length).replace(/\\.$/, "") + "." + config.targetBaseDomain;
      }}
    }}
    return "";
  }}
  function rewriteUrl(value) {{
    if (!value || /^(#|mailto:|tel:|javascript:|data:|blob:)/i.test(value)) return value;
    try {{
      var url = new URL(value, window.location.href);
      var host = mappedHost(url.hostname);
      if (!host) return value;
      url.protocol = (config.scheme || "https") + ":";
      url.hostname = host;
      return url.href;
    }} catch (error) {{
      return value;
    }}
  }}
  function rewriteElement(element) {{
    if (!element || element.nodeType !== 1) return;
    if (element.hasAttribute("href")) element.setAttribute("href", rewriteUrl(element.getAttribute("href")));
    if (element.hasAttribute("action")) element.setAttribute("action", rewriteUrl(element.getAttribute("action")));
  }}
  function closestLink(element) {{
    while (element && element.nodeType === 1) {{
      if ((element.tagName === "A" || element.tagName === "AREA") && element.hasAttribute("href")) return element;
      element = element.parentElement;
    }}
    return null;
  }}
  document.addEventListener("click", function(event) {{
    var link = closestLink(event.target);
    if (!link) return;
    var original = link.getAttribute("href");
    var rewritten = rewriteUrl(original);
    if (!rewritten || rewritten === original) return;
    event.preventDefault();
    window.location.href = rewritten;
  }}, true);
  document.addEventListener("submit", function(event) {{
    var form = event.target;
    if (!form || !form.hasAttribute || !form.hasAttribute("action")) return;
    rewriteElement(form);
  }}, true);
}})();
"""
        target = soup.head or soup.body or soup
        target.insert(0, script)

    def inject_runtime_asset_rewriter(self, soup: BeautifulSoup, page_url: str) -> None:
        runtime_map = self.runtime_asset_map_for_page(soup, page_url)
        if not runtime_map:
            return
        payload = json.dumps(runtime_map, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
        script = soup.new_tag("script")
        script["data-replication-runtime"] = "asset-rewriter"
        script.string = f"""
(function() {{
  var assetMap = {payload};
  function normalizeAssetUrl(value) {{
    if (!value) return "";
    try {{
      var url = new URL(value, window.location.href);
      if (url.pathname === "/_next/image") {{
        var nested = url.searchParams.get("url");
        if (nested) return new URL(nested, window.location.href).href;
      }}
      return url.href;
    }} catch (error) {{
      return value;
    }}
  }}
  function localizeUrl(value) {{
    var key = normalizeAssetUrl(value);
    if (assetMap[key]) return assetMap[key];
    try {{
      var url = new URL(value, window.location.href);
      if (url.pathname === "/_next/image") {{
        var nested = url.searchParams.get("url");
        if (nested && nested.indexOf("/__external_assets/") === 0) return nested;
      }}
    }} catch (error) {{}}
    return value;
  }}
  function rewriteSrcset(value) {{
    if (!value) return value;
    return value.split(",").map(function(item) {{
      var parts = item.trim().split(/\\s+/);
      if (!parts[0]) return item;
      parts[0] = localizeUrl(parts[0]);
      return parts.join(" ");
    }}).join(", ");
  }}
  function setIfChanged(element, attr, value) {{
    if (value && element.getAttribute(attr) !== value) element.setAttribute(attr, value);
  }}
  function rewriteElement(element) {{
    if (!element || element.nodeType !== 1) return;
    if (element.hasAttribute("src")) setIfChanged(element, "src", localizeUrl(element.getAttribute("src")));
    if (element.hasAttribute("poster")) setIfChanged(element, "poster", localizeUrl(element.getAttribute("poster")));
    if (element.hasAttribute("srcset")) setIfChanged(element, "srcset", rewriteSrcset(element.getAttribute("srcset")));
    if (element.hasAttribute("imagesrcset")) setIfChanged(element, "imagesrcset", rewriteSrcset(element.getAttribute("imagesrcset")));
    if (element.tagName === "LINK" && (element.getAttribute("as") || "").toLowerCase() === "image" && element.hasAttribute("href")) {{
      setIfChanged(element, "href", localizeUrl(element.getAttribute("href")));
    }}
  }}
  function rewriteAll(root) {{
    rewriteElement(root);
    if (!root.querySelectorAll) return;
    root.querySelectorAll("img,source,video,audio,track,iframe,link").forEach(rewriteElement);
  }}
  function scheduleRewrite() {{
    var run = function() {{ rewriteAll(document.documentElement); }};
    if ("requestIdleCallback" in window) window.requestIdleCallback(run, {{timeout: 1500}});
    else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run, {{once: true}});
    else setTimeout(run, 0);
  }}
  scheduleRewrite();
}})();
"""
        target = soup.head or soup.body or soup
        target.insert(0, script)

    def runtime_asset_map_for_page(self, soup: BeautifulSoup, page_url: str) -> dict[str, str]:
        text = str(soup)
        static_ext_pattern = "|".join(re.escape(ext.lstrip(".")) for ext in sorted(STATIC_RESOURCE_EXTENSIONS, key=len, reverse=True))
        url_pattern = re.compile(
            rf"https?://[^'\"`<>\s\\]+?\.({static_ext_pattern})(?:\?[^'\"`<>\s\\]*)?",
            re.IGNORECASE,
        )
        next_image_pattern = re.compile(r"/_next/image\?url=[^'\"`<>\s\\]+", re.IGNORECASE)
        candidates: set[str] = set()
        candidates.update(match.group(0).replace("\\u0026", "&") for match in url_pattern.finditer(text))
        candidates.update(urllib.parse.urljoin(page_url, match.group(0).replace("\\u0026", "&")) for match in next_image_pattern.finditer(text))

        runtime_map: dict[str, str] = {}
        def add_mapping(source_url: str, public_path: str) -> None:
            if not source_url or not public_path:
                return
            existing = runtime_map.get(source_url)
            if existing and not (existing.startswith("/_next/image") and public_path.startswith("/__external_assets/")):
                return
            runtime_map[source_url] = public_path

        for candidate in candidates:
            absolute = normalize_url(candidate)
            if not absolute:
                continue
            effective = self.effective_asset_url(absolute, page_url) or absolute
            item = self.resource_table.get(effective) or self.resource_table.get(absolute)
            if not item or item.status not in RESOURCE_REUSABLE_STATUSES:
                continue
            if not item.public_path:
                continue
            add_mapping(effective, item.public_path)
            add_mapping(absolute, item.public_path)
        normalized_page_url = normalize_url(page_url)
        for item in self.resource_table.values():
            if normalize_url(item.page_url) != normalized_page_url:
                continue
            if item.status not in RESOURCE_REUSABLE_STATUSES or not item.public_path:
                continue
            effective = self.effective_asset_url(item.url, page_url) or item.url
            add_mapping(effective, item.public_path)
            add_mapping(item.url, item.public_path)
        return runtime_map

    def rewrite_srcset(self, value: str, page_url: str) -> tuple[str, int]:
        parts: list[str] = []
        count = 0
        for item in value.split(","):
            bits = item.strip().split()
            if not bits:
                continue
            local = self.download_asset_ref(bits[0], page_url)
            if local:
                bits[0] = local
                count += 1
            parts.append(" ".join(bits))
        return ", ".join(parts), count

    def download_asset_ref(self, ref: str, page_url: str) -> str | None:
        if ref.startswith(("data:", "blob:", "#", "mailto:", "tel:", "javascript:")):
            return None
        absolute = normalize_url(urllib.parse.urljoin(page_url, ref))
        if not absolute:
            return None
        effective_absolute = self.effective_asset_url(absolute, page_url)
        if effective_absolute:
            absolute = effective_absolute
        parsed = urllib.parse.urlparse(absolute)
        ext = Path(parsed.path).suffix.lower()
        if ext in VIDEO_EXTENSIONS and not self.config.crawl_policy.download_videos:
            return ref
        if ext in DOCUMENT_EXTENSIONS and not self.config.crawl_policy.download_documents:
            return ref

        current_host = urllib.parse.urlparse(page_url).hostname or ""
        local_path = self.asset_public_path(absolute, current_host)
        state = self.ensure_host(current_host)
        item = self.ensure_resource_item(absolute, current_host, page_url, local_path)
        if absolute in state.assets_done:
            return local_path
        if absolute in state.assets_seen:
            return local_path
        reusable_existing = item.status in RESOURCE_REUSABLE_STATUSES and self.asset_outputs_exist(item)
        if (
            not reusable_existing
            and self.config.crawl_policy.max_assets_per_host
            and len(state.assets_seen) >= self.config.crawl_policy.max_assets_per_host
        ):
            self.asset_records.append({"url": absolute, "status": "skipped_asset_limit", "page": page_url})
            self.update_resource_item(absolute, status="skipped_asset_limit")
            return ref
        if reusable_existing and not self.config.crawl_policy.revalidate_completed_on_resume:
            state.assets_done.add(absolute)
            return item.public_path
        if not reusable_existing:
            state.assets_seen.add(absolute)

        try:
            status, headers, body = self.request(
                absolute,
                allow_robots=False,
                headers=self.conditional_headers(item) if reusable_existing else None,
            )
            if status == 304 and reusable_existing:
                state.assets_done.add(absolute)
                self.asset_records.append(
                    {
                        "url": absolute,
                        "host": item.host,
                        "public_path": item.public_path,
                        "content_type": item.content_type,
                        "size": item.size,
                        "hash": item.content_hash,
                        "status": "unchanged",
                    }
                )
                self.update_resource_item(
                    absolute,
                    status="unchanged",
                    etag=headers.get("etag") or item.etag,
                    last_modified=headers.get("last-modified") or item.last_modified,
                    error=None,
                    last_checked_at=datetime.now(timezone.utc).isoformat(),
                )
                return local_path
            if status != 200:
                self.asset_records.append({"url": absolute, "status": f"http_{status}", "page": page_url})
                self.update_resource_item(absolute, status=f"http_{status}")
                return ref
            content_type = headers.get("content-type", "").split(";")[0].lower()
            local_path = self.mime_adjusted_asset_public_path(absolute, current_host, local_path, content_type)
            item.public_path = local_path
            max_bytes = self.config.crawl_policy.max_asset_size_mb * 1024 * 1024
            if len(body) > max_bytes:
                self.asset_records.append({"url": absolute, "status": "too_large", "page": page_url, "size": len(body)})
                self.update_resource_item(absolute, status="too_large", size=len(body))
                return ref
            if content_type == "text/css" or ext == ".css":
                body = self.rewrite_css(body, absolute, current_host)
            elif is_javascript_resource(content_type, ext):
                body = self.rewrite_js(body, absolute, current_host)
            content_hash = sha256_hex(body)
            if reusable_existing and item.content_hash == content_hash:
                state.assets_done.add(absolute)
                self.asset_records.append(
                    {
                        "url": absolute,
                        "host": current_host,
                        "public_path": local_path,
                        "content_type": content_type,
                        "size": len(body),
                        "hash": content_hash,
                        "status": "unchanged",
                    }
                )
                self.update_resource_item(
                    absolute,
                    status="unchanged",
                    content_type=content_type,
                    size=len(body),
                    content_hash=content_hash,
                    etag=headers.get("etag") or item.etag,
                    last_modified=headers.get("last-modified") or item.last_modified,
                    error=None,
                    last_checked_at=datetime.now(timezone.utc).isoformat(),
                )
                return local_path
            self.write_asset_variants(current_host, local_path, body)
            state.assets_done.add(absolute)
            self.asset_records.append(
                {
                    "url": absolute,
                    "host": current_host,
                    "public_path": local_path,
                    "content_type": content_type,
                    "size": len(body),
                    "hash": content_hash,
                    "status": "saved",
                }
            )
            self.update_resource_item(
                absolute,
                status="saved",
                content_type=content_type,
                size=len(body),
                content_hash=content_hash,
                etag=headers.get("etag"),
                last_modified=headers.get("last-modified"),
                error=None,
                last_checked_at=datetime.now(timezone.utc).isoformat(),
            )
            return local_path
        except Exception as exc:
            self.asset_records.append({"url": absolute, "status": "error", "page": page_url, "error": str(exc)})
            self.update_resource_item(absolute, status="error", error=str(exc))
            return ref

    def rewrite_css(self, body: bytes, css_url: str, current_host: str) -> bytes:
        text = body.decode("utf-8", errors="replace")

        def repl(match: re.Match[str]) -> str:
            raw = match.group(1).strip().strip("'\"")
            if raw.startswith(("data:", "blob:", "#")):
                return match.group(0)
            absolute = normalize_url(urllib.parse.urljoin(css_url, raw))
            if not absolute:
                return match.group(0)
            local = self.download_asset_ref(absolute, f"https://{current_host}/")
            return f"url({local})" if local else match.group(0)

        text = re.sub(r"url\(([^)]+)\)", repl, text)

        def import_repl(match: re.Match[str]) -> str:
            prefix, quote, raw = match.group(1), match.group(2), match.group(3)
            if raw.startswith(("data:", "blob:", "#")):
                return match.group(0)
            absolute = normalize_url(urllib.parse.urljoin(css_url, raw))
            if not absolute:
                return match.group(0)
            local = self.download_asset_ref(absolute, f"https://{current_host}/")
            return f"{prefix}{quote}{local}{quote}" if local else match.group(0)

        text = re.sub(r"(@import\s+)(['\"])([^'\"]+)(?:\2)", import_repl, text)
        return text.encode("utf-8")

    def rewrite_js(self, body: bytes, js_url: str, current_host: str) -> bytes:
        text = body.decode("utf-8", errors="replace")
        static_ext_pattern = "|".join(re.escape(ext.lstrip(".")) for ext in sorted(STATIC_RESOURCE_EXTENSIONS, key=len, reverse=True))
        pattern = re.compile(
            rf"(?P<quote>['\"`])(?P<url>(?:https?://|/|\./|\.\./)[^'\"`\\\s]+?\.({static_ext_pattern})(?:\?[^'\"`\\\s]*)?)(?P=quote)",
            re.IGNORECASE,
        )
        next_image_pattern = re.compile(
            r"(?P<quote>['\"`])(?P<url>(?:https?://[^'\"`\\\s]+)?/_next/image\?url=[^'\"`\\\s]+)(?P=quote)",
            re.IGNORECASE,
        )

        def repl(match: re.Match[str]) -> str:
            quote = match.group("quote")
            raw = match.group("url")
            if raw.startswith(("data:", "blob:")):
                return match.group(0)
            absolute = normalize_url(urllib.parse.urljoin(js_url, raw))
            if not absolute:
                return match.group(0)
            local = self.download_asset_ref(absolute, f"https://{current_host}/")
            return f"{quote}{local}{quote}" if local else match.group(0)

        text = pattern.sub(repl, text)
        text = next_image_pattern.sub(repl, text)
        return text.encode("utf-8")

    def should_download_asset(self, value: str) -> bool:
        return not value.startswith(("data:", "blob:", "#", "mailto:", "tel:", "javascript:"))

    def effective_asset_url(self, absolute: str, page_url: str) -> str | None:
        parsed = urllib.parse.urlparse(absolute)
        nested = self.extract_nested_asset_url(parsed, page_url)
        if nested:
            return nested
        if parsed.path != "/_next/image":
            return None
        query = urllib.parse.parse_qs(parsed.query)
        nested = query.get("url", [""])[0]
        if not nested:
            return None
        nested_url = urllib.parse.unquote(nested)
        normalized = normalize_url(urllib.parse.urljoin(page_url, nested_url))
        return normalized or None

    def extract_nested_asset_url(self, parsed: urllib.parse.ParseResult, page_url: str) -> str | None:
        query = urllib.parse.parse_qs(parsed.query)
        for key in ("url", "src", "image", "media", "asset"):
            nested = query.get(key, [""])[0]
            if not nested:
                continue
            nested_url = urllib.parse.unquote(nested)
            normalized = normalize_url(urllib.parse.urljoin(page_url, nested_url))
            if normalized:
                return normalized
        return None

    def save_asset(self, url: str, current_page_url: str, body: bytes, content_type: str) -> None:
        current_host = urllib.parse.urlparse(current_page_url).hostname or ""
        local_path = self.asset_public_path(url, current_host)
        self.write_asset_variants(current_host, local_path, body)
        self.asset_records.append(
            {
                "url": url,
                "host": current_host,
                "public_path": local_path,
                "content_type": content_type,
                "size": len(body),
                "hash": sha256_hex(body),
                "status": "saved",
            }
        )
        self.ensure_resource_item(url, current_host, current_page_url, local_path)
        self.update_resource_item(url, status="saved", content_type=content_type, size=len(body), content_hash=sha256_hex(body))

    def asset_public_path(self, asset_url: str, current_host: str) -> str:
        parsed = urllib.parse.urlparse(asset_url)
        asset_host = parsed.hostname or current_host
        query_digest = hashlib.sha256(asset_url.encode("utf-8")).hexdigest()[:16] if parsed.query else ""
        if self.is_allowed_host(asset_host) and asset_host == current_host:
            path = parsed.path or "/"
            if path.endswith("/"):
                path = posixpath.join(path, "index")
            if parsed.query and not Path(path).suffix:
                suffix = ".bin"
                return ensure_leading_slash(posixpath.join(path, query_digest + suffix))
            return ensure_leading_slash(path)
        safe_host = safe_segment(asset_host)
        path = parsed.path or "/asset"
        if path.endswith("/"):
            path = posixpath.join(path, "index")
        suffix = Path(path).suffix
        if not suffix:
            suffix = mimetypes.guess_extension("") or ".bin"
        digest = hashlib.sha256(asset_url.encode("utf-8")).hexdigest()[:16]
        return f"/__external_assets/{safe_host}/{digest}{suffix}"

    def mime_adjusted_asset_public_path(self, asset_url: str, current_host: str, public_path: str, content_type: str) -> str:
        suffix = Path(urllib.parse.urlparse(public_path).path).suffix.lower()
        if suffix and suffix != ".bin":
            return public_path
        preferred = preferred_extension_for_content_type(content_type)
        if not preferred:
            return public_path
        parsed = urllib.parse.urlparse(asset_url)
        asset_host = parsed.hostname or current_host
        if self.is_allowed_host(asset_host) and asset_host == current_host:
            base = posixpath.splitext(public_path)[0]
            return base + preferred
        safe_host = safe_segment(asset_host)
        digest = hashlib.sha256(asset_url.encode("utf-8")).hexdigest()[:16]
        return f"/__external_assets/{safe_host}/{digest}{preferred}"

    def write_asset_variants(self, host: str, public_path: str, body: bytes) -> None:
        for variant in ("site", "local_preview"):
            path = self.host_root(host, variant) / public_path_file_path(public_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)

    def repair_missing_local_static_refs(self) -> None:
        """Copy only static files that a final HTML page references but its host lacks."""
        copied = 0
        for item in sorted(self.crawl_table.values(), key=lambda entry: (entry.host, entry.url)):
            if item.status not in PAGE_REUSABLE_STATUSES:
                continue
            for variant, relative_path in (("site", item.deploy_path), ("local_preview", item.local_preview_path)):
                if not relative_path:
                    continue
                page_path = self.original_dir / relative_path
                if not page_path.exists():
                    continue
                host_root = self.host_root(item.host, variant)
                for ref in self.local_static_refs_in_html(page_path):
                    parsed = urllib.parse.urlparse(ref)
                    target = host_root / parsed.path.lstrip("/")
                    if target.exists():
                        continue
                    source = self.find_existing_static_file(parsed.path, variant, exclude_host=item.host)
                    if not source:
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied += 1
        if copied:
            self.asset_records.append({"status": "missing_local_static_refs_repaired", "copied": copied})

    def find_existing_static_file(self, public_path: str, variant: str, exclude_host: str | None = None) -> Path | None:
        relative = public_path_file_path(public_path)
        for host in sorted(self.hosts):
            if exclude_host and host == exclude_host:
                continue
            candidate = self.host_root(host, variant) / relative
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    def write_page_variants(self, url: str, deploy_soup: BeautifulSoup) -> None:
        local_soup = BeautifulSoup(str(deploy_soup), "html5lib")
        self.apply_mode_links(local_soup, url, mode="local")
        self.apply_mode_links(deploy_soup, url, mode="deploy")
        self.inject_runtime_link_rewriter(deploy_soup)

        local_path = self.output_page_path(url, "local_preview")
        deploy_path = self.output_page_path(url, "site")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(str(local_soup), encoding="utf-8")
        deploy_path.write_text(str(deploy_soup), encoding="utf-8")

    def apply_mode_links(self, soup: BeautifulSoup, page_url: str, mode: str) -> None:
        for tag in soup.find_all("a", href=True):
            original = tag.get("data-replication-local-href" if mode == "local" else "data-replication-deploy-href")
            if original:
                target = str(original)
                if mode == "local":
                    tag["href"] = target
                    continue
                target_parsed = urllib.parse.urlparse(target)
                page_host = urllib.parse.urlparse(page_url).hostname or ""
                if target_parsed.hostname == page_host:
                    tag["href"] = urllib.parse.urlunparse(
                        ("", "", target_parsed.path or "/", "", target_parsed.query, target_parsed.fragment)
                    )
                else:
                    tag["href"] = target

    def rewrite_link_for_mode(self, target_url: str, page_url: str, mode: str, already_public: bool = False) -> str:
        if already_public:
            if mode == "local":
                return target_url
            return target_url
        parsed = urllib.parse.urlparse(target_url)
        target_host = parsed.hostname or ""
        page_host = urllib.parse.urlparse(page_url).hostname or ""
        path_query = urllib.parse.urlunparse(("", "", parsed.path or "/", "", parsed.query, parsed.fragment))
        if target_host == page_host:
            return path_query
        if mode == "local":
            state = self.ensure_host(target_host)
            return f"http://localhost:{state.local_port}{path_query}"
        deploy_host = self.deploy_host(target_host)
        return urllib.parse.urlunparse((self.config.deployment.scheme, deploy_host, parsed.path or "/", "", parsed.query, parsed.fragment))

    def output_page_path(self, url: str, variant: str) -> Path:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path or "/"
        if parsed.query:
            self.query_records.append(
                {
                    "url": url,
                    "host": host,
                    "path": path,
                    "query": parsed.query,
                    "strategy": self.config.static_policy.query_strategy,
                }
            )
            path = query_static_path(path, parsed.query)
        return self.host_root(host, variant) / page_file_path(path)

    def host_root(self, host: str, variant: str) -> Path:
        return self.hosts_dir / host / variant

    def public_url(self, url: str, mode: str) -> str:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        path_query = urllib.parse.urlunparse(("", "", parsed.path or "/", "", parsed.query, parsed.fragment))
        if mode == "local":
            state = self.ensure_host(host)
            return f"http://localhost:{state.local_port}{path_query}"
        return urllib.parse.urlunparse(
            (self.config.deployment.scheme, self.deploy_host(host), parsed.path or "/", "", parsed.query, parsed.fragment)
        )

    def enqueue_page(self, url: str, depth: int, discovered_from: str | None = None) -> None:
        with self._state_lock:
            url = self.canonicalize_crawl_url(url)
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname or ""
            if not self.is_allowed_host(host):
                return
            state = self.ensure_host(host)
            item = self.ensure_crawl_item(url, depth, discovered_from)
            if url in state.pages_seen or url in state.pages_done:
                return
            state.pages_seen.add(url)
            if item.status not in PAGE_REUSABLE_STATUSES:
                self.update_crawl_item(url, status="queued")
            self.queue.append((url, depth))

    def ensure_crawl_item(self, url: str, depth: int, discovered_from: str | None) -> CrawlItem:
        with self._state_lock:
            if url in self.crawl_table:
                item = self.crawl_table[url]
                if depth < item.depth:
                    item.depth = depth
                return item
            parsed = urllib.parse.urlparse(url)
            item = CrawlItem(
                url=url,
                host=parsed.hostname or "",
                depth=depth,
                discovered_from=discovered_from,
                local_preview_url=self.public_url(url, "local"),
                deploy_url=self.public_url(url, "deploy"),
                local_preview_path=str(self.output_page_path(url, "local_preview").relative_to(self.original_dir)),
                deploy_path=str(self.output_page_path(url, "site").relative_to(self.original_dir)),
            )
            self.crawl_table[url] = item
            self.rewrite_map[url] = {
                "source_url": url,
                "source_host": item.host,
                "source_path": urllib.parse.urlparse(url).path or "/",
                "local_preview_url": item.local_preview_url,
                "deploy_url": item.deploy_url,
                "local_preview_path": item.local_preview_path,
                "deploy_path": item.deploy_path,
                "status": item.status,
            }
            return item

    def canonicalize_crawl_url(self, url: str) -> str:
        normalized = normalize_url(url)
        if not normalized:
            return url
        parsed = urllib.parse.urlparse(normalized)
        target_scheme = urllib.parse.urlparse(self.config.target_url).scheme
        if target_scheme == "https" and parsed.scheme == "http" and self.is_allowed_host(parsed.hostname or ""):
            return urllib.parse.urlunparse(parsed._replace(scheme="https"))
        return normalized

    def update_crawl_item(self, url: str, **updates: Any) -> None:
        with self._state_lock:
            item = self.crawl_table.get(url)
            if not item:
                item = self.ensure_crawl_item(url, 0, None)
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            item.updated_at = datetime.now(timezone.utc).isoformat()
            if url in self.rewrite_map:
                self.rewrite_map[url].update(
                    {
                        "local_preview_url": item.local_preview_url,
                        "deploy_url": item.deploy_url,
                        "local_preview_path": item.local_preview_path,
                        "deploy_path": item.deploy_path,
                        "status": item.status,
                    }
                )

    def ensure_resource_item(self, url: str, host: str, page_url: str, public_path: str) -> ResourceItem:
        with self._state_lock:
            if url in self.resource_table:
                return self.resource_table[url]
            item = ResourceItem(url=url, host=host, page_url=page_url, public_path=public_path)
            self.resource_table[url] = item
            return item

    def update_resource_item(self, url: str, **updates: Any) -> None:
        with self._state_lock:
            item = self.resource_table.get(url)
            if not item:
                return
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            item.updated_at = datetime.now(timezone.utc).isoformat()

    def ensure_host(self, host: str) -> HostState:
        with self._state_lock:
            if host in self.hosts:
                return self.hosts[host]
            port = self.next_available_port(self.config.local_preview.host_port_map.get(host))
            state = HostState(source_host=host, local_port=port, deploy_host=self.deploy_host(host))
            self.hosts[host] = state
            for variant in ("site", "local_preview"):
                self.host_root(host, variant).mkdir(parents=True, exist_ok=True)
            return state

    def register_host(self, host: str, local_port: int | None, deploy_host: str | None) -> HostState:
        with self._state_lock:
            if host in self.hosts:
                state = self.hosts[host]
                if local_port is not None:
                    state.local_port = self.next_available_port(local_port, current_host=host)
                if deploy_host:
                    state.deploy_host = deploy_host
                return state
            if local_port is None:
                return self.ensure_host(host)
            state = HostState(
                source_host=host,
                local_port=self.next_available_port(local_port),
                deploy_host=deploy_host or self.deploy_host(host),
            )
            self.hosts[host] = state
            for variant in ("site", "local_preview"):
                self.host_root(host, variant).mkdir(parents=True, exist_ok=True)
            return state

    def next_available_port(self, preferred: int | None = None, current_host: str | None = None) -> int:
        used = {
            state.local_port
            for host, state in self.hosts.items()
            if not current_host or host != current_host
        }
        port = preferred if preferred is not None else self.config.local_preview.port_start
        while port in used:
            port += 1
        return port

    def configured_deploy_mapping_enabled(self) -> bool:
        return bool(self.config.deployment.target_host_map or self.config.deployment.target_base_domain)

    def deploy_host(self, host: str) -> str:
        mapped = self.config.deployment.target_host_map.get(host)
        if mapped:
            return mapped
        target_base = self.config.deployment.target_base_domain
        root = self.config.domain_policy.root_domain
        if target_base and (host == root or host.endswith("." + root)):
            prefix = host[: -len(root)].rstrip(".")
            return f"{prefix}.{target_base}" if prefix else target_base
        return host

    def is_allowed_host(self, host: str) -> bool:
        if not host:
            return False
        host = host.lower()
        policy = self.config.domain_policy
        if host in {item.lower() for item in policy.exclude}:
            return False
        if policy.include and host in {item.lower() for item in policy.include}:
            return True
        if host == policy.root_domain:
            return True
        return policy.include_subdomains and host.endswith("." + policy.root_domain)

    def can_fetch(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{parsed.scheme}://{host}/robots.txt")
            try:
                status, _, body = self.curl_request(
                    f"{parsed.scheme}://{parsed.netloc}/robots.txt",
                    {"User-Agent": USER_AGENT},
                )
                if status == 200:
                    rp.parse(body.decode("utf-8", errors="replace").splitlines())
            except Exception:
                pass
            self.robots[host] = rp
        if not self.robots[host].entries and self.robots[host].default_entry is None:
            return True
        return self.robots[host].can_fetch(USER_AGENT, url)

    def browser(self) -> Any:
        if self._browser:
            return self._browser
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise RuntimeError("Python Playwright is not installed. Install it in .venv and run playwright install chromium.") from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        return self._browser

    def close_browser(self) -> None:
        if self._browser:
            try:
                self._browser.close()
            except BaseException:
                pass
            self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except BaseException:
                pass
            self._playwright = None

    def render_dynamic_page(self, url: str) -> RenderResult | None:
        policy = self.config.crawl_policy
        try:
            browser = self.browser()
        except Exception as exc:
            self.errors.append({"type": "browser_unavailable", "url": url, "error": str(exc)})
            return None

        context = browser.new_context(
            viewport={"width": 1365, "height": 900},
            device_scale_factor=1,
            user_agent=USER_AGENT,
        )
        page = context.new_page()
        resource_urls: set[str] = set()
        page.on("response", lambda response: resource_urls.add(response.url))
        status_code: int | None = None
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=policy.dynamic_timeout_seconds * 1000)
            status_code = response.status if response else None
            try:
                page.wait_for_load_state("networkidle", timeout=policy.dynamic_network_idle_timeout_ms)
            except Exception:
                pass
            if policy.dynamic_wait_ms > 0:
                page.wait_for_timeout(policy.dynamic_wait_ms)
            self.expand_lazy_content(page)
            self.safe_reveal_interactive_content(page)
            discovered_urls = self.collect_browser_links(page)
            resource_urls.update(self.collect_browser_resources(page))
            html_text = page.content()
            screenshot_path = self.capture_source_screenshot(page, url)
            return RenderResult(
                html=html_text,
                final_url=page.url,
                status_code=status_code,
                content_hash=sha256_hex(html_text),
                screenshot_path=screenshot_path,
                discovered_urls=discovered_urls,
                resource_urls=sorted(resource_urls),
            )
        except Exception as exc:
            self.errors.append({"type": "render_failed", "url": url, "error": str(exc)})
            return None
        finally:
            try:
                context.close()
            except Exception:
                pass

    def expand_lazy_content(self, page: Any) -> None:
        policy = self.config.crawl_policy
        last_height = 0
        for _ in range(max(0, policy.dynamic_scroll_rounds)):
            try:
                height = int(page.evaluate("() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"))
                viewport_height = int(page.evaluate("() => window.innerHeight || 800"))
                step = max(300, viewport_height // 2)
                for y in range(0, height + step, step):
                    page.evaluate(
                        "y => { window.scrollTo(0, y); window.dispatchEvent(new Event('scroll')); }",
                        y,
                    )
                    page.wait_for_timeout(max(150, policy.dynamic_wait_ms // 4))
                if height == last_height:
                    break
                last_height = height
            except Exception:
                break
        try:
            page.evaluate("() => window.scrollTo(0, 0)")
        except Exception:
            pass

    def safe_reveal_interactive_content(self, page: Any) -> None:
        policy = self.config.crawl_policy
        if policy.dynamic_click_rounds <= 0 or policy.dynamic_click_limit <= 0:
            return
        script = """
        ({limit}) => {
          const deny = /(sign|login|log in|logout|subscribe|buy|purchase|cart|checkout|download|submit|send|delete|remove|close)/i;
          const visible = (el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
          };
          const candidates = Array.from(document.querySelectorAll(
            'button,[role="button"],summary,[aria-expanded="false"],[data-state="closed"],nav [aria-haspopup="true"],header [aria-haspopup="true"]'
          ));
          let clicked = 0;
          for (const el of candidates) {
            if (clicked >= limit) break;
            const text = `${el.innerText || ''} ${el.getAttribute('aria-label') || ''} ${el.getAttribute('title') || ''}`;
            const type = (el.getAttribute('type') || '').toLowerCase();
            if (!visible(el) || type === 'submit' || deny.test(text)) continue;
            try {
              el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
              el.click();
              clicked += 1;
            } catch (_) {}
          }
          return clicked;
        }
        """
        for _ in range(policy.dynamic_click_rounds):
            try:
                clicked = int(page.evaluate(script, {"limit": policy.dynamic_click_limit}))
            except Exception:
                break
            if clicked <= 0:
                break
            try:
                page.wait_for_timeout(max(300, policy.dynamic_wait_ms // 2))
            except Exception:
                break

    def collect_browser_links(self, page: Any) -> list[str]:
        try:
            urls = page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(Boolean)")
        except Exception:
            return []
        return sorted({str(item) for item in urls if isinstance(item, str)})

    def collect_browser_resources(self, page: Any) -> list[str]:
        script = """
        () => {
          const urls = new Set(performance.getEntriesByType('resource').map(entry => entry.name));
          document.querySelectorAll('[src],[href],[poster],[content]').forEach(el => {
            for (const attr of ['src', 'href', 'poster', 'content']) {
              const value = el.getAttribute(attr);
              if (!value) continue;
              try { urls.add(new URL(value, document.baseURI).href); } catch (_) {}
            }
          });
          return Array.from(urls).filter(Boolean);
        }
        """
        try:
            urls = page.evaluate(script)
        except Exception:
            return []
        return sorted({str(item) for item in urls if isinstance(item, str)})

    def capture_source_screenshot(self, page: Any, url: str) -> str | None:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "unknown"
        path = self.snapshots_dir / "screenshots" / "source" / host / (sha256_hex(url)[:16] + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(path), full_page=True)
        except Exception as exc:
            self.errors.append({"type": "source_screenshot_failed", "url": url, "error": str(exc)})
            return None
        return str(path.relative_to(self.original_dir))

    def request(
        self,
        url: str,
        allow_robots: bool = True,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        if allow_robots and self.config.crawl_policy.respect_robots and not self.can_fetch(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        state = self.ensure_host(host) if self.is_allowed_host(host) else None
        request_headers = {"User-Agent": USER_AGENT}
        if headers:
            request_headers.update(headers)
        if not state:
            return self.curl_request(url, request_headers)
        with state.request_lock:
            wait = self.config.crawl_policy.rate_limit_per_host - (time.time() - state.last_request_at)
            if wait > 0:
                time.sleep(wait)
            state.last_request_at = time.time()
            return self.curl_request(url, request_headers)

    def curl_request(self, url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        timeout = max(1, int(self.config.crawl_policy.timeout_seconds))
        connect_timeout = max(1, min(5, timeout))
        header_file = tempfile.NamedTemporaryFile(prefix="replication_headers_", dir="/tmp", delete=False)
        body_file = tempfile.NamedTemporaryFile(prefix="replication_body_", dir="/tmp", delete=False)
        header_path = Path(header_file.name)
        body_path = Path(body_file.name)
        header_file.close()
        body_file.close()
        cmd = [
            "curl",
            "--location",
            "--max-redirs",
            "8",
            "--silent",
            "--show-error",
            "--compressed",
            "--max-time",
            str(timeout),
            "--connect-timeout",
            str(connect_timeout),
            "--speed-limit",
            "1024",
            "--speed-time",
            str(max(3, min(8, timeout))),
            "--retry",
            "0",
            "--dump-header",
            str(header_path),
            "--output",
            str(body_path),
        ]
        for key, value in headers.items():
            cmd.extend(["--header", f"{key}: {value}"])
        cmd.extend(["--write-out", "%{http_code}", "--url", url])
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout + 2)
            except subprocess.TimeoutExpired as exc:
                self.kill_process_group(process)
                raise TimeoutError(f"curl timed out after {timeout + 2}s: {url}") from exc
            if process.returncode != 0:
                message = stderr.strip() or f"curl exit {process.returncode}"
                raise TimeoutError(message) if process.returncode == 28 else urllib.error.URLError(message)
            status = int((stdout or "0").strip()[-3:] or "0")
            response_headers = parse_curl_headers(header_path.read_text(encoding="iso-8859-1", errors="replace"))
            body = body_path.read_bytes()
            if status >= 400:
                raise urllib.error.HTTPError(url, status, f"HTTP Error {status}", response_headers, None)
            return status, response_headers, body
        finally:
            for path in (header_path, body_path):
                try:
                    path.unlink()
                except OSError:
                    pass

    def kill_process_group(self, process: subprocess.Popen[str]) -> None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            try:
                process.kill()
            except OSError:
                pass
        try:
            process.communicate(timeout=1)
        except Exception:
            pass

    def save_snapshot(self, url: str, body: bytes) -> None:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "unknown"
        snapshot_path = self.snapshots_dir / "html" / host / (sha256_hex(url.encode("utf-8"))[:16] + ".html")
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_bytes(body)

    def conditional_headers(self, item: CrawlItem | ResourceItem | None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if not item:
            return headers
        if item.etag:
            headers["If-None-Match"] = item.etag
        if item.last_modified:
            headers["If-Modified-Since"] = item.last_modified
        return headers

    def page_outputs_exist(self, item: CrawlItem) -> bool:
        if not item.local_preview_path or not item.deploy_path:
            return False
        return (self.original_dir / item.local_preview_path).exists() and (self.original_dir / item.deploy_path).exists()

    def asset_outputs_exist(self, item: ResourceItem) -> bool:
        relative = public_path_file_path(item.public_path)
        return (
            (self.host_root(item.host, "local_preview") / relative).exists()
            and (self.host_root(item.host, "site") / relative).exists()
        )

    def record_unchanged_page(
        self,
        url: str,
        item: CrawlItem,
        status_code: int | None,
        content_hash: str | None,
        headers: dict[str, str] | None = None,
    ) -> None:
        parsed = urllib.parse.urlparse(url)
        local_preview_url = item.local_preview_url or self.public_url(url, "local")
        deploy_url = item.deploy_url or self.public_url(url, "deploy")
        local_preview_path = item.local_preview_path or str(self.output_page_path(url, "local_preview").relative_to(self.original_dir))
        deploy_path = item.deploy_path or str(self.output_page_path(url, "site").relative_to(self.original_dir))
        self.page_records.append(
            PageRecord(
                url=url,
                source_host=parsed.hostname or "",
                source_path=parsed.path or "/",
                local_preview_url=local_preview_url,
                deploy_url=deploy_url,
                local_preview_path=local_preview_path,
                deploy_path=deploy_path,
                status_code=status_code,
                content_hash=content_hash,
                render_mode="http",
                internal_links=0,
                external_links=0,
                assets=0,
                status="unchanged",
            )
        )
        headers = headers or {}
        self.update_crawl_item(
            url,
            status="unchanged",
            local_preview_url=local_preview_url,
            deploy_url=deploy_url,
            local_preview_path=local_preview_path,
            deploy_path=deploy_path,
            status_code=status_code,
            content_hash=content_hash,
            etag=headers.get("etag") or item.etag,
            last_modified=headers.get("last-modified") or item.last_modified,
            error=None,
            last_checked_at=datetime.now(timezone.utc).isoformat(),
        )
        self.flush_progress_tables()

    def run_visual_validation(self) -> None:
        servers, preview_ports = self.start_local_preview_servers()
        try:
            pages = [
                record
                for record in self.page_records
                if record.status in {"verified", "unchanged"} and record.local_preview_url
            ][: self.config.visual_policy.sample_pages]
            for record in pages:
                for viewport in self.config.visual_policy.viewports:
                    self.visual_records.append(self.compare_page_visual(record, viewport, preview_ports))
        finally:
            for server in servers:
                try:
                    server.shutdown()
                    server.server_close()
                except Exception:
                    pass
        self.write_visual_report()

    def start_local_preview_servers(self) -> tuple[list[Any], dict[str, int]]:
        servers: list[Any] = []
        ports: dict[str, int] = {}
        for state in sorted(self.hosts.values(), key=lambda item: item.source_host):
            directory = self.host_root(state.source_host, "local_preview")
            if not directory.exists():
                continue
            handler = functools.partial(QuietHandler, directory=str(directory))
            try:
                server = ReusableTCPServer(("127.0.0.1", 0), handler)
            except OSError as exc:
                self.errors.append(
                    {
                        "type": "visual_preview_server_unavailable",
                        "host": state.source_host,
                        "error": str(exc),
                    }
                )
                continue
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            servers.append(server)
            ports[state.source_host] = int(server.server_address[1])
        return servers, ports

    def compare_page_visual(self, record: PageRecord, viewport: Viewport, preview_ports: dict[str, int]) -> dict[str, Any]:
        base = self.snapshots_dir / "visual" / viewport.name / safe_segment(record.source_host)
        source_path = base / "source" / (sha256_hex(record.url)[:16] + ".png")
        local_path = base / "local" / (sha256_hex(record.url)[:16] + ".png")
        diff_path = base / "diff" / (sha256_hex(record.url)[:16] + ".png")
        source_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.parent.mkdir(parents=True, exist_ok=True)

        source_ok = self.capture_url_screenshot(record.url, source_path, viewport)
        visual_local_url = self.visual_local_url(record, preview_ports)
        local_ok = self.capture_url_screenshot(visual_local_url, local_path, viewport)
        result: dict[str, Any] = {
            "url": record.url,
            "local_preview_url": record.local_preview_url,
            "visual_local_url": visual_local_url,
            "viewport": dataclasses.asdict(viewport),
            "source_screenshot": str(source_path.relative_to(self.original_dir)) if source_ok else None,
            "local_screenshot": str(local_path.relative_to(self.original_dir)) if local_ok else None,
            "diff_screenshot": None,
            "diff_ratio": None,
            "status": "screenshot_failed" if not (source_ok and local_ok) else "pending",
            "vision_result": None,
        }
        if source_ok and local_ok:
            diff = compare_images(source_path, local_path, diff_path)
            result.update(diff)
            result["diff_screenshot"] = str(diff_path.relative_to(self.original_dir)) if diff.get("diff_written") else None
            diff_ratio = diff.get("diff_ratio")
            result["status"] = (
                "passed"
                if diff_ratio is not None and float(diff_ratio) <= self.config.visual_policy.diff_threshold
                else "needs_review"
            )
            if self.config.visual_policy.use_vision_model:
                result["vision_result"] = self.call_vision_model(source_path, local_path, record.url)
        return result

    def visual_local_url(self, record: PageRecord, preview_ports: dict[str, int]) -> str:
        port = preview_ports.get(record.source_host)
        if not port:
            return record.local_preview_url
        parsed = urllib.parse.urlparse(record.local_preview_url)
        return urllib.parse.urlunparse(("http", f"127.0.0.1:{port}", parsed.path or "/", "", parsed.query, parsed.fragment))

    def capture_url_screenshot(self, url: str, path: Path, viewport: Viewport) -> bool:
        context: Any = None
        try:
            browser = self.browser()
            screenshot_timeout = max(3000, min(10000, self.config.crawl_policy.dynamic_timeout_seconds * 1000))
            context = browser.new_context(
                viewport={"width": viewport.width, "height": viewport.height},
                device_scale_factor=1,
                user_agent=USER_AGENT,
            )
            page = context.new_page()
            page.goto(url, wait_until="commit", timeout=screenshot_timeout)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=screenshot_timeout)
            except Exception:
                pass
            try:
                page.wait_for_load_state("networkidle", timeout=min(3000, self.config.crawl_policy.dynamic_network_idle_timeout_ms))
            except Exception:
                pass
            if self.config.visual_policy.wait_ms > 0:
                page.wait_for_timeout(self.config.visual_policy.wait_ms)
            page.screenshot(path=str(path), full_page=self.config.visual_policy.full_page, timeout=screenshot_timeout)
            return True
        except Exception as exc:
            self.errors.append({"type": "visual_screenshot_failed", "url": url, "error": str(exc)})
            return False
        finally:
            if context:
                try:
                    context.close()
                except BaseException:
                    pass

    def call_vision_model(self, source_path: Path, local_path: Path, page_url: str) -> dict[str, Any]:
        policy = self.config.visual_policy
        api_key = os.environ.get(policy.vision_api_key_env)
        if not policy.vision_api_url or not policy.vision_model or not api_key:
            return {"status": "skipped", "reason": "vision_model_not_configured"}
        endpoint = policy.vision_api_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint = endpoint + "/chat/completions"
        prompt = (
            "Compare the source website screenshot and replicated local screenshot. "
            "Return compact JSON with fields: consistent(boolean), severity(low|medium|high), "
            "issues(array), summary(string). Focus on missing content, broken layout, missing images, "
            "incorrect spacing, blank regions, and obvious visual regressions."
        )
        payload = {
            "model": policy.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Page URL: {page_url}\n{prompt}"},
                        {"type": "image_url", "image_url": {"url": image_data_url(source_path)}},
                        {"type": "image_url", "image_url": {"url": image_data_url(local_path)}},
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 800,
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.crawl_policy.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"status": "completed", "raw": content}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def write_visual_report(self) -> None:
        total = len(self.visual_records)
        failed = sum(1 for item in self.visual_records if item.get("status") not in {"passed"})
        self.write_json(
            "visual_report.json",
            {
                "enabled": self.config.visual_policy.enabled,
                "total": total,
                "passed": total - failed,
                "needs_review": failed,
                "diff_threshold": self.config.visual_policy.diff_threshold,
                "items": self.visual_records,
            },
        )

    def inject_base_comment(self, soup: BeautifulSoup, url: str) -> None:
        if soup.html:
            soup.html["data-replication-source-url"] = url

    def record_page_failure(
        self,
        url: str,
        status: str,
        error: str | None = None,
        status_code: int | None = None,
    ) -> None:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or ""
        record = PageRecord(
            url=url,
            source_host=host,
            source_path=parsed.path or "/",
            local_preview_url=self.public_url(url, "local") if host else url,
            deploy_url=self.public_url(url, "deploy") if host else url,
            local_preview_path="",
            deploy_path="",
            status_code=status_code,
            content_hash=None,
            render_mode="http",
            internal_links=0,
            external_links=0,
            assets=0,
            status=status,
            error=error,
        )
        self.page_records.append(record)
        self.errors.append({"type": status, "url": url, "error": error, "status_code": status_code})
        self.update_crawl_item(url, status=status, error=error, status_code=status_code)

    def verify_internal_link_completeness(self) -> None:
        unresolved: list[dict[str, str]] = []
        for record in self.page_records:
            if record.status not in {"verified", "unchanged"} or not record.deploy_path:
                continue
            page_file = self.original_dir / record.deploy_path
            if not page_file.exists():
                continue
            try:
                soup = BeautifulSoup(page_file.read_text(encoding="utf-8"), "html5lib")
            except Exception as exc:
                unresolved.append({"page": record.url, "link": "", "reason": f"read_failed:{exc}"})
                continue
            for tag in soup.find_all("a", href=True):
                source = str(tag.get("data-replication-original-href") or tag["href"])
                absolute = self.canonicalize_crawl_url(urllib.parse.urljoin(record.url, source))
                if not absolute:
                    continue
                host = urllib.parse.urlparse(absolute).hostname or ""
                if not self.is_allowed_host(host):
                    continue
                item = self.crawl_table.get(absolute)
                if not item:
                    unresolved.append({"page": record.url, "link": absolute, "reason": "not_in_crawl_table"})
                elif item.status in {"queued", "fetching", "discovered"}:
                    unresolved.append({"page": record.url, "link": absolute, "reason": item.status})
        self.unresolved_internal_links = unresolved

    def verify_static_resource_localization(self) -> None:
        residual: list[dict[str, str]] = []
        for item in sorted(self.resource_table.values(), key=lambda entry: (entry.host, entry.url)):
            if item.status in RESOURCE_REUSABLE_STATUSES:
                if not self.asset_outputs_exist(item):
                    residual.append(
                        {
                            "file": item.public_path,
                            "ref": item.url,
                            "reason": "resource_table_output_missing",
                        }
                    )
                continue
            residual.append(
                {
                    "file": item.public_path,
                    "ref": item.url,
                    "reason": item.status or "resource_not_saved",
                }
            )
        residual.extend(self.find_missing_local_static_refs())
        self.residual_static_refs = dedupe_issue_list(residual)

    def find_missing_local_static_refs(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        for item in sorted(self.crawl_table.values(), key=lambda entry: (entry.host, entry.url)):
            if item.status not in PAGE_REUSABLE_STATUSES or not item.deploy_path:
                continue
            page_path = self.original_dir / item.deploy_path
            if not page_path.exists():
                continue
            for ref in self.local_static_refs_in_html(page_path):
                parsed = urllib.parse.urlparse(ref)
                target = self.host_root(item.host, "site") / public_path_file_path(parsed.path)
                if not target.exists():
                    issues.append(
                        {
                            "file": str(page_path.relative_to(self.original_dir)),
                            "ref": ref,
                            "reason": "html_local_static_ref_missing",
                        }
                    )
        return issues

    def local_static_refs_in_html(self, page_path: Path) -> set[str]:
        soup = BeautifulSoup(page_path.read_text(encoding="utf-8", errors="ignore"), "html5lib")
        refs: set[str] = set()
        for tag in soup.find_all(True):
            for attr in ("src", "href", "poster", "data-src"):
                value = tag.get(attr)
                if isinstance(value, str):
                    refs.add(value)
            for attr in ("srcset", "imagesrcset"):
                value = tag.get(attr)
                if isinstance(value, str):
                    refs.update(part.strip().split()[0] for part in value.split(",") if part.strip())
        return {ref for ref in refs if self.is_local_static_ref(ref)}

    def is_local_static_ref(self, ref: str) -> bool:
        if not ref or ref.startswith(("data:", "blob:", "#", "mailto:", "tel:", "javascript:", "//")):
            return False
        parsed = urllib.parse.urlparse(ref)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
            return False
        return Path(parsed.path).suffix.lower() in STATIC_RESOURCE_EXTENSIONS

    def flush_progress_tables(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_progress_flush_at < self._progress_flush_interval_seconds:
            return
        self._last_progress_flush_at = now
        with self._state_lock:
            crawl_items = [
                dataclasses.asdict(item)
                for item in sorted(self.crawl_table.values(), key=lambda entry: (entry.host, entry.depth, entry.url))
            ]
            resource_items = [
                dataclasses.asdict(item)
                for item in sorted(self.resource_table.values(), key=lambda entry: (entry.host, entry.url))
            ]
            rewrite_items = [self.rewrite_map[key] for key in sorted(self.rewrite_map)]
        self.write_json("crawl_table.json", {"items": crawl_items})
        self.write_json("resource_table.json", {"items": resource_items})
        self.write_json("rewrite_map.json", {"items": rewrite_items})

    def page_quality_class(self, item: CrawlItem) -> str:
        if item.status in PAGE_REUSABLE_STATUSES or item.status == "canonicalized":
            return "success"
        if item.status in {"discovered", "queued", "fetching"}:
            return "pending"
        if item.status and item.status.startswith("http_"):
            try:
                code = int(item.status.split("_", 1)[1])
            except (IndexError, ValueError):
                code = item.status_code or 0
            if code in self.config.crawl_policy.terminal_http_statuses:
                return "acceptable_terminal"
        if item.status_code in self.config.crawl_policy.terminal_http_statuses:
            return "acceptable_terminal"
        return "failed"

    def resource_quality_class(self, item: ResourceItem) -> str:
        if item.status in RESOURCE_REUSABLE_STATUSES:
            return "success" if self.asset_outputs_exist(item) else "missing_output"
        if item.status in {"skipped_asset_limit", "too_large"}:
            return "skipped"
        if item.status in {"discovered", "downloading"}:
            return "pending"
        return "failed"

    def compute_quality_report(self) -> dict[str, Any]:
        page_counts = {"success": 0, "acceptable_terminal": 0, "pending": 0, "failed": 0}
        failed_pages: list[dict[str, Any]] = []
        pending_pages: list[dict[str, Any]] = []
        for item in sorted(self.crawl_table.values(), key=lambda entry: (entry.host, entry.depth, entry.url)):
            classification = self.page_quality_class(item)
            page_counts[classification] = page_counts.get(classification, 0) + 1
            if classification == "failed":
                failed_pages.append(dataclasses.asdict(item))
            elif classification == "pending":
                pending_pages.append(dataclasses.asdict(item))

        resource_counts = {"success": 0, "missing_output": 0, "pending": 0, "failed": 0, "skipped": 0}
        failed_resources: list[dict[str, Any]] = []
        for item in sorted(self.resource_table.values(), key=lambda entry: (entry.host, entry.url)):
            classification = self.resource_quality_class(item)
            resource_counts[classification] = resource_counts.get(classification, 0) + 1
            if classification in {"missing_output", "failed", "pending"}:
                failed_resources.append(dataclasses.asdict(item))

        page_gate_total = page_counts["success"] + page_counts["pending"] + page_counts["failed"]
        resource_gate_total = (
            resource_counts["success"]
            + resource_counts["missing_output"]
            + resource_counts["pending"]
            + resource_counts["failed"]
        )
        page_success_rate = safe_ratio(page_counts["success"], page_gate_total)
        resource_success_rate = safe_ratio(resource_counts["success"], resource_gate_total)
        visual_total = len(self.visual_records)
        visual_needs_review = sum(1 for item in self.visual_records if item.get("status") != "passed")

        policy = self.config.quality_policy
        release_blockers: list[str] = []
        if page_counts["pending"]:
            release_blockers.append(f"{page_counts['pending']} pages are still pending")
        if page_counts["failed"]:
            release_blockers.append(f"{page_counts['failed']} pages failed with non-terminal errors")
        if page_success_rate < policy.min_page_success_rate:
            release_blockers.append(f"page success rate {page_success_rate:.4f} below {policy.min_page_success_rate:.4f}")
        if resource_counts["pending"] or resource_counts["failed"] or resource_counts["missing_output"]:
            release_blockers.append(
                f"{resource_counts['pending'] + resource_counts['failed'] + resource_counts['missing_output']} resources are not localized"
            )
        if resource_success_rate < policy.min_resource_success_rate:
            release_blockers.append(
                f"resource success rate {resource_success_rate:.4f} below {policy.min_resource_success_rate:.4f}"
            )
        if len(self.unresolved_internal_links) > policy.max_unresolved_internal_links:
            release_blockers.append(f"{len(self.unresolved_internal_links)} unresolved internal links")
        if len(self.residual_static_refs) > policy.max_residual_resources:
            release_blockers.append(f"{len(self.residual_static_refs)} residual static resource refs")
        if policy.require_visual_pass and (visual_total == 0 or visual_needs_review):
            release_blockers.append(f"visual gate failed: total={visual_total}, needs_review={visual_needs_review}")

        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ready_for_release": not release_blockers,
            "release_blockers": release_blockers,
            "page_success_rate": page_success_rate,
            "resource_success_rate": resource_success_rate,
            "page_counts": page_counts,
            "resource_counts": resource_counts,
            "visual": {
                "enabled": self.config.visual_policy.enabled,
                "total": visual_total,
                "needs_review": visual_needs_review,
                "require_visual_pass": policy.require_visual_pass,
            },
            "failed_pages": failed_pages[:200],
            "pending_pages": pending_pages[:200],
            "failed_resources": failed_resources[:200],
            "thresholds": dataclasses.asdict(policy),
        }

    def write_manifests(self) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        quality_report = self.compute_quality_report()
        asset_records = self.asset_manifest_records()
        manifest = {
            "site_id": self.config.site_id,
            "target_url": self.config.target_url,
            "root_domain": self.config.domain_policy.root_domain,
            "runtime_database": False,
            "deployment_base_root": self.config.deployment.base_root,
            "created_at": created_at,
            "visual_report": "visual_report.json" if self.config.visual_policy.enabled else None,
            "quality_report": "quality_report.json",
            "hosts": [
                {
                    "source_host": state.source_host,
                    "local_port": state.local_port,
                    "deploy_host": state.deploy_host,
                    "site_root": f"hosts/{state.source_host}/site",
                    "local_preview_root": f"hosts/{state.source_host}/local_preview",
                    "pages_discovered": len(state.pages_seen),
                    "pages_done": len(state.pages_done),
                }
                for state in sorted(self.hosts.values(), key=lambda item: item.source_host)
            ],
            "pages": [dataclasses.asdict(record) for record in self.page_records],
        }
        self.write_json("manifest.json", manifest)
        self.write_json(
            "host_manifest.json",
            {
                "hosts": [
                    {
                        "source_host": state.source_host,
                        "pages": sum(1 for record in self.page_records if record.source_host == state.source_host),
                        "assets": sum(1 for record in asset_records if record.get("host") == state.source_host),
                        "local_port": state.local_port,
                        "deploy_host": state.deploy_host,
                        "status": self.host_quality_status(state.source_host),
                    }
                    for state in sorted(self.hosts.values(), key=lambda item: item.source_host)
                ]
            },
        )
        self.write_json("asset_manifest.json", {"assets": asset_records})
        self.write_json("link_graph.json", {"links": self.link_records})
        self.write_json("query_manifest.json", {"queries": unique_dicts(self.query_records)})
        self.flush_progress_tables()
        self.write_json(
            "completeness_report.json",
            {
                "discovered_pages": len(self.crawl_table),
                "replicated_pages": sum(1 for item in self.crawl_table.values() if item.status in {"replicated", "unchanged"}),
                "pending_pages": [
                    dataclasses.asdict(item)
                    for item in self.crawl_table.values()
                    if item.status in {"discovered", "queued", "fetching"}
                ],
                "unresolved_internal_links": self.unresolved_internal_links,
                "residual_static_refs": self.residual_static_refs,
                "complete": quality_report["ready_for_release"],
                "quality_report": "quality_report.json",
            },
        )
        self.write_json("quality_report.json", quality_report)
        self.write_json(
            "crawl_report.json",
            {
                "created_at": created_at,
                "pages_total": len(self.page_records),
                "pages_discovered": len(self.crawl_table),
                "assets_total": len(asset_records),
                "hosts_total": len(self.hosts),
                "visual_total": len(self.visual_records),
                "visual_needs_review": sum(1 for item in self.visual_records if item.get("status") not in {"passed"}),
                "ready_for_release": quality_report["ready_for_release"],
                "release_blockers": quality_report["release_blockers"],
                "errors": self.errors,
            },
        )

    def asset_manifest_records(self) -> list[dict[str, Any]]:
        records = [
            {
                "url": item.url,
                "host": item.host,
                "page": item.page_url,
                "public_path": item.public_path,
                "content_type": item.content_type,
                "size": item.size,
                "hash": item.content_hash,
                "status": item.status,
                "error": item.error,
            }
            for item in sorted(self.resource_table.values(), key=lambda entry: (entry.host, entry.url))
        ]
        if records:
            return records
        return self.asset_records

    def host_quality_status(self, host: str) -> str:
        host_pages = [item for item in self.crawl_table.values() if item.host == host]
        host_resources = [item for item in self.resource_table.values() if item.host == host]
        if any(self.page_quality_class(item) == "failed" for item in host_pages):
            return "failed"
        if any(self.page_quality_class(item) == "pending" for item in host_pages):
            return "pending"
        if any(self.resource_quality_class(item) in {"failed", "pending", "missing_output"} for item in host_resources):
            return "resource_incomplete"
        return "verified"

    def write_json(self, name: str, data: Any) -> None:
        with self._write_lock:
            (self.original_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_deployment_doc(self) -> None:
        rows = []
        for state in sorted(self.hosts.values(), key=lambda item: item.source_host):
            rows.append(
                f"| {state.source_host} | http://localhost:{state.local_port} | "
                f"{state.deploy_host} | hosts/{state.source_host}/site |"
            )
        doc = f"""# 静态复刻部署声明

本复刻产物为纯静态站点，不依赖数据库、后端 API、Redis 或运行时任务队列。

## 复刻目标

- 入口 URL：{self.config.target_url}
- 主域名：{self.config.domain_policy.root_domain}
- 生成时间：{datetime.now(timezone.utc).isoformat()}

## Host 映射

| 原始 Host | 本地预览 | 部署 Host | 静态目录 |
| --- | --- | --- | --- |
{os.linesep.join(rows)}

## 路径规则

- 原始 path 保持不变。
- 本地预览只替换为 `localhost:端口`。
- 线上部署只替换为部署 host。
- 外部域名链接保持原始地址。

## 部署步骤

1. 确认 `quality_report.json` 的 `ready_for_release=true`。
2. 将 `mirror/original` 上传到服务器 `{self.config.deployment.base_root}`。
2. 将 `nginx/mirror.conf` 放入 Nginx 配置目录。
3. 配置部署 Host 的 DNS。
4. 配置 HTTPS 证书。
5. 执行 `nginx -t`。
6. reload Nginx。

可使用脚本：

```bash
.venv/bin/python scripts/deploy_static_mirror.py --mirror-dir {self.original_dir} --ssh-host <server-ip> --ssh-user root --remote-root {self.config.deployment.base_root} --enable-nginx-site --reload-nginx
```

## 更新步骤

1. 运行复刻 Agent 增量同步。
2. 上传变化文件。
3. 如果新增 host，更新 DNS 和 Nginx server block。
4. 执行 `nginx -t && nginx -s reload`。

## 已知限制

- 纯静态复刻不能保证登录、搜索、提交表单、购物车等依赖后端 API 的业务动作可用。
- query 参数影响页面内容时，需要查看 `query_manifest.json`。
- 第三方脚本可能因 CSP、跨域或授权限制无法本地完整运行。
"""
        (self.original_dir / "DEPLOYMENT.md").write_text(doc, encoding="utf-8")

    def write_nginx_configs(self) -> None:
        local_blocks = []
        deploy_blocks = []
        for state in sorted(self.hosts.values(), key=lambda item: item.source_host):
            local_root = (self.host_root(state.source_host, "local_preview")).resolve()
            deploy_root = posixpath.join(self.config.deployment.base_root, "hosts", state.source_host, "site")
            local_blocks.append(nginx_server_block(state.local_port, "localhost", str(local_root)))
            deploy_blocks.append(nginx_server_block(80, state.deploy_host, deploy_root))
        (self.nginx_dir / "local-preview.conf").write_text("\n\n".join(local_blocks) + "\n", encoding="utf-8")
        (self.nginx_dir / "mirror.conf").write_text("\n\n".join(deploy_blocks) + "\n", encoding="utf-8")


def nginx_server_block(port: int, server_name: str, root: str) -> str:
    return f"""server {{
    listen {port};
    server_name {server_name};

    root {root};
    index index.html;

    location / {{
        try_files $uri $uri/ $uri/index.html =404;
    }}

    location ~* \\.(css|js|png|jpg|jpeg|gif|webp|svg|ico|woff|woff2|ttf|otf|mp4|webm|pdf)$ {{
        try_files $uri =404;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}"""


def normalize_rel(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item).lower() for item in value}
    return {item.lower() for item in str(value or "").split()}


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return numerator / denominator


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return ""
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [
        (key, value)
        for key, value in query
        if key not in TRACKING_PARAMS and not key.startswith("utm_")
    ]
    path = parsed.path or "/"
    return urllib.parse.urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            "",
            urllib.parse.urlencode(query),
            "",
        )
    )


def registrable_domain(hostname: str) -> str:
    parts = hostname.lower().split(".")
    if len(parts) <= 2:
        return hostname.lower()
    return ".".join(parts[-2:])


def is_probable_page_url(url: str) -> bool:
    path = urllib.parse.urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in DOCUMENT_EXTENSIONS or suffix in VIDEO_EXTENSIONS:
        return False
    if suffix and suffix not in PAGE_EXTENSIONS:
        return False
    return True


def is_html_response(url: str, content_type: str) -> bool:
    if content_type in {"text/html", "application/xhtml+xml"}:
        return True
    return is_probable_page_url(url) and content_type in {"", "text/plain"}


def is_javascript_resource(content_type: str, ext: str) -> bool:
    return (
        "javascript" in content_type
        or content_type in {"application/ecmascript", "text/ecmascript"}
        or ext in {".js", ".mjs", ".cjs"}
    )


def is_static_resource_url(url: str) -> bool:
    path = urllib.parse.urlparse(url).path
    return Path(path).suffix.lower() in STATIC_RESOURCE_EXTENSIONS


def preferred_extension_for_content_type(content_type: str) -> str | None:
    content_type = content_type.split(";", 1)[0].strip().lower()
    mapping = {
        "text/css": ".css",
        "text/javascript": ".js",
        "application/javascript": ".js",
        "application/x-javascript": ".js",
        "application/json": ".json",
        "image/svg+xml": ".svg",
        "font/woff": ".woff",
        "font/woff2": ".woff2",
        "application/font-woff": ".woff",
        "application/font-woff2": ".woff2",
        "application/pdf": ".pdf",
    }
    if content_type in mapping:
        return mapping[content_type]
    guessed = mimetypes.guess_extension(content_type)
    if guessed in {".jpe", ".jpeg"}:
        return ".jpg"
    return guessed


def decode_body(body: bytes, headers: dict[str, str]) -> str:
    content_type = headers.get("content-type", "")
    match = re.search(r"charset=([^;]+)", content_type, flags=re.I)
    charset = match.group(1) if match else "utf-8"
    return body.decode(charset, errors="replace")


def parse_sitemap_locations(body: bytes) -> list[str]:
    text = body.decode("utf-8", errors="replace")
    return [html.unescape(match) for match in re.findall(r"<loc>\s*([^<]+)\s*</loc>", text, flags=re.I)]


def parse_curl_headers(raw: str) -> dict[str, str]:
    blocks = [block for block in re.split(r"\r?\n\r?\n", raw.strip()) if block.strip()]
    selected = blocks[-1] if blocks else ""
    headers: dict[str, str] = {}
    for line in selected.splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def discover_sitemaps(start_url: str, timeout: int) -> list[str]:
    parsed = urllib.parse.urlparse(start_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    sitemaps = [base + "/sitemap.xml"]
    robots_url = base + "/robots.txt"
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
            robots = response.read().decode("utf-8", errors="replace")
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap = line.split(":", 1)[1].strip()
                if sitemap:
                    sitemaps.append(sitemap)
    except Exception:
        pass
    return list(dict.fromkeys(sitemaps))


def page_file_path(path: str) -> Path:
    if not path or path == "/":
        return Path("index.html")
    clean_path = public_path_file_path(path)
    clean = clean_path.as_posix()
    suffix = Path(clean).suffix
    if suffix and suffix not in PAGE_EXTENSIONS:
        return clean_path
    if suffix in {".html", ".htm"}:
        return clean_path
    return clean_path / "index.html"


def public_path_file_path(public_path: str) -> Path:
    parsed = urllib.parse.urlparse(public_path)
    raw_path = parsed.path or public_path
    if not raw_path.startswith("/"):
        raw_path = "/" + raw_path
    decoded = urllib.parse.unquote(raw_path)
    normalized = posixpath.normpath(decoded)
    if normalized in {"", "/", "."}:
        return Path()
    return Path(normalized.lstrip("/"))


def query_static_path(path: str, query: str) -> str:
    pairs = urllib.parse.parse_qsl(query, keep_blank_values=True)
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
    label = "-".join(f"{safe_segment(k)}-{safe_segment(v)}" for k, v in pairs[:3]) or digest
    label = (label[:80] + "-" + digest) if len(label) > 80 else f"{label}-{digest}"
    base = path if path and path != "/" else "/index"
    return posixpath.join(base, "__query", label)


def ensure_leading_slash(path: str) -> str:
    return path if path.startswith("/") else "/" + path


def safe_segment(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value.strip("-") or "item"


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def unique_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def dedupe_issue_list(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, str]] = []
    for item in items:
        key = (item.get("file", ""), item.get("ref", ""), item.get("reason", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def compare_images(source_path: Path, local_path: Path, diff_path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops
    except Exception as exc:
        return {"status": "pillow_missing", "error": str(exc), "diff_ratio": None, "diff_written": False}
    try:
        source = Image.open(source_path).convert("RGB")
        local = Image.open(local_path).convert("RGB")
        width = max(source.width, local.width)
        height = max(source.height, local.height)
        if source.size != (width, height):
            canvas = Image.new("RGB", (width, height), "white")
            canvas.paste(source, (0, 0))
            source = canvas
        if local.size != (width, height):
            canvas = Image.new("RGB", (width, height), "white")
            canvas.paste(local, (0, 0))
            local = canvas
        diff = ImageChops.difference(source, local)
        histogram = diff.convert("L").histogram()
        changed = sum(count for value, count in enumerate(histogram) if value > 12)
        total = width * height
        diff_ratio = changed / total if total else 1.0
        diff.save(diff_path)
        return {
            "status": "compared",
            "diff_ratio": round(diff_ratio, 6),
            "source_size": [source.width, source.height],
            "local_size": [local.width, local.height],
            "diff_written": True,
        }
    except Exception as exc:
        return {"status": "compare_failed", "error": str(exc), "diff_ratio": None, "diff_written": False}


def image_data_url(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


@contextmanager
def hard_timeout(seconds: int, message: str):
    if seconds <= 0:
        yield
        return

    def handler(signum: int, frame: Any) -> None:
        raise TimeoutError(message)

    previous = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def load_config(args: argparse.Namespace) -> ReplicationConfig:
    data: dict[str, Any] = {}
    if args.config:
        data = json.loads(Path(args.config).read_text(encoding="utf-8"))

    target_url = args.url or data.get("target_url")
    if not target_url:
        raise ValueError("target URL is required")
    parsed = urllib.parse.urlparse(target_url)
    host = parsed.hostname or ""
    root_domain = (
        data.get("domain_policy", {}).get("root_domain")
        or args.root_domain
        or registrable_domain(host)
    )
    site_id = args.site_id or data.get("site_id") or safe_segment(root_domain)
    out_dir = Path(args.out_dir or data.get("out_dir") or ROOT / "output" / site_id).resolve()

    domain_data = data.get("domain_policy", {})
    crawl_data = data.get("crawl_policy", {})
    static_data = data.get("static_policy", {})
    local_data = data.get("local_preview", {})
    deploy_data = data.get("deployment", {})
    visual_data = data.get("visual_policy", {})
    quality_data = data.get("quality_policy", {})
    authorization_data = data.get("authorization_policy", {})

    domain_policy = DomainPolicy(
        root_domain=root_domain,
        include_subdomains=domain_data.get("include_subdomains", True),
        include=domain_data.get("include", []),
        exclude=domain_data.get("exclude", []),
    )
    if host and host not in domain_policy.include:
        domain_policy.include.append(host)

    crawl_policy = CrawlPolicy(
        respect_robots=args.no_robots is False and crawl_data.get("respect_robots", True),
        max_pages_per_host=args.max_pages_per_host or crawl_data.get("max_pages_per_host", CrawlPolicy.max_pages_per_host),
        max_depth=args.max_depth if args.max_depth is not None else crawl_data.get("max_depth", CrawlPolicy.max_depth),
        rate_limit_per_host=crawl_data.get("rate_limit_per_host", 0.4),
        render_dynamic_pages=args.render_dynamic_pages or crawl_data.get("render_dynamic_pages", CrawlPolicy.render_dynamic_pages),
        dynamic_render_mode=crawl_data.get("dynamic_render_mode", "always"),
        require_browser_render=args.require_browser_render or crawl_data.get("require_browser_render", False),
        dynamic_wait_ms=crawl_data.get("dynamic_wait_ms", 1500),
        dynamic_network_idle_timeout_ms=crawl_data.get("dynamic_network_idle_timeout_ms", 5000),
        dynamic_scroll_rounds=crawl_data.get("dynamic_scroll_rounds", 4),
        dynamic_click_rounds=crawl_data.get("dynamic_click_rounds", 2),
        dynamic_click_limit=crawl_data.get("dynamic_click_limit", 20),
        dynamic_timeout_seconds=crawl_data.get("dynamic_timeout_seconds", 30),
        download_videos=crawl_data.get("download_videos", True),
        download_documents=crawl_data.get("download_documents", True),
        max_asset_size_mb=crawl_data.get("max_asset_size_mb", CrawlPolicy.max_asset_size_mb),
        max_assets_per_host=args.max_assets_per_host if args.max_assets_per_host is not None else crawl_data.get("max_assets_per_host", 0),
        timeout_seconds=args.timeout_seconds if args.timeout_seconds is not None else crawl_data.get("timeout_seconds", 30),
        revalidate_completed_on_resume=crawl_data.get("revalidate_completed_on_resume", True),
        retry_failed_on_resume=crawl_data.get("retry_failed_on_resume", True),
        terminal_http_statuses=[int(item) for item in crawl_data.get("terminal_http_statuses", [404, 410])],
        max_attempts_per_page=int(crawl_data.get("max_attempts_per_page", 3)),
        worker_count=crawl_data.get("worker_count", CrawlPolicy.worker_count),
    )
    if args.no_robots:
        crawl_policy.respect_robots = False

    viewports = [
        Viewport(str(item.get("name")), int(item.get("width")), int(item.get("height")))
        for item in visual_data.get("viewports", [])
        if item.get("name") and item.get("width") and item.get("height")
    ] or VisualPolicy().viewports

    return ReplicationConfig(
        site_id=site_id,
        target_url=target_url,
        out_dir=out_dir,
        domain_policy=domain_policy,
        crawl_policy=crawl_policy,
        static_policy=StaticPolicy(
            preserve_paths=static_data.get("preserve_paths", True),
            runtime_database=False,
            external_link_policy=static_data.get("external_link_policy", "keep_original"),
            query_strategy=static_data.get("query_strategy", "record_and_map_when_needed"),
        ),
        local_preview=LocalPreview(
            port_start=args.port_start or local_data.get("port_start", 8300),
            host_port_map={str(k): int(v) for k, v in local_data.get("host_port_map", {}).items()},
        ),
        deployment=Deployment(
            generate_nginx=deploy_data.get("generate_nginx", True),
            base_root=deploy_data.get("base_root", "/srv/mirror/original"),
            target_host_map={str(k): str(v) for k, v in deploy_data.get("target_host_map", {}).items()},
            target_base_domain=deploy_data.get("target_base_domain"),
            scheme=deploy_data.get("scheme", "https"),
            inject_runtime_link_rewriter=deploy_data.get("inject_runtime_link_rewriter", True),
        ),
        visual_policy=VisualPolicy(
            enabled=args.visual_compare or visual_data.get("enabled", False),
            sample_pages=args.visual_sample_pages if args.visual_sample_pages is not None else visual_data.get("sample_pages", 20),
            diff_threshold=visual_data.get("diff_threshold", 0.02),
            full_page=visual_data.get("full_page", True),
            wait_ms=visual_data.get("wait_ms", 1000),
            use_vision_model=visual_data.get("use_vision_model", False),
            vision_api_url=visual_data.get("vision_api_url"),
            vision_api_key_env=visual_data.get("vision_api_key_env", "VISION_API_KEY"),
            vision_model=visual_data.get("vision_model"),
            viewports=viewports,
        ),
        quality_policy=QualityPolicy(
            min_page_success_rate=float(quality_data.get("min_page_success_rate", 0.95)),
            min_resource_success_rate=float(quality_data.get("min_resource_success_rate", 0.98)),
            max_unresolved_internal_links=int(quality_data.get("max_unresolved_internal_links", 0)),
            max_residual_resources=int(quality_data.get("max_residual_resources", 0)),
            require_visual_pass=quality_data.get("require_visual_pass", False),
        ),
        authorization_policy=AuthorizationPolicy(
            require_ack=authorization_data.get("require_ack", AuthorizationPolicy.require_ack),
            authorized=bool(args.ack_authorized or authorization_data.get("authorized", False)),
            statement=authorization_data.get("statement", ""),
        ),
        force_refresh=args.force_refresh or data.get("force_refresh", False),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replicate authorized websites into static multi-host mirrors.")
    parser.add_argument("url", nargs="?", help="Target website URL.")
    parser.add_argument("--config", help="JSON config path.")
    parser.add_argument("--site-id")
    parser.add_argument("--root-domain")
    parser.add_argument("--out-dir")
    parser.add_argument("--max-pages-per-host", type=int)
    parser.add_argument("--max-assets-per-host", type=int)
    parser.add_argument("--max-depth", type=int)
    parser.add_argument("--timeout-seconds", type=int)
    parser.add_argument("--port-start", type=int)
    parser.add_argument("--force-refresh", action="store_true", help="Ignore previous crawl/resource tables and rebuild.")
    parser.add_argument("--render-dynamic-pages", action="store_true", help="Use Playwright to render HTML pages before replication.")
    parser.add_argument("--require-browser-render", action="store_true", help="Fail HTML pages when Playwright rendering is unavailable.")
    parser.add_argument("--visual-compare", action="store_true", help="Capture source/local screenshots and write visual_report.json.")
    parser.add_argument("--visual-sample-pages", type=int, help="Maximum pages to include in visual comparison.")
    parser.add_argument("--no-robots", action="store_true", help="Disable robots.txt checks. Use only for authorized sites.")
    parser.add_argument("--ack-authorized", action="store_true", help="Confirm you are authorized to mirror the target site.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args)
    agent = ReplicationAgent(config)
    agent.run()
    print(json.dumps({"output": str(agent.original_dir), "hosts": len(agent.hosts), "pages": len(agent.page_records)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
