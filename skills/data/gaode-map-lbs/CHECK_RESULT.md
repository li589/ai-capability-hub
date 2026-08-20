# Gaode Map LBS Official Release Check

## A. SKILL_NAME / APP_NAME

- `SKILL_NAME = gaode-map-lbs`
- `APP_NAME = gaode-map-lbs`
- Public display name: `Gaode Map LBS - 高德官方地图综合服务 Skill`
- Web API region rule: `中国大陆（含港澳台）` defaults to `https://restapi.amap.com`; `非中国大陆（不含港澳台）` uses `https://sg-restapi.opnavi.com`.

This release keeps the public Skill slug as `gaode-map-lbs` and uses the official appname `gaode-map-lbs` for LBS Skill call statistics.

## B-D. AMap API Call Points

| File | Call point | appname status |
|---|---|---|
| `SKILL.md` | `restapi.amap.com/v3/log/init` for keyword search | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `restapi.amap.com/v3/log/init` for nearby search | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `restapi.amap.com/v3/geocode/geo` API format and curl example | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `restapi.amap.com/v3/log/init` for heatmap | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `restapi.amap.com/v3/log/init` for POI search | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `restapi.amap.com/v3/log/init` for route planning | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `restapi.amap.com/v3/log/init` for travel planner | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `www.amap.com/search` generated links | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `ditu.amap.com/search` generated links | Added `appname=gaode-map-lbs` |
| `SKILL.md` | `a.amap.com/jsapi_demo_show/static/openclaw/heatmap.html` generated links | Added `appname=gaode-map-lbs` |
| `index.js` | `restapi.amap.com/v5/place/text` via `axios.get(url, { params })` | Added `appname: APP_NAME` |
| `index.js` | `restapi.amap.com/v3/direction/walking` via `axios.get(url, { params })` | Added `appname: APP_NAME` |
| `index.js` | `restapi.amap.com/v3/direction/driving` via `axios.get(url, { params })` | Added `appname: APP_NAME` |
| `index.js` | `restapi.amap.com/v4/direction/bicycling` via `axios.get(url, { params })` | Added `appname: APP_NAME` |
| `index.js` | `restapi.amap.com/v3/direction/transit/integrated` via `axios.get(url, { params })` | Added `appname: APP_NAME` |
| `index.js` | `sg-restapi.opnavi.com/v3/place/text` for Non-Mainland Web API | Added `appname: APP_NAME`; requires `city` adcode |
| `index.js` | `sg-restapi.opnavi.com/v3/direction/walking` for Non-Mainland Web API | Added `appname: APP_NAME` |
| `index.js` | `sg-restapi.opnavi.com/v3/direction/driving` for Non-Mainland Web API | Added `appname: APP_NAME` |
| `index.js` | `a.amap.com/jsapi_demo_show/static/openclaw/travel_plan.html` generated link | Added `appname=${APP_NAME}` |
| `gaode_skill.py` | Socket payload to the Electron JSAPI adapter | Added `appname` to payload params; no direct HTTP URL exists in this file |

No `webapi.amap.com` or `sg-webapi.opnavi.com` call points exist in this package. The overseas addition is Web API only.

## Public Key

- Added public Web Service Key fallback: `PUBLIC_AMAP_WEBSERVICE_KEY`.
- User-owned keys still take priority through `AMAP_WEBSERVICE_KEY`, then legacy `AMAP_KEY`, then config file.
- If no user key is configured, both `restapi.amap.com` and `sg-restapi.opnavi.com` fall back to the same public key and tell users that the free daily quota is first-come, first-served.
- Added `AMAP_OVERSEAS_WEBSERVICE_KEY` / `overseasWebServiceKey` path for Non-Mainland Web API.
- Non-Mainland users who need dedicated capacity are directed to AMap Overseas Contact Sales.
- The official package no longer marks `AMAP_WEBSERVICE_KEY` as a required environment variable in frontmatter.

## Scenario Coverage

| Scenario | Overseas Web API status | Notes |
|---|---|---|
| Scenario 1 keyword search | Not applicable | Uses generated `www.amap.com/search` links, not Web API |
| Scenario 2 nearby search | Documented | Geocoding examples include both `restapi.amap.com` and `sg-restapi.opnavi.com`; final map link remains `ditu.amap.com` |
| Scenario 3 heatmap | Not applicable | Uses generated `a.amap.com/jsapi_demo_show` link, not Web API |
| Scenario 4 detailed POI search | Covered | `userRegion=non-mainland` uses `sg-restapi.opnavi.com/v3/place/text` |
| Scenario 5 route planning | Covered for walking and driving | Transit smoke test returned HTTP 404; riding is not invented without a reference endpoint |
| Scenario 6 travel planner | Covered for POI search | Interest POI search uses overseas Web API when `userRegion=non-mainland`; visualization remains existing map-task link |
| Scenario 7 Python adapter | Payload only | Sends `appname`, but final request behavior depends on the external Electron adapter |

## Remaining Risk

- `gaode_skill.py` talks to an external Electron adapter over a Unix socket. This package can pass `appname` into the payload, but final JSAPI request attribution depends on that adapter honoring or forwarding the field.
- Non-Mainland transit is not enabled because the referenced endpoint returned HTTP 404 in smoke testing; riding is not enabled because the reference did not provide a clear overseas bicycling endpoint.
- The package does not include `axios` installed locally; syntax checks pass, but full runtime execution requires the declared install step.

## Result

- Web Service examples and runtime request params are covered.
- Public generated links are tagged where a query string is already used.
- No complex instrumentation system was added.
- Business logic was not changed.
- No account, token, cookie, or private credential was added.
- The public-facing Skill name is clean and does not contain channel wording.

## Smoke Test

Run from a temporary unpacked copy with dependencies installed:

| Test | Command shape | Result |
|---|---|---|
| Mainland POI | `node scripts/poi-search.js --keywords=肯德基 --city=北京` | Passed, returned Beijing POIs |
| Non-Mainland POI | `node scripts/poi-search.js --keywords=starbucks --city=840000000 --user-region=non-mainland` | Passed, returned US POIs |
| Mainland driving | `node scripts/route-planning.js --type=driving ...` | Passed, returned route and map link |
| Non-Mainland driving | `node scripts/route-planning.js --type=driving ... --user-region=non-mainland` | Passed, returned route and map link |
| Mainland travel planner | `node scripts/travel-planner.js --city=北京 --interests=景点 --routeType=walking` | Passed |
| Non-Mainland travel planner | `node scripts/travel-planner.js --city=840000000 --interests=landmark --routeType=walking --user-region=non-mainland` | Passed |
| Non-Mainland transit | `node scripts/route-planning.js --type=transfer ... --user-region=non-mainland` | Intentionally blocked with clear unsupported-endpoint message |
