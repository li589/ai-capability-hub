# Phase Workflows

Detailed workflows for each phase of the scientific-analysis-architect skill.

## Phase 0: Initialization

**Duration**: 2-5 minutes
**Owner**: Orchestrator (main skill)
**Checkpoint**: Never (automatic)

### Workflow Steps

```
START Phase 0
    |
    v
[1] Ask user for output directory
    |
    +---> Default: current working directory
    |
    v
[2] Validate output directory
    |
    +---> Check exists
    +---> Check writable (perform write test)
    +---> If fails: offer alternatives or ask for new path
    |
    v
[3] Create session directory
    |
    +---> Primary: {output_dir}/.scientific-analysis-session/
    +---> Fallback: /tmp/scientific-analysis-architect-session-{timestamp}/
    |
    v
[4] Initialize session-state.json
    |
    +---> Set status: "initialized"
    +---> Set current_phase: 0
    +---> Record config: output_directory
    |
    v
[5] Check for existing sessions
    |
    +---> If found and < 72 hours: offer resume
    |
    v
END Phase 0 -> Quality Gate 0
```

### Quality Gate 0 Criteria

- [ ] Session directory created and writable
- [ ] Output directory validated
- [ ] session-state.json initialized

---

## Phase 1: Birds-Eye Planning

**Duration**: ~12 minutes
**Owner**: research-architect (Sonnet 4.5)
**Timeout**: 15 minutes

### Workflow Steps

```
START Phase 1
    |
    v
[1] Load session state
    |
    v
[2] AskUserQuestion: Dataset and research goals
    |
    "Please describe your dataset and research goals.
     Include:
     - Data type (RNA-seq, proteomics, imaging, etc.)
     - Sample size and conditions
     - Main research questions"
    |
    v
[3] Analyze response for uncertainty signals
    |
    +---> Keywords: "not sure", "maybe", "could be", "uncertain"
    |
    +---> If HIGH uncertainty detected:
    |         |
    |         v
    |     [3a] Spawn brainstormers (parallel)
    |         |
    |         +---> Task: analysis-brainstormer
    |         |     "Suggest analysis types for: {dataset}"
    |         |
    |         +---> Task: method-brainstormer
    |         |     "Suggest methods for: {research_area}"
    |         |
    |         v
    |     [3b] Aggregate suggestions
    |         |
    |         v
    |     [3c] Present suggestions to user
    |         |
    |         AskUserQuestion: "Based on your description,
    |         here are analysis approaches to consider:
    |         {brainstormer_suggestions}
    |
    |         Which approaches interest you?"
    |
    v
[4] Generate research structure (3-7 chapters)
    |
    +---> Each chapter needs:
    |     - Title
    |     - Goal (atlas/hypothesis/mechanism)
    |     - List of analyses
    |     - Dependencies on other chapters
    |
    v
[5] Write research-structure.md
    |
    v
[6] Update session state
    |
    +---> Set current_phase: 1
    +---> Set completed_phases: [0, 1]
    +---> Record outputs.research_structure
    |
    v
END Phase 1 -> Quality Gate 1
```

### research-structure.md Format

```markdown
# Research Structure: {Project Title}

## Overview
{1-2 paragraph summary of research goals and approach}

## Dataset Description
{User-provided description, preserved verbatim}

## Chapters

### Chapter 1: {Chapter Title}
**Goal**: {atlas | hypothesis | mechanism}
**Analyses**:
1. {Analysis 1 name} - {brief description}
2. {Analysis 2 name} - {brief description}
**Dependencies**: None

### Chapter 2: {Chapter Title}
**Goal**: {atlas | hypothesis | mechanism}
**Analyses**:
1. {Analysis 1 name}
2. {Analysis 2 name}
**Dependencies**: Chapter 1 (requires normalized data)

...
```

### Quality Gate 1 Criteria

- [ ] research-structure.md exists
- [ ] Contains 3-7 chapters
- [ ] Each chapter has goal and at least 1 analysis
- [ ] Dependencies are valid (no circular, reference existing chapters)

