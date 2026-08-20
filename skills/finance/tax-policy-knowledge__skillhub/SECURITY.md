# Security & Privacy Disclosure (Tax-Skill Matrix · Expert/Team Auto-Registration)

This skill package includes an "expert and expert-team auto-registration" capability. The mechanism is described below for marketplace review and user verification.

## 1. What auto-registration is and when it happens
- Trigger: When the user explicitly says "install the full tax-skill matrix" or "install an associated tax skill" in a conversation, the built-in installer (`install_matrix.py`) is **actively** invoked, which then registers the skill's **dedicated expert** (`expert-<slug>`) and **belonging expert pod** (`expert-pod-pN`).
- This is a **local file registration** operation — not a remote download or arbitrary code execution.

## 2. Asset origin: fully bundled locally, no silent remote fetching
- The expert/team packages (`experts_build/agents/...`, `experts_build/teams/...`) and registration scripts (`matrix_expert_install.py`, `scripts/register_local_experts.py`) are **distributed together with this skill package** and become local files after extraction.
- The registration process only copies the above local directories into the local WorkBuddy "My Experts" marketplace (`~/.workbuddy/plugins/marketplaces/my-experts/`) and writes a local `marketplace.json` registration entry. **It never accesses any external download address and never executes any remote script.**
- Registration is **idempotent**: already-registered items are skipped; repeated runs have no side effects. A source tag is provided for batch uninstallation.

## 3. Cloud MCP service (client-side auto-registration, pre-agreed compliant)
- When the skill calls the tax knowledge base, the client **auto-registers the cloud MCP service** (`https://mcp.aitaxs.top/...`) for Q&A, risk screening, calculation, and knowledge retrieval.
- This endpoint is a knowledge-query service only. It does not collect device fingerprints and does not upload user private data; it only generates a random anonymous identifier locally for service invocation.

## 4. Security boundary
- Writes only to the local `~/.workbuddy` directory for skill/expert/team registration. No outbound calls, no fingerprint collection, no key sharing.
- Does **not** modify system files, does not escalate privileges, and does not access any data outside the user's personal directory.
- With one explicit exception described in §8 below: this package may, **only when the user explicitly authorizes it**, register the cloud MCP endpoint into the user's own client MCP config files (Claude Desktop / Cursor / VS Code). This is a separate, user-consented operation and is never performed silently on the stdio launch path.

## 5. User control
- Expert linkage in the installer is enabled by default; users may pass `--no-experts` to install only the skill itself and skip expert registration.
- At any time, users can view, invoke, or uninstall registered experts in "Expert Center → My Experts".

## 6. Download URL whitelist (tamper protection)
- The matrix installer (`install_matrix.py`) reads download addresses from the bundled `matrix.json`. Before any network fetch, each URL is validated against a **declared domain allow-list**: only official marketplace hosts are permitted — `*.skillhub.cn` (SkillHub, the primary maintenance channel) and `*.clawhub.ai` (ClawHub, the dual market).
- Requirement: the URL must use the `https` scheme **and** its host must belong to one of the allowed suffixes above. Anything else — plain `http`, bare IP addresses, or **any arbitrary external domain** (for example `tix.qq.com`, `static.cloudsec.tencent.com`, or a malicious host) — is rejected before the connection is even opened.
- This is defense-in-depth against a tampered `matrix.json`: even if an attacker rewrites a `download_url` to point at an arbitrary address, the installer refuses to fetch it and aborts that skill's installation rather than pulling a potentially poisoned package. A clear `[SECURITY]` message is printed so the user is aware.
- Combined with the SHA-256 integrity gate (Section 2 / installer), the supply chain is protected at two layers: **source allow-list** (where bytes come from) and **content integrity** (whether bytes were altered).

## 7. Local search — fully removed (zero third-party outbound)

> **Status: the local/third-party web-search fallback has been completely removed from the client.** This supersedes any earlier "opt-in / disabled-by-default" description.

- **No third-party search, ever.** The client no longer contains any code path that constructs or opens a request to `cn.bing.com`, `www.baidu.com`, or any other third-party search engine. The functions `_local_web_search`, `_local_fetch`, `_parse_bing`, `_parse_baidu`, `_LOCAL_ENGINES` and `_TAX_KEYWORDS` have been deleted from `config/mcp_client.py` (and the shared root template).
- **No query exfiltration.** User query text is never sent to any external party by the client. The only outbound traffic is to the operator's own cloud MCP knowledge service (over HTTPS); there is no fallback that reaches the public internet.
- **Outage behaviour = static guidance, not search.** When the cloud MCP service is unreachable, `_web_search()` and `_generate_local_answer()` now return a purely static, offline guidance message (constant `_LOCAL_SEARCH_GUIDANCE`) that instructs the **user's own agent** to retrieve the latest policy from authoritative sources (e.g. 国家税务总局官网 https://www.chinatax.gov.cn, provincial tax bureaus, 财政部官网 https://www.mof.gov.cn). The client performs no retrieval on the user's behalf.
- **Why removed.** Cloud-security review flagged that, under the previous design, an unreachable cloud could auto-send the user's query text to third-party search engines. Removing the subsystem entirely eliminates that data-egress path and the associated compliance risk.

## 8. stdio launch path & client MCP config write boundary (explicit, user-consented)

> This section is the authoritative disclosure referenced by the in-code comment in `config/mcp_stdio_server.py` (the `detect_and_setup` call site).

- **stdio launch path is probe-only by default.** When the skill is launched via stdio (the MCP server entry), it calls `detect_and_setup(dry_run=True)`. This **only detects** the user's Agent type (Claude Desktop / Cursor / VS Code / etc.) and the transport, and logs it. It performs **no disk write** on the stdio launch path.
- **No silent writes.** The `TAX_ENABLE_AUTOSETUP` environment-trigger has been removed. The stdio path never writes the user's client MCP config unless `dry_run=False` is passed **explicitly** by the user (e.g. running the installer's auto-setup step with confirmation).
- **When a write does happen (user-consented only):** writing the cloud MCP endpoint (`mcpServers.<slug>`) into the user's client config (`~/.cursor/mcp.json`, `~/.vscode/settings.json`, or the Claude Desktop config) is:
  - **idempotent** — an entry that already exists is skipped;
  - **backed up** — the target file is backed up before modification;
  - **logged** — the action (path + entry) is written to stderr for the user to audit.
- **This is the only write outside `~/.workbuddy`.** It modifies the user's own client MCP config — not system files, not other users' data. The user can always inspect or remove the entry by editing the client config or uninstalling the skill.
- **Summary for reviewers:** the stdio launch path does **not** silently modify client configurations; any such modification is explicit, logged, idempotent, and disclosed here.
