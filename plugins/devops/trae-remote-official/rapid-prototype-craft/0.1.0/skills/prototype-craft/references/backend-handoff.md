# backend-handoff · Contract Export & Three-Tier Backend Onboarding

Goal: after the user is satisfied with the MVP, let them **wire up a real backend as fast as possible without locking the prototype into any one backend architecture**. This reference does **not** implement a backend — it stays within the skill's thin boundary. It only formalizes the prototype's stub layer into an **architecture-neutral contract** and hands the user a clear "pick one of three tiers" path.

## 0. Core Principle: the single seam

The prototype's `api.js` stub layer is the **only seam** between the frontend and any future backend. Keep it single and clean, and swapping the backend means swapping only the inside of `api.js` — the view/state/data layers stay untouched. The contract exported here is the neutral definition of that seam; which technology fulfills it becomes a pluggable choice, not an upfront commitment.

> Do NOT let the prototype choose a backend architecture. The prototype only defines **what data looks like and which interfaces exist**; **how they are implemented** is the user's later, separate decision.

## 1. When to produce the handoff

Trigger at wrap-up (or when the user says "MVP looks good, how do I get a backend / go live with real data") — after the prototype passes `acceptance.md`. Do NOT trigger during normal iteration. Producing the handoff never implies building the backend; it stops at contract + guidance.

## 2. Contract artifacts (export to a `contract/` directory in the delivery dir)

Extract directly from the frozen `api.js` stubs and `mock.js` schema — do not invent new interfaces. At minimum:

- **`contract/openapi.yaml`** (or `contract/types.ts` for a TS-only project): every stub becomes one endpoint with explicit **HTTP method + path + request shape + response shape**, matching the stub signatures 1:1.
- **`contract/data-model.md`**: the entity/field definitions distilled from `mock.js` (entity name, fields, types, relations, example values) — the neutral source of truth for any database schema.
- **`contract/endpoint-map.md`**: a page → stub function → endpoint mapping table, so a backend team can see which screen consumes which API.

Prerequisite (enforced upstream in `interaction-mock.md`): each stub in `api.js` MUST already carry its intended `method + path + request/response shape` and a `// TODO: replace with ...` marker. The contract is a mechanical extraction of that, not fresh design.

## 3. Three-Tier Onboarding Guidance (write into the delivery notes)

Give the user all three and let them pick by team size, timeline, and cost. Order = fastest to most flexible.

| Tier | Best for | What the user does | Frontend change |
|---|---|---|---|
| **① BaaS direct** (Supabase / Pocketbase / Firebase / Appwrite) | validation phase, small team, want real data today | Map `contract/data-model.md` to BaaS tables; replace each `api.js` stub body with the BaaS SDK call | Only `api.js` internals; signatures unchanged |
| **② Contract-driven scaffolding** | self-hosted backend, architecture still open (Node/Go/Python…) | Feed `contract/openapi.yaml` to a codegen: typed client for FE, route/DTO/validation scaffold for BE, migrations from the data model | Only `api.js` internals; the contract keeps FE & BE decoupled so the architecture stays swappable |
| **③ Engineering handoff** (dev doc) | complex business, custom architecture, outsourced build | Use the `convert` intent to reverse a full dev doc (feature modules, API contracts, data model, page-to-API map); the team implements the backend independently | Depends on the team's chosen implementation |

Whatever the tier, real auth (JWT/session/OAuth), deployment, env vars, and monitoring remain the user's engineering work — the prototype's "login" was front-end mock validation only.

## 4. Delivery message pattern

At handoff, tell the user in one breath: "MVP is frozen → here is a neutral `contract/` → pick by your situation: **fastest → wire a BaaS by mapping this schema; self-build → generate scaffolding from this OpenAPI; outsource → hand over this dev doc**. In all cases your frontend barely changes — you only swap the inside of `api.js`."

## 5. Boundary (unchanged)

This reference adds a **handoff artifact**, not a backend capability. It introduces no server code, database, auth backend, or deployment. If the user wants the backend actually built, that is engineering beyond this skill's scope and is the user's call — the skill stops at "high-fidelity interactive + mock + shareable static artifact + neutral contract for handoff."
