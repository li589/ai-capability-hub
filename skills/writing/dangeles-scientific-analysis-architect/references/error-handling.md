# Error Handling

Comprehensive error handling specification for the scientific-analysis-architect skill.

## Timeout Configuration

### Per-Phase Timeouts

| Phase | Timeout | Description |
|-------|---------|-------------|
| 0 | 5 min | Initialization (session, output validation) |
| 1 | 15 min | Birds-eye planning |
| 2 | 20 min | Subsection planning (includes consultant fan-out) |
| 3 | 10 min | Structure review |
| 4 | 15 min | Plan review (parallel) |
| 5 | 20 min | Document generation (parallel) |
| 6 | 30 min | Statistical fact-checking (interview mode) |
| 7 | 15 min | Audience document generation |

### Per-Agent Timeouts

| Agent | Timeout | Criticality |
|-------|---------|-------------|
| research-architect | 15 min | Critical |
| analysis-brainstormer | 3 min | Optional |
| method-brainstormer | 3 min | Optional |
| analysis-planner | 8 min per chapter | Critical |
| statistician-consultant | 5 min | Critical |
| mathematician-consultant | 5 min | Optional |
| programmer-consultant | 5 min | Optional |
| structure-reviewer | 10 min | Critical |
| notebook-reviewer | 5 min per chapter | Critical |
| notebook-generator | 7 min per chapter | Critical |
| statistical-fact-checker | 30 min | Critical |

## Exception Handling Protocol

### Detection

- Monitor agent execution time against timeout
- Catch Task tool failures
- Validate output file existence and format

### Containment

- Isolate failed agent from parallel group
- Preserve partial outputs
- Log failure details to `{session_dir}/logs/errors.log`

### Recovery

- Apply retry protocol (see below)
- Execute compensation actions (see below)

### Escalation

- Use AskUserQuestion templates (see below)

## Retry Protocol

### Automatic Retry (Attempt 1)

- Trigger: Agent timeout or failure
- Wait: 30 seconds
- Action: Retry same agent with same inputs
- Log: "Retry attempt 1 for {agent_name}"

### User Escalation (After Attempt 2)

- Trigger: Second consecutive failure
- Action: Present escalation prompt (see templates below)

### Maximum Retries

- 2 attempts per agent per invocation
- Reset on successful execution

## Circuit Breaker Configuration

### Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Consecutive failures per agent | 2 | Open circuit, escalate |
| Total failures per phase | 50% of agents | Abort phase, escalate |
| Session-wide failures | 5 | Suggest abort workflow |

### States

- **Closed**: Normal operation
- **Open**: Agent bypassed, escalation active
- **Half-Open**: Testing single request after cooldown

### Reset Conditions

- Closed -> Open: 2 consecutive failures
- Open -> Half-Open: 60 second cooldown
- Half-Open -> Closed: 1 successful execution
- Half-Open -> Open: 1 failure

## Compensation Actions by Phase

### Phase 0 Failure: Initialization

**Trigger**: Session directory creation fails, output validation fails

**Compensation**:
1. Clean up any partial session directory
2. Log error to stdout
3. Exit with clear error message

**No retry** - Initialization failures are terminal

### Phase 1 Failure: Birds-Eye Planning

**Trigger**: research-architect timeout or failure

**Compensation**:
1. Save partial research-structure.md (if any content generated)
2. Log failure to session state
3. Escalate to user

**Recovery options**:
- Retry Phase 1
- User provides manual research structure
- Abort workflow

### Phase 2 Failure: Subsection Planning

**Trigger**: Consultant timeout or failure

**For statistician-consultant (Critical)**:
1. Retry once
2. If retry fails, escalate with statistical guidance gap
3. User can: provide manual guidance, proceed without, retry, abort

**For mathematician-consultant (Optional)**:
1. Retry once
2. If retry fails, proceed with warning
3. Log gap in analysis plans

**For programmer-consultant (Optional)**:
1. Retry once
2. If retry fails, proceed with warning
3. Log gap in analysis plans

**Compensation for analysis-planner failure**:
1. Save partial chapter plans
2. Allow per-chapter retry
3. If >50% chapters fail, escalate