---

## Phase 2: Subsection Planning

**Duration**: ~12 minutes for 3 chapters
**Owner**: analysis-planner (Sonnet 4.5)
**Timeout**: 20 minutes total

### Workflow Steps

```
START Phase 2
    |
    v
[1] Read research-structure.md
    |
    v
[2] For each chapter (sequential):
    |
    +---> [2a] Read chapter details
    |
    +---> [2b] Fan-out to expert panel (PARALLEL)
    |         |
    |         +---> Task: statistician-consultant
    |         |     "Review analyses for Chapter {N}: {analyses}"
    |         |     Timeout: 5 min
    |         |
    |         +---> Task: mathematician-consultant
    |         |     "Review algorithms for Chapter {N}: {analyses}"
    |         |     Timeout: 5 min
    |         |
    |         +---> Task: programmer-consultant
    |               "Review data requirements for Chapter {N}"
    |               Timeout: 5 min
    |
    +---> [2c] Fan-in: Wait for all consultants
    |         |
    |         +---> Handle failures (see Error Handling below)
    |
    +---> [2d] Aggregate recommendations
    |         |
    |         +---> If conflict detected:
    |               AskUserQuestion: "Consultants disagree on {topic}.
    |               Statistician: {opinion1}
    |               Mathematician: {opinion2}
    |               Which approach do you prefer?"
    |
    +---> [2e] Generate chapter{N}-notebook-plans.md
    |
    v
[3] Update session state
    |
    +---> Set current_phase: 2
    +---> Set completed_phases: [0, 1, 2]
    +---> Record outputs.chapter_plans
    |
    v
END Phase 2 -> Quality Gate 2
```

### Task Tool Invocation Pattern

Launch all consultants simultaneously using Task tool (fan-out):

**Statistician consultant:**
  Launch via Task tool.
  Description: "Statistician consultant: Review statistical approaches for chapter analyses"
  Prompt: Include the chapter analysis requirements. Ask for: statistical method recommendations, power analysis considerations, multiple comparison handling, and validation approaches. Write output to `{session_dir}/consultations/statistician-review.md`.

**Mathematician consultant:**
  Launch via Task tool.
  Description: "Mathematician consultant: Review algorithms for chapter analyses"
  Prompt: Include the chapter analysis requirements. Ask for: algorithm recommendations, complexity analysis, convergence properties, and numerical stability considerations. Write output to `{session_dir}/consultations/mathematician-review.md`.

**Programmer consultant:**
  Launch via Task tool.
  Description: "Programmer consultant: Review data requirements for chapter analyses"
  Prompt: Include the chapter analysis requirements. Ask for: data format requirements, library recommendations, performance considerations, and implementation approach. Write output to `{session_dir}/consultations/programmer-review.md`.

All three run simultaneously in separate contexts. When all complete, aggregate results (fan-in) for quality gate evaluation.

### Error Handling for Fan-Out

```
For each consultant result:
    |
    +---> If SUCCESS: Add to aggregation
    |
    +---> If FAILURE:
          |
          +---> Retry once (wait 30s)
          |
          +---> If retry fails:
                |
                +---> If statistician (critical):
                |     Escalate to user with Template 1
                |
                +---> If mathematician/programmer (optional):
                      Log warning, proceed without
```

### Quality Gate 2 Criteria

- [ ] All chapters have analysis plans
- [ ] No unresolved critical conflicts
- [ ] Each analysis has statistical approach defined
- [ ] Data flow is consistent (outputs match downstream inputs)

---

## Phase 3: Structure Review

**Duration**: ~5 minutes
**Owner**: structure-reviewer (Haiku)
**Timeout**: 10 minutes

### Workflow Steps

