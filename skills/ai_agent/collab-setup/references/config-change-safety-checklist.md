# Config Change Safety Checklist

Use this whenever a task may alter routing, agents, channels, gateway behavior, or collaboration setup.

## Before editing
- identify whether the current system is already partially or fully working
- confirm which user-visible behaviors must not regress
- prefer patch-style edits over broad regeneration
- back up the current active config before changes
- avoid deleting working fields unless necessary

## During editing
- change the smallest complete unit needed
- keep old working semantics intact unless intentionally replaced
- avoid mixing unrelated cleanup with functional fixes
- preserve a clear rollback target

## Before restart
- validate config syntax
- check for obvious schema/doctor warnings
- confirm the intended changed fields are the only meaningful behavioral changes

## After restart
- verify gateway health
- verify the target channel is connected
- verify the exact user-facing scenario that motivated the change
- verify final outbound reply behavior, not just inbound routing

## If health regresses
- restore the last known-good config first
- re-run health check after restore
- only then explain the failure cause and next safe step

## User-facing principles
- do not leave the user in a broken state if rollback is possible
- do not claim success without runtime verification
- do not hide degraded state; explain what works and what still does not
- prefer one-pass safe completion over repeated risky edits
