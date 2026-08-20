# Config Backup Rollback Playbook

Use this reference for practical backup, validation, and rollback sequencing around risky OpenClaw config changes.

## Standard backup flow
1. read the active config path actually used by the gateway/service
2. create a timestamped backup before editing
3. edit only the minimum required fields
4. validate syntax before restart
5. restart gateway
6. run health verification
7. if health is degraded, restore the backup immediately

## Backup naming
Use a timestamped backup pattern such as:
- `~/.openclaw/openclaw.json.bak-YYYYMMDD-HHMMSS`

Do not overwrite a stable last-known-good backup blindly.

## Minimum verification flow
After restart, verify at least:
- gateway status is healthy
- RPC probe is healthy if available
- channel connection is healthy for the affected channel
- one direct user-visible test if direct delivery matters
- one group-visible test if group routing matters
- one final outbound reply test if final delivery was the issue

## Safe rollback trigger
Rollback should happen immediately if any of the following occur:
- gateway cannot start
- gateway health probe fails
- target channel is disconnected when it was previously working
- the exact user-critical path regresses and the change was the likely cause

## Rollback sequence
1. stop or restart into restore path if needed
2. restore the last known-good config backup
3. re-run syntax validation
4. restart gateway
5. re-run health verification
6. tell the user the system has been restored before discussing further fixes

## Communication style
Preferred order:
- say whether the system is healthy now
- say whether rollback was needed
- say what likely caused the regression
- say the smallest next safe step