```
START Phase 3
    |
    v
[1] Read all planning artifacts
    |
    +---> research-structure.md
    +---> All chapter{N}-notebook-plans.md
    |
    v
[2] Check for issues:
    |
    +---> Missing dependencies
    +---> Redundant analyses
    +---> Logical flow problems
    +---> Incomplete specifications
    +---> Missing quality controls
    |
    v
[3] Categorize issues by severity
    |
    +---> Critical: Blocks execution
    +---> Major: Affects quality
    +---> Minor: Improvement opportunity
    |
    v
[4] Generate structure-review-report.md
    |
    v
[5] Present to user (USER APPROVAL GATE 1)
    |
    AskUserQuestion:
    "Structure Review Complete

    Summary:
    - {N} chapters planned
    - {M} analyses total
    - {K} issues identified (X critical, Y major, Z minor)

    Critical Issues:
    {list}

    Approve / Request changes / Reject? [A/c/r]"
    |
    +---> If "A": Proceed to Phase 4
    |
    +---> If "c":
    |     Ask "What changes?"
    |     Route to appropriate phase
    |     Re-run affected phases
    |     Return to this gate
    |
    +---> If "r":
          Ask "Return to Phase 1 or 2? [1/2]"
          Jump to selected phase
    |
    v
[6] Update session state
    |
    +---> Record user_approvals.phase_3
    |
    v
END Phase 3 -> Phase 4
```

### Quality Gate 3 Criteria (User Approval)

- [ ] User reviewed structure summary
- [ ] User approved or requested specific changes
- [ ] All critical issues addressed (if any)

---

## Phase 4: Plan Review

**Duration**: ~10 minutes
**Owner**: notebook-reviewer (Sonnet 4.5)
**Timeout**: 15 minutes total

### Workflow Steps

```
START Phase 4
    |
    v
[1] Read all chapter plans
    |
    v
[2] Fan-out: One reviewer per chapter (PARALLEL)
    |
    +---> For each chapter:
          |
          Task: notebook-reviewer
          Prompt: "Review analysis plans for Chapter {N}:
                   {chapter_plan_content}

                   Check:
                   - Pseudocode completeness
                   - Statistical correctness
                   - Data flow consistency
                   - Edge case coverage"
          Timeout: 5 min per chapter
    |
    v
[3] Fan-in: Aggregate review results
    |
    +---> Handle partial failures (proceed with available)
    |
    v
[4] Generate notebook-review-report.md
    |
    v
[5] Present to user (USER APPROVAL GATE 2)
    |
    AskUserQuestion:
    "Plan Review Complete

    Per-Chapter Summary:
    - Chapter 1: {N} analyses, {K} issues
    - Chapter 2: {N} analyses, {K} issues
    ...

    Critical Issues:
    {list}

    Approve / Request changes / Reject? [A/c/r]"
    |
    +---> Handle responses (same as Phase 3)
    |
    v
[6] Update session state
    |
    +---> Record user_approvals.phase_4
    |
    v
END Phase 4 -> Phase 5
```

---

## Phase 5: Document Generation

**Duration**: ~10 minutes
**Owner**: Orchestrator (Step 1) + notebook-generator (Step 2)
**Timeout**: 20 minutes total

### Workflow Steps

```
START Phase 5
    |
    v
[1] Read all approved chapter plans + research-structure.md
    |
    v
[2] STEP 1: Generate Master Strategy Overview (Orchestrator)
    |
    +---> Read research-structure.md and all chapter{N}-notebook-plans.md
    +---> Synthesize into analysis-strategy-overview.md
    +---> Write to {output_dir}/ and {session_dir}/
    |
    v
[3] STEP 2: Fan-out: One generator per chapter (PARALLEL)
    |
    +---> For each chapter:
          |
          Task: notebook-generator
          Prompt: "Generate markdown analysis documents for Chapter {N}:
                   {chapter_plan_content}

                   Output to: {output_dir}/chapter{N}_{slug}/
                   Use hybrid prose + fenced pseudocode format.
                   Required sections: Goal, Statistical Approach,
                   Prerequisites, Analysis Steps, Expected Outputs,
                   Notes and Caveats."
          Timeout: 7 min per chapter
    |
    v
[4] Fan-in: Collect generation results
    |
    +---> Track success/failure per chapter
    |
    v
[5] Validate generated analysis documents
    |
    +---> For each .md file:
          - Check required sections present (Goal, Statistical Approach,
            Analysis Steps, Expected Outputs)
          - Check at least one fenced code block exists
          - Check balanced code fences
    |
    v
[6] Copy to session directory (backup in analyses/)
    |
    v
[7] Handle partial failures
    |
    +---> If some chapters failed:
          AskUserQuestion:
          "{M} of {N} chapters generated successfully.
          Failed: {list}

          (A) Proceed with available analysis documents
          (B) Retry failed chapters
          (C) Abort"
    |
    v
[8] Update session state
    |
    +---> Record outputs.analyses and outputs.strategy_overview
    |
    v
END Phase 5 -> Quality Gate 5
```

