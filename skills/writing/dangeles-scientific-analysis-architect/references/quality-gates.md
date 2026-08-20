# Quality Gates

Definitions and criteria for all quality gates in the scientific-analysis-architect workflow.

## Gate Definitions

### Quality Gate 0: Initialization

**Phase**: 0
**Owner**: Orchestrator
**Type**: Automated

**Pass Criteria**:
- [ ] Session directory created successfully
- [ ] Session directory is writable (test file created and deleted)
- [ ] Output directory exists and is writable
- [ ] session-state.json initialized with valid schema

**Validation Code**:
```python
def validate_gate_0(session_state: dict) -> bool:
    """Validate initialization gate."""

    # Check session directory
    session_dir = session_state["config"]["session_directory"]
    if not os.path.exists(session_dir):
        return False, "Session directory does not exist"

    # Write test
    test_file = os.path.join(session_dir, ".write_test")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        return False, f"Session directory not writable: {e}"

    # Check output directory
    output_dir = session_state["config"]["output_directory"]
    if not os.path.isdir(output_dir):
        return False, "Output directory does not exist"

    return True, "Gate 0 passed"
```

**Fail Action**: Abort workflow with clear error message

---

### Quality Gate 1: Research Structure

**Phase**: 1
**Owner**: research-architect
**Type**: Automated

**Pass Criteria**:
- [ ] research-structure.md file exists
- [ ] File is valid markdown
- [ ] Contains 3-7 chapters (inclusive)
- [ ] Each chapter has:
  - [ ] Title (non-empty string)
  - [ ] Goal (one of: atlas, hypothesis, mechanism)
  - [ ] At least 1 analysis listed
- [ ] Dependencies reference valid chapter numbers
- [ ] No circular dependencies

**Validation Code**:
```python
def validate_gate_1(session_dir: str) -> tuple:
    """Validate research structure gate."""

    structure_path = os.path.join(session_dir, "research-structure.md")

    # File exists
    if not os.path.exists(structure_path):
        return False, "research-structure.md not found"

    # Parse structure
    with open(structure_path) as f:
        content = f.read()

    chapters = parse_chapters(content)

    # Chapter count
    if not (3 <= len(chapters) <= 7):
        return False, f"Invalid chapter count: {len(chapters)} (expected 3-7)"

    # Validate each chapter
    valid_goals = {"atlas", "hypothesis", "mechanism"}
    for i, chapter in enumerate(chapters, 1):
        if not chapter.get("title"):
            return False, f"Chapter {i} missing title"
        if chapter.get("goal") not in valid_goals:
            return False, f"Chapter {i} invalid goal: {chapter.get('goal')}"
        if not chapter.get("analyses"):
            return False, f"Chapter {i} has no analyses"

    # Check dependencies
    chapter_nums = set(range(1, len(chapters) + 1))
    for chapter in chapters:
        for dep in chapter.get("dependencies", []):
            if dep not in chapter_nums:
                return False, f"Invalid dependency: Chapter {dep}"
            if dep >= chapter["number"]:
                return False, f"Circular/forward dependency: Chapter {chapter['number']} -> {dep}"

    return True, f"Gate 1 passed: {len(chapters)} chapters validated"
```

**Fail Action**: Return to Phase 1 with specific feedback

---

### Quality Gate 2: Chapter Plans

**Phase**: 2
**Owner**: analysis-planner
**Type**: Automated

**Pass Criteria**:
- [ ] All chapter{N}-notebook-plans.md files exist
- [ ] Each chapter plan has:
  - [ ] At least 1 analysis defined
  - [ ] Statistical approach for each analysis
  - [ ] No unresolved critical conflicts
- [ ] Data flow is consistent:
  - [ ] Outputs defined for each analysis
  - [ ] Inputs available from upstream analyses or user data

**Validation Code**:
```python
def validate_gate_2(session_dir: str, num_chapters: int) -> tuple:
    """Validate chapter plans gate."""

    plans = []
    for i in range(1, num_chapters + 1):
        plan_path = os.path.join(session_dir, f"chapter{i}-notebook-plans.md")

        if not os.path.exists(plan_path):
            return False, f"chapter{i}-notebook-plans.md not found"

        with open(plan_path) as f:
            plan = parse_chapter_plan(f.read())

        # At least one analysis
        if not plan.get("analyses"):
            return False, f"Chapter {i} has no analyses"

        # Statistical approach required
        for analysis in plan["analyses"]:
            if not analysis.get("statistical_approach"):
                return False, f"Chapter {i} analysis {analysis['number']} missing statistical approach"

        # Check for unresolved conflicts
        if plan.get("unresolved_conflicts"):
            return False, f"Chapter {i} has unresolved conflicts: {plan['unresolved_conflicts']}"

        plans.append(plan)

    # Validate data flow
    available_outputs = set(["user_data"])
    for plan in plans:
        for analysis in plan["analyses"]:
            # Check inputs available
            for input_req in analysis.get("data_requirements", {}).get("inputs", []):
                if input_req not in available_outputs:
                    return False, f"Input not available: {input_req}"

            # Add outputs to available
            for output in analysis.get("data_requirements", {}).get("outputs", []):
                available_outputs.add(output)

    total_analyses = sum(len(p["analyses"]) for p in plans)
    return True, f"Gate 2 passed: {total_analyses} analyses across {num_chapters} chapters"
```

