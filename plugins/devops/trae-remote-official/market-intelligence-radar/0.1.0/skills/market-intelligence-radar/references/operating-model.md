# Operating model

## First-run contract

Create a working watch specification from the user's language. Do not turn onboarding into a long
questionnaire. Show only:

1. the decision this watch will support;
2. the proposed monitored entities and change themes;
3. the initial lookback used to establish a baseline;
4. the recommended recurring cadence and why;
5. one scheduling question.

Use this question pattern, localized to the user:

> I recommend [cadence] because [market-specific reason]. Should I create this recurring schedule?

The first response must ask about scheduling even if research also proceeds. Never claim a schedule
exists until the runtime confirms it.

## Cadence defaults

Choose by change velocity and decision latency:

| Watch type | Scan cadence | Synthesis cadence | Reason |
|---|---|---|---|
| AI, software, developer tools, consumer apps | Weekdays at 09:00 local time | Friday at 16:30 | Releases and pricing move quickly; a weekly rollup suppresses daily noise |
| Competitive product and B2B SaaS | Monday, Wednesday, Friday at 09:00 | Friday at 16:30 | Captures launches and commercial moves without over-sampling |
| Policy, regulation, security, or live deals | Weekdays at 09:00 plus P0 alert review | Weekly | Effective dates and response windows can be short |
| Industrial, enterprise, or slower markets | Tuesday and Friday at 09:00 | Monthly pattern review | Material changes are less frequent and need corroboration |

Use the user's timezone. If none is known, use the current runtime timezone and say so. For the
example AI Coding watch in China, recommend:

- weekday scan at 09:00 Asia/Shanghai;
- weekly synthesis Friday at 16:30 Asia/Shanghai;
- explain that the morning scan captures overnight global releases while the Friday report separates
  durable movement from launch noise.

If the runtime supports only one schedule, prioritize the scan matching the requested report. Embed
the weekly synthesis in Friday's run when possible.

## Automation behavior

After the user approves:

1. discover the runtime's automation-management capability;
2. create the smallest number of schedules that implements the approved cadence;
3. include the exact watch scope, time window, output type, timezone, and destination in the task;
4. instruct every run to compare against the latest successful baseline;
5. report the created cadence in plain language.

Do not write raw automation directives. Do not create a schedule solely because the user said
"continuously" if the first-response confirmation has not occurred.

## Baseline policy

On the first run, separate baseline from net-new intelligence:

- use 30 days for fast-moving products and technologies;
- use 90 days for funding, organization, partnerships, and regulation;
- extend only when a comparison or policy history requires it.

The baseline establishes the last known state. Do not present every baseline event as a new alert.
Label the first report `baseline established` and identify only changes occurring after the selected
cutoff as net new.

## Watch specification

Maintain these fields when a recurring workspace exists:

```json
{
  "watch_id": "ai-coding-global",
  "decision": "inform product roadmap and commercialization",
  "entities": ["named competitors and products"],
  "themes": ["models", "pricing", "IDE", "enterprise", "funding", "ecosystem"],
  "markets": ["China", "global"],
  "languages": ["zh-CN", "en"],
  "timezone": "Asia/Shanghai",
  "baseline_days": 30,
  "cadence": "weekdays 09:00; Friday 16:30 synthesis",
  "exclusions": ["private people", "rumor-only claims"]
}
```

Store no credentials or private personal information. Keep configuration separate from the signal
ledger.

## Run lifecycle

Every recurring run follows:

1. start a run and record the prior successful run;
2. execute the source query mesh;
3. normalize and ingest candidate signals;
4. review new events, revisions, and new evidence;
5. score and synthesize only decision-relevant deltas;
6. finish the run only after the report is successfully written;
7. retain failed-run notes so the next run does not treat an incomplete scan as a baseline.

Use `scripts/radar_state.py` when local persistence is appropriate. The script records identities and
run state; it does not research, infer, or make decisions.

## Change requests

When the user changes scope, keep the old baseline and version the watch specification. Mark newly
added entities as `baseline pending` until their initial lookback completes. Do not mix a widened
scope with a claim that the whole watch has been continuously monitored.

