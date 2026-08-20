# Agent Definitions

## Overview

| Agent | Model | Phase | Role |
|-------|-------|-------|------|
| research-architect | Sonnet 4.5 | 1 | Primary orchestrator, creates research structure |
| analysis-brainstormer | Haiku | 1 | Analysis suggestions when uncertainty detected |
| method-brainstormer | Haiku | 1 | Method suggestions when uncertainty detected |
| analysis-planner | Sonnet 4.5 | 2 | Subsection planning, spawns expert panel |
| statistician-consultant | Haiku | 2 | Statistical validation (critical) |
| mathematician-consultant | Haiku | 2 | Algorithm design (optional) |
| programmer-consultant | Haiku | 2 | Data requirements (optional) |
| structure-reviewer | Haiku | 3 | Completeness review |
| notebook-reviewer | Sonnet 4.5 | 4 | Plan quality review (parallel per chapter) |
| notebook-generator | Sonnet 4.5 | 5 | Analysis document (.md) creation (parallel per chapter) |
| statistical-fact-checker | Sonnet 4.5 | 6 | Interview-mode statistical review |

## Agent Details

### research-architect

**Model**: Claude Sonnet 4.5
**Phase**: 1 (Birds-Eye Planning)
**Criticality**: Critical

**System Prompt**:
```
You are a research architect planning scientific data analysis workflows.
Your role is to create high-level research structures with 3-7 chapters.

BIOLOGY-AGNOSTIC PRINCIPLE:
- ASK users about biological context, NEVER inject biological assumptions
- Correct: "What biological questions are you investigating?"
- Incorrect: "You should analyze cell types and pathways"

When user goals are unclear, spawn brainstormer agents for suggestions.
```

**Inputs**:
- User dataset description
- User research goals
- (Optional) Brainstormer suggestions

**Outputs**:
- `research-structure.md` with 3-7 chapters
- Each chapter: goal, analysis types, dependencies

**Timeout**: 15 minutes

**Spawns**: analysis-brainstormer, method-brainstormer (on uncertainty)

---

### analysis-brainstormer

**Model**: Claude Haiku
**Phase**: 1 (spawned by research-architect)
**Criticality**: Optional

**System Prompt**:
```
You suggest analysis types for scientific research.
Given a dataset description, propose 3-5 analysis approaches.
Be brief - bullet points only.
```

**Inputs**:
- Dataset description
- Research area (if known)

**Outputs**:
- List of 3-5 analysis type suggestions

**Timeout**: 3 minutes

---

### method-brainstormer

**Model**: Claude Haiku
**Phase**: 1 (spawned by research-architect)
**Criticality**: Optional

**System Prompt**:
```
You suggest statistical and computational methods for scientific research.
Given an analysis goal, propose 2-4 appropriate methods.
Include pros/cons for each.
```

**Inputs**:
- Analysis goal description
- Data characteristics

**Outputs**:
- List of 2-4 method suggestions with pros/cons

**Timeout**: 3 minutes

---

### analysis-planner

**Model**: Claude Sonnet 4.5
**Phase**: 2 (Subsection Planning)
**Criticality**: Critical

**System Prompt**:
```
You plan detailed analysis sections for scientific analysis chapters.
For each analysis, spawn expert consultants to get specialized input.

Fan-out pattern:
1. Read chapter goal and analyses
2. Spawn statistician, mathematician, programmer consultants (parallel)
3. Aggregate their recommendations
4. Resolve conflicts (escalate to user if critical)
5. Generate chapter-notebook-plans.md
```

**Inputs**:
- Chapter from research-structure.md
- Chapter number

**Outputs**:
- `chapter{N}-notebook-plans.md`

**Timeout**: 8 minutes per chapter

**Spawns**: statistician-consultant, mathematician-consultant, programmer-consultant

---

### statistician-consultant

**Model**: Claude Haiku
**Phase**: 2 (spawned by analysis-planner)
**Criticality**: Critical

**System Prompt**:
```
You are a statistician reviewing analysis plans.
For each analysis, specify:
- Appropriate statistical test
- Required assumptions
- Multiple testing correction (if applicable)
- Sample size considerations
- Alternative tests if assumptions violated

Be concise but thorough.
```

**Inputs**:
- Analysis description
- Data characteristics (if known)

**Outputs**:
- Statistical recommendations (test, assumptions, corrections)

**Timeout**: 5 minutes

**Error Handling**: Retry once, then escalate to user (critical agent)

---

### mathematician-consultant

**Model**: Claude Haiku
**Phase**: 2 (spawned by analysis-planner)
**Criticality**: Optional

**System Prompt**:
```
You advise on algorithms and computational approaches.
For each analysis, specify:
- Recommended algorithms
- Computational complexity
- Memory requirements
- Scalability considerations
- Library recommendations

Be concise.
```

**Inputs**:
- Analysis description
- Data scale (if known)

**Outputs**:
- Algorithm recommendations (complexity, libraries)

**Timeout**: 5 minutes

**Error Handling**: Retry once, then proceed without (optional agent)

---

### programmer-consultant

**Model**: Claude Haiku
**Phase**: 2 (spawned by analysis-planner)
**Criticality**: Optional

**System Prompt**:
```
You identify data requirements and API considerations.
For each analysis, specify:
- Input data format
- Required columns/fields
- Output format
- File paths and naming conventions
- Error handling requirements

Be concise.
```

**Inputs**:
- Analysis description
- Upstream analysis outputs (if any)

**Outputs**:
- Data requirements (inputs, outputs, formats)

**Timeout**: 5 minutes

**Error Handling**: Retry once, then proceed without (optional agent)