### Phase 3 Failure: Structure Review

**Trigger**: structure-reviewer timeout or failure

**Compensation**:
1. Skip review (warning to user)
2. User can: accept unreviewed structure, retry review, abort

**Recovery**:
- Proceed to Phase 4 with "unreviewed" flag
- Structure approval gate shows warning

### Phase 4 Failure: Plan Review

**Trigger**: notebook-reviewer timeout or failure

**Compensation**:
1. Mark failed chapters as "unreviewed"
2. Proceed with reviewed chapters
3. User can: accept partial, retry failed, abort

**Recovery**:
- Per-chapter retry option
- Proceed with partial reviews

### Phase 5 Failure: Document Generation

**Trigger**: notebook-generator timeout or failure

**Compensation**:
1. Preserve successfully generated analysis documents
2. Mark failed chapters in session state
3. Offer per-chapter regeneration

**Recovery**:
- Retry failed chapters only
- Manual document creation instructions
- Proceed to Phase 6 with partial (user choice)

### Phase 6 Failure: Statistical Fact-Checking

**Trigger**: statistical-fact-checker timeout or failure

**Compensation**:
1. Save interview progress (concerns reviewed so far)
2. Save corrections-manifest.json with partial decisions
3. Offer resume interview

**Recovery**:
- Resume interview from last concern
- Skip remaining concerns (user accepts risk)
- Pass without statistical review (warning logged)

### Phase 7 Failure: Audience Document Generation

**Trigger**: Document generation timeout or failure

**Compensation**:
1. Preserve any successfully generated audience documents
2. Mark failed documents in session state
3. Log failure to session state errors array

**Recovery options**:
- Retry failed documents (up to 2 retries per document)
- Proceed without failed documents (warn user)
- Abort Phase 7 (Phase 0-6 outputs are unaffected)

**For individual document failure**:
- Retry once with same inputs
- If retry fails: mark as skipped, proceed with remaining documents
- All three documents are independent; failure of one does not affect others

**For total failure (all three documents fail)**:
- Escalate to user with Template 1
- Options: retry all, proceed without audience documents, abort

## Escalation Prompt Templates

### Template 1: Critical Agent Failure (Single)

```
[AGENT FAILURE] {agent_name} failed after 2 attempts

Phase: {phase_number} ({phase_name})
Error: {error_type} - {error_message}
Impact: {impact_description}

Options:
  (A) Retry {agent_name} (attempt 3)
  (B) Proceed without {agent_name} output (may affect quality)
  (C) Provide manual input for {missing_output}
  (D) Abort workflow

Enter choice [A/B/C/D]:
```

### Template 2: Multiple Agent Failures (Consolidated)

```
[MULTIPLE FAILURES] {count} agents failed in Phase {phase_number}

Failed agents:
{foreach agent in failed_agents}
  - {agent.name}: {agent.error_type}
{end}

Working agents:
{foreach agent in working_agents}
  - {agent.name}: completed successfully
{end}

Options:
  (A) Retry all failed agents
  (B) Proceed with {working_count} available outputs
  (C) Abort phase and return to Phase {phase_number - 1}
  (D) Abort workflow

Enter choice [A/B/C/D]:
```

### Template 3: Phase Timeout

```
[TIMEOUT] Phase {phase_number} ({phase_name}) exceeded {timeout} minutes

Status at timeout:
  - Completed: {completed_items}
  - In progress: {in_progress_items}
  - Not started: {not_started_items}

Options:
  (A) Wait additional {extension} minutes
  (B) Proceed with completed items only
  (C) Abort phase and troubleshoot
  (D) Abort workflow

Enter choice [A/B/C/D]:
```

### Template 4: Circuit Breaker Open

```
[CIRCUIT BREAKER] {agent_name} circuit breaker opened

Consecutive failures: {failure_count}
Last error: {last_error}
Time since last success: {time_elapsed}

This agent is temporarily disabled to prevent cascading failures.

Options:
  (A) Wait {cooldown} seconds and retry
  (B) Skip this agent for this session
  (C) Abort workflow

Enter choice [A/B/C]:
```