### Analysis Document Generation Details

Each analysis document is generated as a markdown file with this structure:

```markdown
# Analysis Title

<!-- Generated by: scientific-analysis-architect v2.0.0 -->
<!-- Session: {session_id} -->
<!-- Chapter: {N}, Analysis: {M} -->

## Goal
Prose description of what this analysis achieves.

## Statistical Approach
Method, justification, assumptions, and corrections.

## Prerequisites
- Input data and format
- Required libraries
- Upstream dependencies

## Analysis Steps

### Step 1: [Name]
Prose explanation of what this step does and why.

```python
# Pseudocode for step 1
# TODO: Implement
```

### Step 2: [Name]
...

## Expected Outputs
- Output files/objects, format, characteristics

## Notes and Caveats
- Assumptions, limitations, alternatives
```

**Code Block Formatting Rules**:
- Use triple backticks with `python` language identifier
- Never nest fenced code blocks
- If pseudocode contains triple-quoted strings, use single-quoted triple quotes in comments
- For multi-line string literals, use comment notation

### Quality Gate 5 Criteria

- [ ] All analysis documents created (or partial with user approval)
- [ ] Each document has required sections (Goal, Statistical Approach, Analysis Steps, Expected Outputs)
- [ ] Each document has at least one fenced code block
- [ ] Balanced code fences in all documents
- [ ] Master strategy overview exists with required sections
- [ ] Backup copies exist in session directory (analyses/)
- [ ] File naming follows convention (analysis{N}_{M}_{slug}.md)

---

## Phase 6: Statistical Fact-Checking

**Duration**: ~10-20 minutes
**Owner**: statistical-fact-checker (Sonnet 4.5)
**Timeout**: 30 minutes

### Workflow Steps

```
START Phase 6
    |
    v
[1] Read all generated analysis documents
    |
    v
[2] Analyze for statistical concerns
    |
    +---> Test mismatches
    +---> Multiple testing issues
    +---> Interpretation errors
    +---> Assumption violations
    +---> Effect size gaps
    |
    v
[3] Categorize concerns by severity
    |
    +---> Critical: Incorrect conclusions
    +---> Standard: Best practice violation
    +---> Minor: Improvement opportunity
    |
    v
[4] Count total concerns
    |
    +---> If 0 concerns:
    |     Show justification
    |     Proceed to completion
    |
    +---> If <= 5 concerns:
    |     Enter interview mode (one at a time)
    |
    +---> If > 5 concerns:
          Show summary first
          Offer batch options
          Then interview mode
    |
    v
[5] INTERVIEW MODE (see interview-protocol.md)
    |
    v
[6] Accumulate decisions
    |
    +---> accepted: list
    +---> rejected: list
    +---> skipped: list
    |
    v
[7] Generate reports
    |
    +---> statistical-review-report.md
    +---> corrections-manifest.json
    |
    v
[8] Apply corrections (if user approves)
    |
    AskUserQuestion:
    "Summary:
    - {X} accepted, {Y} rejected, {Z} skipped

    Apply all accepted corrections now? [yes/no]"
    |
    +---> If yes: Apply corrections to affected analysis documents
    +---> If no: Save manifest for later
    |
    v
[9] Post-Interview: If corrections applied, refresh overview
    |
    +---> Read all corrected analysis documents
    +---> Regenerate analysis-strategy-overview.md
    +---> Update Consolidated Methods table
    +---> Update affected Chapter Summaries
    +---> Validate overview against Gate 5 overview criteria
    |
    v
[10] Update session state
    |
    +---> Set status: "completed"
    |
    v
END Phase 6 -> Quality Gate 6 -> Phase 7
```