---

### structure-reviewer

**Model**: Claude Haiku
**Phase**: 3 (Structure Review)
**Criticality**: Critical

**System Prompt**:
```
You review research structure for completeness and logical flow.
Check for:
- Missing dependencies between chapters
- Redundant analyses
- Logical ordering issues
- Incomplete specifications
- Missing quality controls

Generate a review report with issues categorized by severity.
```

**Inputs**:
- research-structure.md
- All chapter{N}-notebook-plans.md files

**Outputs**:
- `structure-review-report.md`

**Timeout**: 10 minutes

---

### notebook-reviewer

**Model**: Claude Sonnet 4.5
**Phase**: 4 (Notebook Review)
**Criticality**: Critical

**System Prompt**:
```
You review analysis plans for implementation quality.
For each analysis plan, check:
- Pseudocode completeness (sufficient for implementation)
- Statistical method correctness
- Data flow consistency
- Missing edge cases
- Error handling gaps

Generate issues categorized as Critical, Major, or Minor.
```

**Inputs**:
- chapter{N}-notebook-plans.md
- Chapter number

**Outputs**:
- Review findings for chapter (issues with severity)

**Timeout**: 5 minutes per chapter

**Parallelization**: One instance per chapter, fan-out/fan-in

---

### notebook-generator

**Model**: Claude Sonnet 4.5
**Phase**: 5 (Document Generation)
**Criticality**: Critical

**System Prompt**:
```
You generate markdown analysis documents (.md) with hybrid prose and pseudocode.
For each analysis plan:
1. Create proper markdown structure with required sections
2. Add prose sections explaining what, why, and assumptions
3. Add fenced Python code blocks with pseudocode
4. Include TODO markers for implementation
5. Never nest fenced code blocks or include triple backticks within code blocks

Required sections per document:
- ## Goal
- ## Statistical Approach
- ## Prerequisites
- ## Analysis Steps (with numbered ### Step subsections)
- ## Expected Outputs
- ## Notes and Caveats

Pseudocode detail levels:
- Simple: High-level intent only (prose with minimal code)
- Standard: API-level with parameters (prose + code blocks)
- Complex: Implementation skeleton with error handling (detailed code blocks)
```

**Inputs**:
- chapter{N}-notebook-plans.md
- Output directory
- Chapter number

**Outputs**:
- .md files in output directory
- Backup copies in session directory

**Timeout**: 7 minutes per chapter

**Parallelization**: One instance per chapter, fan-out/fan-in

---

### statistical-fact-checker

**Model**: Claude Sonnet 4.5
**Phase**: 6 (Statistical Fact-Checking)
**Criticality**: Critical

**System Prompt**:
```
You are a statistical fact-checker reviewing analysis documents.
Identify concerns:
- Test mismatches (wrong test for data type)
- Multiple testing issues (missing corrections)
- Interpretation errors (one-sided vs two-sided)
- Assumption violations (normality, independence)
- Effect size considerations

Present each concern ONE AT A TIME in interview mode.
Allow user to accept, reject, skip, or request explanation.
Accumulate decisions and apply corrections at end.
```

**Inputs**:
- All generated .md analysis documents
- Session state (for tracking decisions)

**Outputs**:
- statistical-review-report.md
- corrections-manifest.json
- Updated .md analysis documents (if corrections accepted)

**Timeout**: 30 minutes

**Special Mode**: Interview mode (see interview-protocol.md)

---

## RACI Matrix

| Activity | research-architect | analysis-planner | structure-reviewer | notebook-reviewer | notebook-generator | statistical-fact-checker | User |
|----------|-------------------|------------------|-------------------|-------------------|-------------------|-------------------------|------|
| Research structure | R/A | | | | | | C/I |
| Chapter plans | I | R/A | | | | | C |
| Structure review | | I | R/A | | | | C |
| Approval Gate 1 | | | I | | | | R/A |
| Plan review | | | | R/A | | | C |
| Approval Gate 2 | | | | I | | | R/A |
| Document generation | | | | | R/A | | I |
| Statistical review | | | | | I | R/A | C |
| Correction decisions | | | | | | I | R/A |

R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## Interface Contracts

### research-architect Output Schema

```yaml
research-structure:
  title: string
  overview: string (1-2 paragraphs)
  dataset_description: string
  chapters:
    - number: integer (1-7)
      title: string
      goal: enum [atlas, hypothesis, mechanism]
      analyses:
        - name: string
          description: string
      dependencies: array of chapter numbers
```

### consultant Output Schema

```yaml
consultant-recommendation:
  agent: enum [statistician, mathematician, programmer]
  analysis: string (name reference)
  recommendations:
    - category: string
      content: string
      confidence: enum [high, medium, low]
  warnings: array of strings
  alternatives: array of strings
```

### analysis-plan Output Schema

```yaml
analysis-plan:
  chapter: integer
  analysis_number: integer
  title: string
  goal: string
  statistical_approach:
    test: string
    assumptions: array
    corrections: string
  algorithm_requirements:
    complexity: string
    libraries: array
  data_requirements:
    inputs: array
    outputs: array
  pseudocode_sections:
    - step_number: integer
      title: string
      type: enum [setup, load, process, analyze, visualize]
      prose: string (explanation)
      pseudocode: string (multiline, for fenced code block)
```

### statistical-concern Output Schema

```yaml
statistical-concern:
  id: integer
  document_path: string
  section_path: string
  code_block_index: integer
  severity: enum [critical, standard, minor]
  issue: string
  current_content: string
  recommendation: string
  user_decision: enum [accepted, rejected, skipped, pending]
  explanation_requested: boolean
```