### Template 5: Session-Wide Failure Threshold

```
[WORKFLOW STABILITY WARNING]

This session has encountered {failure_count} failures across phases.
Failure rate: {failure_rate}%

Recent failures:
{foreach failure in recent_failures limit=5}
  - Phase {failure.phase}: {failure.agent} - {failure.type}
{end}

Recommendation: Consider aborting and troubleshooting.

Options:
  (A) Continue workflow (accepting higher risk)
  (B) Save session state and pause for troubleshooting
  (C) Abort workflow and start fresh

Enter choice [A/B/C]:
```

## Fan-Out Failure Handling

### Consolidated Escalation Protocol

When multiple parallel agents are running (Phase 2 consultants, Phase 4/5 per-chapter):

1. **Wait for all agents** to complete or timeout (do not escalate immediately)
2. **Collect all failures** into single failure report
3. **Present consolidated prompt** (Template 2 above)
4. **User makes single decision** for all failures

### Critical vs Optional Agents

| Agent | Criticality | Failure Behavior |
|-------|-------------|------------------|
| statistician-consultant | Critical | Escalate if fails |
| mathematician-consultant | Optional | Warn and proceed |
| programmer-consultant | Optional | Warn and proceed |
| notebook-reviewer (per chapter) | Critical | Per-chapter escalation |
| notebook-generator (per chapter) | Critical | Per-chapter escalation |

### >50% Failure Rule

If more than 50% of parallel agents in a fan-out fail:
1. Abort the current phase
2. Present escalation prompt
3. Options: Retry all, abort workflow, return to previous phase

## Logging

### Error Log Format

```json
{
  "timestamp": "2026-02-04T14:30:22Z",
  "session_id": "session-20260204-143022-12345",
  "phase": 2,
  "agent": "statistician-consultant",
  "error_type": "timeout",
  "error_message": "Agent exceeded 5 minute timeout",
  "retry_count": 2,
  "resolution": "user_escalation",
  "user_choice": "proceed_without"
}
```

### Log Location

`{session_dir}/logs/errors.log` - one JSON object per line

### Log Levels

- **ERROR**: Agent failure, timeout, validation failure
- **WARNING**: Optional agent failure, partial completion
- **INFO**: Retry attempt, circuit breaker state change
- **DEBUG**: Agent input/output details (verbose mode only)

## Graceful Degradation

### Degradation Paths

1. **Full workflow** (all agents succeed)
2. **Partial consultant** (optional consultants fail, statistician succeeds)
3. **Partial chapters** (some chapters fail generation/review)
4. **No statistical review** (fact-checker fails, user accepts risk)
5. **No audience documents** (Phase 7 fails, user accepts)

### Degradation Warnings

When degraded workflow completes, show summary:

```
Workflow Complete (with degradation)

Warnings:
- Chapter 3 analysis documents generated without mathematician input
- Chapter 4 not statistically reviewed

Generated outputs:
- 3 of 4 chapters complete
- 8 of 11 planned analysis documents

Recommendation: Manually review Chapter 3 algorithms and Chapter 4 statistics.
```

## Recovery Best Practices

### When to Retry vs Abort

**Retry when:**
- Single agent failure (not pattern)
- Network/timeout error (transient)
- First occurrence in session

**Abort when:**
- Same agent fails 3+ times
- >50% parallel agents fail
- Circuit breaker opens twice
- User requests abort

### Preserving User Progress

Always checkpoint before:
- Spawning parallel agents
- User approval gates
- Notebook generation

Never lose:
- User-provided context
- Approval decisions
- Statistical interview progress

### Post-Failure Diagnostics

When session aborts or errors, provide:

```
Session Summary

Duration: {elapsed_time}
Completed: Phases {completed_list}
Failed at: Phase {phase} - {agent}

Saved artifacts:
- {session_dir}/session-state.json
- {session_dir}/logs/errors.log
- {list of generated outputs}

To resume:
  /scientific-analysis-architect

To start fresh:
  rm -rf {session_dir} && /scientific-analysis-architect
```