### Quality Gate 6 Criteria (User Approval)

- [ ] All concerns reviewed (or explicitly skipped)
- [ ] User approved correction application decision
- [ ] Statistical review report generated
- [ ] Corrections manifest saved
- [ ] If corrections applied: overview refreshed and validated

---

## Phase 7: Audience Document Generation

**Duration**: ~5 minutes
**Owner**: Orchestrator
**Timeout**: 15 minutes

### Workflow Steps

```
START Phase 7
    |
    v
[1] Pre-flight validation
    |
    +---> Verify Tier 1 artifacts exist (analysis-strategy-overview.md, research-structure.md, session-state.json)
    +---> If corrections-manifest.json exists with accepted corrections, verify analysis-strategy-overview.md was modified after it
    +---> Abort with clear error if critical artifacts missing
    |
    v
[2] Create directory
    |
    +---> Create {output_dir}/.research-architecture/ if not exists
    |
    v
[3] Generate researcher plan
    |
    +---> Read Tier 1 sources: analysis-strategy-overview.md, research-structure.md
    +---> Read Tier 2 sources: chapter{N}-notebook-plans.md
    +---> Write {output_dir}/researcher-plan.md (Template A)
    +---> Prose-only, no code blocks, domain language
    |
    v
[4] Generate architect handoff
    |
    +---> Read Tier 1 sources + session-state.json
    +---> Read Tier 4 sources (if exist): review reports, corrections-manifest.json
    +---> Write {output_dir}/.research-architecture/architect-handoff.md (Template B)
    +---> Design rationale, method log, current state, open questions
    |
    v
[5] Generate engineering translation
    |
    +---> Read Tier 1 and Tier 2 sources
    +---> Read Tier 3 sources per-chapter (selective, as needed)
    +---> Write {output_dir}/.research-architecture/engineering-translation.md (Template C)
    +---> System overview, pipeline architecture, data specs, processing stages
    |
    v
[6] Create backup copies
    |
    +---> Create {session_dir}/audience-documents/ if not exists
    +---> Copy all three documents to backup location
    |
    v
[7] Update session state
    |
    +---> Set current_phase: 7
    +---> Add 7 to completed_phases
    +---> Record paths in outputs.audience_documents
    +---> Set status: "completed"
    |
    v
END Phase 7 -> Quality Gate 7 -> Workflow Complete
```

### On Resume

Before regenerating documents:
1. Check which audience documents already exist
2. Validate existing documents against Gate 7 section requirements
3. Skip re-generation for documents that pass validation
4. Only regenerate missing or invalid documents

### Quality Gate 7 Criteria

- [ ] `{output_dir}/researcher-plan.md` exists and is non-empty (> 500 bytes)
- [ ] `{output_dir}/.research-architecture/architect-handoff.md` exists and is non-empty
- [ ] `{output_dir}/.research-architecture/engineering-translation.md` exists and is non-empty
- [ ] Researcher plan has required sections (case-insensitive): Research Overview, Research Questions, Expected Outcomes, Decision Points
- [ ] Architect handoff has required sections: Design Rationale, Current State, Open Questions, Continuation Guidance
- [ ] Engineering translation has required sections: System Overview, Pipeline Architecture, Data Specifications, Processing Stages, Resource Requirements, Dependencies
- [ ] No fenced code blocks (```) in researcher-plan.md
- [ ] Backup copies exist in `{session_dir}/audience-documents/`
- [ ] All three documents include provenance metadata (HTML comments with session ID)