**Fail Action**: Return to Phase 2 with specific feedback

---

### Quality Gate 3: Structure Approval (USER)

**Phase**: 3
**Owner**: User
**Type**: Human judgment

**Presentation**:
```
Structure Review Complete

Summary:
- {N} chapters planned
- {M} analyses total
- {K} issues identified (X critical, Y major, Z minor)

Critical Issues:
{list or "None"}

Major Issues:
{list or "None"}

Approve / Request changes / Reject? [A/c/r]
```

**Pass Criteria**:
- [ ] User explicitly approves (enters "A")
- [ ] OR user requests changes and changes are implemented

**Responses**:
- **A (Approve)**: Record approval, proceed to Phase 4
- **c (Changes)**: Gather feedback, re-run affected phases, return to gate
- **r (Reject)**: Ask which phase to return to (1 or 2)

**Fail Action**: Loop until approved or workflow aborted

---

### Quality Gate 4: Notebook Approval (USER)

**Phase**: 4
**Owner**: User
**Type**: Human judgment

**Presentation**:
```
Plan Review Complete

Per-Chapter Summary:
- Chapter 1: {N} analyses, {K} issues
- Chapter 2: {N} analyses, {K} issues
...

Critical Issues:
{list or "None"}

Approve / Request changes / Reject? [A/c/r]
```

**Pass Criteria**:
- [ ] User explicitly approves (enters "A")
- [ ] OR all critical issues addressed after changes

**Responses**: Same as Gate 3

**Fail Action**: Loop until approved or workflow aborted

---

### Quality Gate 5: Analysis Document Validation

**Phase**: 5
**Owner**: Orchestrator + notebook-generator
**Type**: Automated

**Pass Criteria**:
- [ ] All expected analysis documents created
- [ ] Each document has required sections (Goal, Statistical Approach, Analysis Steps, Expected Outputs)
- [ ] Each document has at least one fenced code block
- [ ] Balanced code fences in all documents
- [ ] Master strategy overview exists with required sections
- [ ] Backup copies exist in session directory (analyses/)

**Validation Code**:
```python
import os
import re

REQUIRED_SECTIONS = {
    "goal": [r'^##\s+(Goal|Objective|Goals)\b'],
    "statistical_approach": [r'^##\s+(Statistical Approach|Statistical Method|Methods)\b'],
    "analysis_steps": [r'^##\s+(Analysis Steps|Steps|Workflow Steps)\b'],
    "expected_outputs": [r'^##\s+(Expected Outputs|Outputs|Results)\b']
}

def validate_analysis_document(path: str) -> tuple:
    """Validate markdown analysis document structure."""
    if not os.path.exists(path):
        return False, f"Document not found: {path}"

    with open(path) as f:
        content = f.read()

    if len(content.strip()) == 0:
        return False, f"Empty file: {path}"

    # Check required sections
    missing = []
    for section_name, patterns in REQUIRED_SECTIONS.items():
        found = any(
            re.search(p, content, re.MULTILINE | re.IGNORECASE)
            for p in patterns
        )
        if not found:
            missing.append(section_name)

    if missing:
        return False, f"Missing sections in {path}: {missing}"

    # Check for at least one fenced code block
    if '```' not in content:
        return False, f"No code blocks found in {path}"

    # Check balanced fences
    fence_count = content.count('```')
    if fence_count % 2 != 0:
        return False, f"Unbalanced code fences in {path} ({fence_count} backtick markers)"

    return True, f"Valid: {path}"

def validate_gate_5(session_state: dict) -> tuple:
    """Validate markdown analysis document generation (Gate 5)."""
    expected = session_state["outputs"].get("analyses", [])
    if not expected:
        return False, "No analysis documents generated"

    for doc_path in expected:
        valid, msg = validate_analysis_document(doc_path)
        if not valid:
            return False, msg

    # Check master overview
    overview_path = os.path.join(
        session_state["config"]["output_directory"],
        "analysis-strategy-overview.md"
    )
    if not os.path.exists(overview_path):
        return False, "Master strategy overview not found"

    # Check overview required sections
    OVERVIEW_SECTIONS = [
        r'^##\s+Project Objective',
        r'^##\s+Strategy at a Glance',
        r'^##\s+Chapter Summaries',
        r'^##\s+Data Flow',
        r'^##\s+Execution Order'
    ]
    with open(overview_path) as f:
        overview_content = f.read()
    for pattern in OVERVIEW_SECTIONS:
        if not re.search(pattern, overview_content, re.MULTILINE):
            return False, f"Master overview missing section: {pattern}"

    # Check backup directory
    backup_dir = os.path.join(
        session_state["config"]["session_directory"],
        "analyses"
    )
    if not os.path.exists(backup_dir):
        return False, "Backup directory not found"

    return True, f"Gate 5 passed: {len(expected)} valid analysis documents + master overview"
