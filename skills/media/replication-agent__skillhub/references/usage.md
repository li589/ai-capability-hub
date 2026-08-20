# Usage Reference

## Minimal Run

```bash
.venv/bin/python scripts/replication_agent.py \
  https://www.example.com/ \
  --ack-authorized \
  --force-refresh
```

`--ack-authorized` means the user confirms ownership or permission for the target site. Use `--force-refresh` for the first full run. Remove it for incremental updates.

## Config File

```json
{
  "target_url": "https://www.example.com/",
  "site_id": "example",
  "out_dir": "output/example",
  "domain_policy": {
    "root_domain": "example.com",
    "include_subdomains": true,
    "exclude": ["status.example.com"]
  },
  "deployment": {
    "target_base_domain": "mirror.example.com"
  }
}
```

Run with a config:

```bash
.venv/bin/python scripts/replication_agent.py \
  --config configs/replication_agent.example.json \
  --ack-authorized \
  --force-refresh
```

## Useful Options

- `--max-pages-per-host N`: limit page count during testing.
- `--max-assets-per-host N`: limit asset count during testing; use `0` for no limit.
- `--max-depth N`: limit crawl depth.
- `--timeout-seconds N`: request timeout.
- `--port-start N`: base port for multi-host local preview.
- `--render-dynamic-pages`: use browser rendering for dynamic pages.
- `--visual-compare`: enable visual comparison if configured.

## Local Preview

Single-port localhost preview:

```bash
.venv/bin/python scripts/serve_replica.py \
  output/example/original \
  --localhost \
  --port 8700
```

Open:

```text
http://localhost:8700/
```

The server maps source hosts under `/_mirror/<source-host>/` and rewrites root-path resources at response time.

## Deployment

```bash
.venv/bin/python scripts/deploy_static_mirror.py \
  --mirror-dir output/example/original \
  --ssh-host <server-ip> \
  --ssh-user root \
  --remote-root /srv/mirror/example \
  --remote-nginx-conf /etc/nginx/sites-available/example.conf \
  --enable-nginx-site \
  --reload-nginx
```

Deploy only after the release checklist passes.
