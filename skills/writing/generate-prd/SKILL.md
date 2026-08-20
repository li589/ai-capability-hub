---
name: generate-prd
description: "Produce a structured PRD for the current repo, grounded in real services + packages via `browzer explore`/`search` so requirements aren't fictional. Proposes search-trigger expansions for uncovered domain concepts via PRD `assumptions[]`. Assumes saturated input — `orchestrate-task-delivery` Phase 0 routes vague input through `brainstorming` BEFORE this skill is invoked. Use whenever defining, planning, or documenting any non-trivial feature, change, or refactor. Triggers: write a PRD, draft a PRD, PRD for, requirements doc, spec this out, document requirements for, plan this feature, turn this idea into a spec, roadmap this, sanity-check scope."
argument-hint: <featureId>
install_source: official
install_method: download
skill_id: official_hhnGpgRa
enabled_at: 1787232959249
version: 1.0.0
name_zh: 生成 prd
---

You are a senior PM. Write a tight PRD grounded in the actual codebase.

## Read context

```!
if [ -n "$ARGUMENTS" ]; then
  if browzer get-step BRAINSTORM --id "$ARGUMENTS" 2>/dev/null; then
    :
  else
    browzer get-step ORIGINAL_REQUEST --id "$ARGUMENTS"
  fi
fi
```

`$ARGUMENTS` is the feature id passed by the orchestrator (e.g. `feat-20260507-preamble-staging-migration`); it is also the directory name under `docs/browzer/`.

The block above prefers a prior `BRAINSTORM` step when one exists; otherwise it falls back to `ORIGINAL_REQUEST` — the verbatim operator ask that `workflow init` recorded. Do NOT re-run brainstorming logic. The input is considered **unsaturated** when ANY of the following hold: (a) fewer than 30 words, (b) missing a clear persona ("who"), (c) missing a success signal / observable outcome. In that case return one line `generate-prd: input unsaturated — orchestrator should route through brainstorming first` and stop.

## Process

1. Extract every concrete noun from the input (services, packages, files, endpoints, symbols).
2. For each noun, run `browzer explore "<noun>" --save /tmp/prd-explore-<noun>.json` (code) and `browzer search "<topic>" --save /tmp/prd-search-<topic>.json` (docs). Use the hits to ground requirement language in real paths. Attach the receipt path(s) alongside each grounded requirement so downstream phases can verify the search was performed.
3. Draft acceptance criteria that name observable, testable outcomes. No vague verbs ("improve", "enhance") without a metric.
4. Identify candidate skills the implementer will need (e.g. `fastify-best-practices`, `bullmq-specialist`, `neo4j-cypher`). `skillsFound[]` is the working array of candidate skill names — initially populated from the implementer's suggestions and/or a scan of the available skills trees. **Validate each name exists on disk** by checking those same trees. A name not found in either tree MUST be removed from `skillsFound[]` and surfaced as a gap. Inventing a fictional skill (e.g. `go-cli-flag-plumbing`) is a contract violation — prefer the empty list to a fabricated one.

## Search-trigger proposal (FR-6)

The target repo's `.browzer/search-triggers.json` is an array of strings the search guard reacts to — when the operator's prompt mentions one of these terms, the guard nudges the agent toward `browzer explore`/`search` instead of blind reads. Expanding this list with domain-specific terms catches future invariants the repo's `CLAUDE.md` may not document.

While extracting nouns and exploring the repo (steps 1–2 above), if the operator's input mentions a domain concept that is NOT already present in the target repo's `.browzer/search-triggers.json`, you MUST add a candidate entry to the PRD `assumptions[]` array with the form:

> Propose adding `<term>` to `.browzer/search-triggers.json` — observed during exploration when … (justification).

Common candidate terms to look for: `permission`, `rbac`, `authn`, `authz`, `role`, `i18n`, `translation`, `locale`, `extract`, `migration`, `feature-flag`, `mutation`, `query`, `prisma`, `drizzle`, `neo4j`, `redis`, `queue`, `worker`, `webhook`, `billing`, `audit-log`.

Do NOT auto-write `.browzer/search-triggers.json`. The operator approves (or rejects) the proposal as part of the standard PRD review; the actual patch lands later in the workflow and is out of scope for this phase. Skills propose, operators approve.

> Note: if the persisted PRD's `assumptions[]` contains any "Propose adding ... to `.browzer/search-triggers.json`" entry, downstream skills (especially `feature-acceptance`) MAY surface the proposal in their final report so the operator doesn't lose track of the open decision.

## Produce

Write `docs/browzer/<feat>/staging/PRD.md` (where `<feat>` is `$ARGUMENTS`). The canonical scaffold + field reference for the PRD payload is auto-generated in `template.md` from the workflow CUE schema. Any heading not in the field list is silently dropped on save; any required field missing fails CUE validation.

> Shape reference: see `template.md` (auto-generated from the workflow CUE schema). Do not paste schema-claiming JSON into this body.

## Persistence

The autosave hook persists `staging/PRD.md` automatically on write. Recommended flags when manually invoking `save-step`:

- `--quiet --await` — PRD is load-bearing: `generate-task` reads it back immediately after this phase completes.

If the autosave hook fails you'll be notified — fix and re-write the staging file.

On validation failure, re-run with --hint-fixes for worked examples of valid values.

## Done when

- File exists at `docs/browzer/<feat>/staging/PRD.md`.
- Every entry under "Skills the implementer will need" was verified to exist on disk before writing.
- The autosave hook validates and persists; if it fails you'll be notified — fix and re-write.

Return one line: `generate-prd: PRD written with <N> requirements, <M> ACs`.
