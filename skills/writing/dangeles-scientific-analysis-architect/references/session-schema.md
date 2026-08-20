# Session Schema

Complete specification for session state management and resume capability.

## session-state.json

### Full Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Scientific Analysis Architect Session State",
  "type": "object",
  "required": ["version", "session_id", "created_at", "status", "current_phase"],
  "properties": {
    "version": {
      "type": "string",
      "description": "Schema version",
      "enum": ["1.0", "2.0", "2.1"]
    },
    "session_id": {
      "type": "string",
      "description": "Unique session identifier",
      "pattern": "^session-[0-9]{8}-[0-9]{6}-[0-9]+$"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Session creation timestamp (ISO 8601)"
    },
    "last_updated": {
      "type": "string",
      "format": "date-time",
      "description": "Last state update timestamp"
    },
    "status": {
      "type": "string",
      "enum": ["initialized", "in_progress", "completed", "interrupted", "aborted", "error"],
      "description": "Current session status"
    },
    "current_phase": {
      "type": "integer",
      "minimum": 0,
      "maximum": 7,
      "description": "Currently executing phase (0-7)"
    },
    "completed_phases": {
      "type": "array",
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 7
      },
      "description": "List of successfully completed phases"
    },
    "user_approvals": {
      "type": "object",
      "description": "User approval decisions at gates",
      "properties": {
        "phase_3": {
          "$ref": "#/definitions/approval"
        },
        "phase_4": {
          "$ref": "#/definitions/approval"
        },
        "phase_6": {
          "$ref": "#/definitions/approval"
        }
      }
    },
    "config": {
      "type": "object",
      "description": "Session configuration",
      "properties": {
        "output_directory": {
          "type": "string",
          "description": "User-specified output directory path"
        },
        "session_directory": {
          "type": "string",
          "description": "Session working directory path"
        },
        "num_chapters": {
          "type": "integer",
          "minimum": 3,
          "maximum": 7,
          "description": "Number of chapters in research structure"
        }
      }
    },
    "outputs": {
      "type": "object",
      "description": "Generated output file references",
      "properties": {
        "research_structure": {
          "type": "string",
          "description": "Path to research-structure.md"
        },
        "chapter_plans": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Paths to chapter{N}-notebook-plans.md files"
        },
        "structure_review": {
          "type": "string",
          "description": "Path to structure-review-report.md"
        },
        "notebook_review": {
          "type": "string",
          "description": "Path to notebook-review-report.md"
        },
        "analyses": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Paths to generated .md analysis documents"
        },
        "strategy_overview": {
          "type": "string",
          "description": "Path to analysis-strategy-overview.md"
        },
        "statistical_review": {
          "type": "string",
          "description": "Path to statistical-review-report.md"
        },
        "corrections_manifest": {
          "type": "string",
          "description": "Path to corrections-manifest.json"
        },
        "audience_documents": {
          "type": "object",
          "description": "Audience-targeted document references (Phase 7)",
          "properties": {
            "researcher_plan": {
              "type": "string",
              "description": "Path to researcher-plan.md"
            },
            "architect_handoff": {
              "type": "string",
              "description": "Path to architect-handoff.md"
            },
            "engineering_translation": {
              "type": "string",
              "description": "Path to engineering-translation.md"
            }
          }
        }
      }
    },
    "user_context": {
      "type": "object",
      "description": "User-provided context captured during workflow",
      "properties": {
        "dataset_description": {
          "type": "string",
          "description": "User description of their dataset"
        },
        "research_goals": {
          "type": "string",
          "description": "User's stated research goals"
        },
        "biological_context": {
          "type": "object",
          "description": "Biological context gathered via AskUserQuestion",
          "additionalProperties": { "type": "string" }
        }
      }
    },
    "errors": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/error_entry"
      },
      "description": "Log of errors encountered during session"
    },
    "agent_execution_log": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/agent_execution"
      },
      "description": "Log of agent executions for debugging"
    }
  },
  "definitions": {
    "approval": {
      "type": "object",
      "properties": {
        "approved": { "type": "boolean" },
        "timestamp": { "type": "string", "format": "date-time" },
        "feedback": { "type": "string" },
        "changes_requested": { "type": "array", "items": { "type": "string" } }
      }
    },
    "error_entry": {
      "type": "object",
      "properties": {
        "timestamp": { "type": "string", "format": "date-time" },
        "phase": { "type": "integer" },
        "agent": { "type": "string" },
        "error_type": { "type": "string" },
        "error_message": { "type": "string" },
        "retry_count": { "type": "integer" },
        "resolution": { "type": "string" }
      }
    },
    "agent_execution": {
      "type": "object",
      "properties": {
        "timestamp": { "type": "string", "format": "date-time" },
        "agent": { "type": "string" },
        "phase": { "type": "integer" },
        "duration_seconds": { "type": "number" },
        "status": { "type": "string", "enum": ["success", "failure", "timeout"] },
        "output_files": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

### Example session-state.json

```json
{
  "version": "2.0",
  "session_id": "session-20260204-143022-12345",
  "created_at": "2026-02-04T14:30:22Z",
  "last_updated": "2026-02-04T15:02:45Z",
  "status": "in_progress",
  "current_phase": 4,
  "completed_phases": [0, 1, 2, 3],
  "user_approvals": {
    "phase_3": {
      "approved": true,
      "timestamp": "2026-02-04T14:55:00Z",
      "feedback": null,
      "changes_requested": []
    }
  },
  "config": {
    "output_directory": "/Users/researcher/projects/rnaseq-analysis",
    "session_directory": "/Users/researcher/projects/rnaseq-analysis/.scientific-analysis-session",
    "num_chapters": 4
  },
  "outputs": {
    "research_structure": "research-structure.md",
    "chapter_plans": [
      "chapter1-notebook-plans.md",
      "chapter2-notebook-plans.md",
      "chapter3-notebook-plans.md",
      "chapter4-notebook-plans.md"
    ],
    "structure_review": "structure-review-report.md",
    "notebook_review": null,
    "analyses": [],
    "strategy_overview": null,
    "statistical_review": null,
    "corrections_manifest": null
  },
  "user_context": {
    "dataset_description": "Single-cell RNA-seq of mouse brain tissue. 50,000 cells across 4 conditions: wild-type young, wild-type old, mutant young, mutant old.",
    "research_goals": "Identify cell type markers and find differentially expressed genes between conditions to understand aging effects.",
    "biological_context": {
      "cell_types_of_interest": "neurons, astrocytes, microglia",
      "genes_of_interest": "inflammation markers, synaptic genes"
    }
  },
  "errors": [],
  "agent_execution_log": [
    {
      "timestamp": "2026-02-04T14:32:15Z",
      "agent": "research-architect",
      "phase": 1,
      "duration_seconds": 245.3,
      "status": "success",
      "output_files": ["research-structure.md"]
    },
    {
      "timestamp": "2026-02-04T14:38:00Z",
      "agent": "analysis-planner",
      "phase": 2,
      "duration_seconds": 520.1,
      "status": "success",
      "output_files": [
        "chapter1-notebook-plans.md",
        "chapter2-notebook-plans.md",
        "chapter3-notebook-plans.md",
        "chapter4-notebook-plans.md"
      ]
    }
  ]
}
```

---

## Resume Protocol

### Session Detection

On skill invocation, check for existing sessions:

```python
import os
import json
from datetime import datetime, timedelta

def find_resumable_sessions(output_dir: str) -> list:
    """Find sessions that can be resumed."""
    sessions = []

    # Check primary location (output_dir)
    primary_path = os.path.join(output_dir, ".scientific-analysis-session")
    if os.path.exists(primary_path):
        sessions.extend(check_session_dir(primary_path))

    # Check fallback location (/tmp)
    import glob
    for session_dir in glob.glob("/tmp/scientific-analysis-architect-session-*"):
        sessions.extend(check_session_dir(session_dir))

    # Filter to resumable sessions
    cutoff = datetime.now() - timedelta(hours=72)
    resumable = []

    for session in sessions:
        if session["status"] in ["in_progress", "interrupted"]:
            if session["last_updated"] > cutoff:
                resumable.append(session)

    return resumable

def check_session_dir(path: str) -> list:
    """Load session state from directory."""
    state_file = os.path.join(path, "session-state.json")
    if not os.path.exists(state_file):
        return []

    with open(state_file) as f:
        state = json.load(f)

    state["session_dir"] = path
    state["last_updated"] = datetime.fromisoformat(state["last_updated"])
    return [state]
```

### Resume Prompt

```
Found incomplete session from {timestamp}
Project: {research_goals_summary}
Status: Phase {current_phase} ({phase_name})
Completed: Phases {completed_list}

Resume from Phase {current_phase}? [yes/no]
```

### Resume Logic

```python
def resume_session(session_state: dict):
    """Resume workflow from saved state."""

    # Restore session directory
    os.chdir(session_state["session_dir"])

    # Validate outputs still exist
    for phase in session_state["completed_phases"]:
        if not validate_phase_outputs(phase, session_state):
            # Output missing - need to re-run phase
            session_state["completed_phases"].remove(phase)
            session_state["current_phase"] = min(
                session_state["current_phase"],
                phase
            )

    # Continue from current phase
    return run_workflow(
        start_phase=session_state["current_phase"],
        session_state=session_state
    )
```

---

## Checkpoint Protocol

### Per-Phase Checkpointing

After each phase completes successfully:

```python
def checkpoint_phase(phase: int, session_state: dict, outputs: dict):
    """Save checkpoint after phase completion."""

    # Update state
    session_state["current_phase"] = phase + 1
    session_state["completed_phases"].append(phase)
    session_state["last_updated"] = datetime.now().isoformat()

    # Record outputs
    for key, value in outputs.items():
        session_state["outputs"][key] = value

    # Write to file
    state_file = os.path.join(
        session_state["config"]["session_directory"],
        "session-state.json"
    )
    with open(state_file, "w") as f:
        json.dump(session_state, f, indent=2)

    # Log checkpoint
    print(f"[CHECKPOINT] Phase {phase} complete. State saved.")
```

### Rollback Capability

To rollback to a previous phase:

```python
def rollback_to_phase(target_phase: int, session_state: dict):
    """Rollback session to earlier phase."""

    # Remove phases after target
    session_state["completed_phases"] = [
        p for p in session_state["completed_phases"]
        if p < target_phase
    ]
    session_state["current_phase"] = target_phase

    # Clear outputs from later phases
    phase_outputs = {
        1: ["research_structure"],
        2: ["chapter_plans"],
        3: ["structure_review"],
        4: ["notebook_review"],
        5: ["analyses", "strategy_overview"],
        6: ["statistical_review", "corrections_manifest"],
        7: ["audience_documents"]
    }

    for phase in range(target_phase, 8):
        for output_key in phase_outputs.get(phase, []):
            session_state["outputs"][output_key] = None

    # Clear user approvals for later phases
    for approval_key in list(session_state["user_approvals"].keys()):
        approval_phase = int(approval_key.split("_")[1])
        if approval_phase >= target_phase:
            del session_state["user_approvals"][approval_key]

    # Save state
    checkpoint_phase(target_phase - 1, session_state, {})

    return session_state
```

---

## Traceability

### Decision Logging

All user decisions are logged:

```python
def log_user_decision(session_state: dict, decision: dict):
    """Log user decision for traceability."""

    if "user_decisions" not in session_state:
        session_state["user_decisions"] = []

    decision["timestamp"] = datetime.now().isoformat()
    session_state["user_decisions"].append(decision)
```

Example decisions:

```json
{
  "user_decisions": [
    {
      "timestamp": "2026-02-04T14:55:00Z",
      "type": "approval_gate",
      "phase": 3,
      "decision": "approved",
      "details": null
    },
    {
      "timestamp": "2026-02-04T15:35:00Z",
      "type": "statistical_concern",
      "concern_id": 1,
      "document": "chapter1/analysis1_2_normalization.md",
      "decision": "accepted",
      "details": "Added Benjamini-Hochberg correction"
    },
    {
      "timestamp": "2026-02-04T15:36:30Z",
      "type": "statistical_concern",
      "concern_id": 2,
      "document": "chapter2/analysis2_1_differential-expression.md",
      "decision": "rejected",
      "details": "User confirmed data is normally distributed"
    }
  ]
}
```

### Output Provenance

Each output file includes provenance metadata:

```markdown
<!-- Provenance -->
<!-- Generated by: scientific-analysis-architect v2.0.0 -->
<!-- Session: session-20260204-143022-12345 -->
<!-- Phase: 1 -->
<!-- Agent: research-architect -->
<!-- Timestamp: 2026-02-04T14:36:00Z -->
```

---

## Session Cleanup

### Automatic Cleanup

Sessions older than 72 hours are archived on next skill invocation:

```python
def cleanup_old_sessions():
    """Archive or delete old sessions."""

    cutoff = datetime.now() - timedelta(hours=72)

    for session_dir in find_all_sessions():
        state = load_session_state(session_dir)

        if state["last_updated"] < cutoff:
            if state["status"] == "completed":
                # Completed sessions: delete session dir, keep outputs
                shutil.rmtree(session_dir)
            else:
                # Incomplete sessions: archive
                archive_path = f"{session_dir}.archive"
                shutil.move(session_dir, archive_path)
                print(f"[CLEANUP] Archived old session: {archive_path}")
```

### Manual Cleanup

User can request cleanup:

```
Would you like to clean up old sessions?
Found:
- session-20260201-... (completed, 3 days old)
- session-20260202-... (interrupted, 2 days old)

Delete completed, archive interrupted? [yes/no]
```