```

**Fail Action**:
- If partial failure: Offer to proceed with available or retry failed
- If total failure: Return to Phase 5 with error details

---

### Quality Gate 6: Statistical Review (USER)

**Phase**: 6
**Owner**: User
**Type**: Human judgment (Interview mode)

**Pass Criteria**:
- [ ] All concerns reviewed (accepted, rejected, or skipped)
- [ ] User confirmed correction application decision
- [ ] If corrections applied: analysis documents re-validated
- [ ] If corrections applied: master overview refreshed and validated

**Validation Code**:
```python
def validate_gate_6(session_state: dict) -> tuple:
    """Validate statistical review gate."""

    corrections = session_state.get("corrections", {})

    # All concerns have decisions
    total = (
        len(corrections.get("accepted", [])) +
        len(corrections.get("rejected", [])) +
        len(corrections.get("skipped", []))
    )

    expected = session_state.get("total_concerns", 0)
    if total < expected:
        return False, f"Not all concerns reviewed: {total}/{expected}"

    # If corrections applied, verify analysis documents
    if corrections.get("applied"):
        for doc_path in session_state["outputs"]["analyses"]:
            valid, msg = validate_analysis_document(doc_path)
            if not valid:
                return False, f"Corrected document invalid: {msg}"

        # Verify overview was refreshed
        overview_path = session_state["outputs"].get("strategy_overview")
        if overview_path and not os.path.exists(overview_path):
            return False, "Master overview not refreshed after corrections"

    return True, "Gate 6 passed: Statistical review complete"
```

**Fail Action**: Resume interview from last concern

---

### Quality Gate 7: Audience Document Validation

**Phase**: 7
**Owner**: Orchestrator
**Type**: Automated

**Pass Criteria**:
- [ ] `{output_dir}/researcher-plan.md` exists and is non-empty (> 500 bytes)
- [ ] `{output_dir}/.research-architecture/architect-handoff.md` exists and is non-empty
- [ ] `{output_dir}/.research-architecture/engineering-translation.md` exists and is non-empty
- [ ] Researcher plan has required sections (case-insensitive): Research Overview, Research Questions, Expected Outcomes, Decision Points
- [ ] Architect handoff has required sections: Design Rationale, Current State, Open Questions, Continuation Guidance
- [ ] Engineering translation has required sections: System Overview, Pipeline Architecture, Data Specifications, Processing Stages, Resource Requirements, Dependencies
- [ ] No fenced code blocks (```) in researcher-plan.md
- [ ] Backup copies exist in `{session_dir}/audience-documents/`
- [ ] All three documents include provenance metadata (HTML comments with session ID)

**Validation Code**:
```python
import re
import os

RESEARCHER_SECTIONS = {
    "research_overview": [r'^##\s+Research Overview'],
    "research_questions": [r'^##\s+Research Questions'],
    "expected_outcomes": [r'^##\s+Expected Outcomes'],
    "decision_points": [r'^##\s+Decision Points']
}

ARCHITECT_SECTIONS = {
    "design_rationale": [r'^##\s+Design Rationale'],
    "current_state": [r'^##\s+Current State'],
    "open_questions": [r'^##\s+Open Questions'],
    "continuation": [r'^##\s+Continuation Guidance']
}

ENGINEERING_SECTIONS = {
    "system_overview": [r'^##\s+System Overview'],
    "pipeline_architecture": [r'^##\s+Pipeline Architecture'],
    "data_specifications": [r'^##\s+Data Specifications'],
    "processing_stages": [r'^##\s+Processing Stages'],
    "resource_requirements": [r'^##\s+Resource Requirements'],
    "dependencies": [r'^##\s+Dependencies']
}

def validate_gate_7(output_dir: str, session_dir: str) -> tuple:
    """Validate audience document gate."""

    researcher_plan = os.path.join(output_dir, "researcher-plan.md")
    architect_handoff = os.path.join(output_dir, ".research-architecture", "architect-handoff.md")
    engineering_translation = os.path.join(output_dir, ".research-architecture", "engineering-translation.md")

    # Check existence and minimum size
    for path, name in [(researcher_plan, "researcher plan"),
                       (architect_handoff, "architect handoff"),
                       (engineering_translation, "engineering translation")]:
        if not os.path.exists(path):
            return False, f"{name} does not exist"
        if os.path.getsize(path) < 500:
            return False, f"{name} is too small (< 500 bytes)"

    # Read contents
    with open(researcher_plan) as f:
        researcher_content = f.read()
    with open(architect_handoff) as f:
        architect_content = f.read()
    with open(engineering_translation) as f:
        engineering_content = f.read()

    # Check sections (case-insensitive)
    for content, sections, name in [
        (researcher_content, RESEARCHER_SECTIONS, "researcher plan"),
        (architect_content, ARCHITECT_SECTIONS, "architect handoff"),
        (engineering_content, ENGINEERING_SECTIONS, "engineering translation")
    ]:
        for section_key, patterns in sections.items():
            found = False
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    found = True
                    break
            if not found:
                return False, f"{name} missing section: {section_key}"

    # Check no code blocks in researcher plan
    if '```' in researcher_content:
        return False, "researcher plan contains code blocks (must be prose-only)"

    # Check backups
    backup_dir = os.path.join(session_dir, "audience-documents")
    for filename in ["researcher-plan.md", "architect-handoff.md", "engineering-translation.md"]:
        backup_path = os.path.join(backup_dir, filename)
        if not os.path.exists(backup_path):
            return False, f"backup copy missing: {filename}"

    # Check provenance metadata
    for content, name in [(researcher_content, "researcher plan"),
                          (architect_content, "architect handoff"),
                          (engineering_content, "engineering translation")]:
        if "Session:" not in content:
            return False, f"{name} missing provenance metadata"

    return True, "Gate 7 passed: All audience documents validated"
```

**Fail Action**:
- If document generation fails: Retry failed documents (up to 2 attempts per document)
- If backup fails but documents exist: Retry backup only, warn if still fails
- If total failure: Proceed without audience documents, warn user, mark Phase 7 as "degraded"

---

## Pass/Fail Actions Summary

| Gate | On Pass | On Fail |
|------|---------|---------|
| 0 | Proceed to Phase 1 | Abort workflow |
| 1 | Proceed to Phase 2 | Retry Phase 1 |
| 2 | Proceed to Phase 3 | Retry Phase 2 |
| 3 | Proceed to Phase 4 | Handle user choice |
| 4 | Proceed to Phase 5 | Handle user choice |
| 5 | Proceed to Phase 6 | Partial proceed or retry |
| 6 | Proceed to Phase 7 | Resume interview |
| 7 | Complete workflow | Retry documents or proceed without |

## Minimum Thresholds

These thresholds cannot be bypassed:

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| Minimum chapters | 3 | Ensures meaningful analysis structure |
| Maximum chapters | 7 | Prevents scope creep |
| Analysis documents per chapter | >= 1 | Each chapter must produce output |
| Statistical approach | Required | Core purpose of skill |
| Markdown structure validation | Required | Ensures usable output |

## Quality Gate Flow Diagram

```
Start
  |
  v
[Gate 0] --FAIL--> Abort
  |
  PASS
  |
  v
Phase 1
  |
  v
[Gate 1] --FAIL--> Retry Phase 1
  |
  PASS
  |
  v
Phase 2
  |
  v
[Gate 2] --FAIL--> Retry Phase 2
  |
  PASS
  |
  v
Phase 3
  |
  v
[Gate 3: USER] --REJECT--> Return to Phase 1 or 2
  |           --CHANGES--> Implement changes, re-check
  |
  APPROVE
  |
  v
Phase 4
  |
  v
[Gate 4: USER] --REJECT--> Return to earlier phase
  |           --CHANGES--> Implement changes, re-check
  |
  APPROVE
  |
  v
Phase 5
  |
  v
[Gate 5] --PARTIAL--> Proceed with available / Retry failed
  |      --TOTAL FAIL--> Retry Phase 5
  |
  PASS
  |
  v
Phase 6
  |
  v
[Gate 6: USER] --INCOMPLETE--> Resume interview
  |
  COMPLETE
  |
  v
Phase 7
  |
  v
[Gate 7] --PARTIAL--> Proceed with available documents, warn user
  |      --TOTAL FAIL--> Proceed without audience documents (degraded)
  |
  PASS
  |
  v
Workflow Complete
```

## Bypassing Gates

Gates 0, 1, 2, 5, and 7 cannot be bypassed (automated validation).

Gates 3, 4, and 6 can be "bypassed" by user choice:
- Gate 3: User can approve with known issues
- Gate 4: User can approve with known issues
- Gate 6: User can skip remaining concerns

When a user bypasses a gate, a warning is logged:

```json
{
  "gate": 3,
  "bypassed": true,
  "reason": "User approved with 2 unresolved minor issues",
  "timestamp": "2026-02-04T14:55:00Z",
  "known_issues": ["Issue 1", "Issue 2"]
}
```
