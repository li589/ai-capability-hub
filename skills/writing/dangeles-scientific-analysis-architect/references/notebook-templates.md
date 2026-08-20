# Analysis Document Templates

Templates and guidelines for generating markdown analysis documents with pseudocode.

## Detail Levels

### Simple (High-Level Intent)

Use for exploratory analyses where implementation details are flexible.

```markdown
# Quality Control

## Goal
Filter low-quality cells and genes to ensure reliable downstream analysis.

## Statistical Approach
MAD-based outlier detection for adaptive QC thresholds.

## Prerequisites
- Input: raw_counts.h5ad
- Libraries: scanpy

## Analysis Steps

### Step 1: Load Data
Load the AnnData object containing single-cell RNA-seq data.

```python
# sc.read_h5ad("raw_counts.h5ad")
# Expected: (50000, ~20000) cells x genes
```

### Step 2: Quality Control
Filter cells and genes based on standard QC metrics.

```python
# Calculate QC metrics and filter
# sc.pp.calculate_qc_metrics(adata, inplace=True)
# Filter cells by gene count and mitochondrial fraction
```

### Step 3: Visualization
Create QC diagnostic plots.

```python
# Plot QC metric distributions
# Save to figures directory
```

## Expected Outputs
- adata_qc.h5ad: Filtered AnnData object
- qc_report figures

## Notes and Caveats
- Thresholds may need dataset-specific tuning
```

**Characteristics:**
- Brief prose sections
- One fenced code block per step with one-line comments
- No specific function parameters
- Suitable for: brainstorming, early planning

### Standard (API-Level)

Use for defined analyses where methods are chosen but parameters need tuning.

```markdown
# Quality Control

## Goal
Filter low-quality cells and genes to ensure reliable downstream analysis.

## Statistical Approach
- MAD-based outlier detection for adaptive thresholds
- Thresholds: 3 MAD from median for each QC metric
- Metrics: n_genes, total_counts, pct_mito

## Prerequisites
- Input: raw_counts.h5ad (AnnData format)
- Libraries: scanpy, matplotlib, numpy
- No upstream dependencies (first analysis)

## Analysis Steps

### Step 1: Load Data
Load the raw count matrix and verify expected dimensions.

```python
# TODO: Load AnnData from file
# Function: sc.read_h5ad(path)
# Expected input: "{data_dir}/raw_counts.h5ad"
# Expected shape: (n_cells, n_genes) approximately (50000, 20000)
```

### Step 2: Calculate QC Metrics
Compute per-cell quality metrics for filtering decisions.

```python
# TODO: Calculate QC metrics
# sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)
#
# Metrics added to adata.obs:
#   - n_genes_by_counts
#   - total_counts
#   - pct_counts_mt
```

### Step 3: Visualize QC Distributions
Plot distributions of QC metrics to inform threshold selection.

```python
# TODO: Create QC diagnostic plots
# Plot: n_genes, total_counts, pct_mito distributions by sample
# Add threshold lines at 3 MAD from median
# Save to: {output_dir}/figures/qc_distributions.png
```

### Step 4: Apply MAD-Based Filtering
Filter cells using adaptive thresholds based on median absolute deviation.

```python
# TODO: Apply MAD-based filtering
# For each metric:
#   median = np.median(values)
#   mad = np.median(np.abs(values - median))
#   lower = median - 3*mad
#   upper = median + 3*mad
#   filter cells outside range
#
# sc.pp.filter_cells(adata, min_genes=200)
# sc.pp.filter_cells(adata, max_genes=5000)
# sc.pp.filter_genes(adata, min_cells=3)
```

### Step 5: Report Filtering Results
Summarize cell and gene counts before and after filtering.

```python
# TODO: Report filtering results
# Print: cells before/after, genes before/after
# Validate: sufficient cells remain (>= 100)
# Save: adata_qc.h5ad
```

## Expected Outputs
- adata_qc.h5ad: Filtered AnnData object
- qc_distributions.png: QC metric distributions
- Console: filtering summary statistics

## Notes and Caveats
- MAD thresholds assume roughly symmetric distributions
- Mitochondrial gene patterns are species-specific (mouse: ^mt-, human: ^MT-)
- Consider sample-specific thresholds if batch effects are strong
```

**Characteristics:**
- Detailed prose explaining what and why for each step
- Fenced code blocks with specific function calls and parameters
- Expected inputs/outputs documented per step
- Suitable for: implementation-ready plans

### Complex (Implementation Skeleton)

Use for critical analyses requiring error handling and validation.

```markdown
# Differential Expression Analysis

## Goal
Identify differentially expressed genes between conditions with proper statistical controls.

## Statistical Approach
- Test: Wilcoxon rank-sum (non-parametric, appropriate for scRNA-seq)
- Multiple testing: Benjamini-Hochberg FDR correction (alpha=0.05)
- Effect size: log2 fold-change threshold of 0.5
- Rationale: Non-parametric test avoids normality assumption violated by count data

## Prerequisites
- Input: adata_normalized.h5ad (from Normalization analysis)
- Libraries: scanpy, pandas, numpy, statsmodels
- Upstream: Quality Control and Normalization must complete first

## Analysis Steps

### Step 1: Setup and Configuration
Configure analysis parameters and validate input data.

```python
# TODO: Import libraries and set configuration
#
# Required imports:
#   import scanpy as sc
#   import pandas as pd
#   import numpy as np
#   from statsmodels.stats.multitest import multipletests
#
# Parameters (adjust as needed):
#   ALPHA = 0.05
#   LOG2FC_THRESHOLD = 0.5
#   MIN_CELLS_PER_GROUP = 10
#
# Validation:
#   assert 'condition' in adata.obs.columns
#   assert adata.obs['condition'].nunique() >= 2
```

### Step 2: Load and Validate Data
Load normalized data with validation checks.

```python
# TODO: Load data with validation
#
# def load_and_validate(path: str) -> sc.AnnData:
#     # Load: sc.read_h5ad(path)
#     # Check: file exists, n_obs > 0, n_vars > 0
#     # Check: required columns in obs
#     # Check: min cells per group >= MIN_CELLS_PER_GROUP
#     # Log: data dimensions, conditions, cell counts per group
#     # Return: validated AnnData
#
# adata = load_and_validate("{data_dir}/adata_normalized.h5ad")
```

### Step 3: Run Differential Expression
Execute DE analysis with explicit statistical parameters.

```python
# TODO: Run DE analysis
#
# sc.tl.rank_genes_groups(
#     adata,
#     groupby='condition',
#     groups=['treatment'],
#     reference='control',
#     method='wilcoxon',
#     corr_method='benjamini-hochberg'
# )
#
# result = sc.get.rank_genes_groups_df(adata, group='treatment')
#
# # Apply additional BH correction (verification)
# _, result['pvals_adj_bh'], _, _ = multipletests(
#     result['pvals'],
#     method='fdr_bh',
#     alpha=ALPHA
# )
```

### Step 4: Filter Significant Results
Apply significance and effect size thresholds.

```python
# TODO: Filter significant genes
#
# significant = result[
#     (result['pvals_adj_bh'] < ALPHA) &
#     (abs(result['logfoldchanges']) > LOG2FC_THRESHOLD)
# ]
#
# # Report results
# print(f"Total genes tested: {len(result)}")
# print(f"Significant (FDR<{ALPHA}, |log2FC|>{LOG2FC_THRESHOLD}): {len(significant)}")
# print(f"Up-regulated: {(significant['logfoldchanges'] > 0).sum()}")
# print(f"Down-regulated: {(significant['logfoldchanges'] < 0).sum()}")
#
# # Validate: not suspiciously many or few
# pct_sig = len(significant) / len(result) * 100
# if pct_sig > 50:
#     print(f"WARNING: {pct_sig:.1f}% genes significant -- check for batch effects")
# if pct_sig == 0:
#     print("WARNING: No significant genes -- check sample sizes and conditions")
```

### Step 5: Save Results
Export results with provenance metadata.

```python
# TODO: Save results
#
# significant.to_csv(f"{output_dir}/de_results.csv", index=False)
# result.to_csv(f"{output_dir}/de_all_genes.csv", index=False)
#
# # Save AnnData with DE results
# adata.write(f"{output_dir}/adata_with_de.h5ad")
```

## Expected Outputs
- de_results.csv: Significant DE genes with statistics
- de_all_genes.csv: Full gene-level results
- adata_with_de.h5ad: AnnData with DE results stored

## Notes and Caveats
- Wilcoxon test may have reduced power compared to parametric alternatives
- FDR correction is per-comparison; consider experiment-wide correction if multiple comparisons
- Log2FC threshold is arbitrary; adjust based on biological significance
- Pseudobulk approach recommended for interaction analyses (see Chapter 4)
```

**Characteristics:**
- Full function definitions with docstrings
- Type hints and validation
- Error handling with assertions and warnings
- Diagnostic output and logging
- Multiple testing correction implemented
- Suitable for: production-ready implementation

## Document Structure

### Standard Analysis Document Layout

```
# Analysis Title

## Goal
## Statistical Approach
## Prerequisites
## Analysis Steps
### Step 1: [Name]
### Step 2: [Name]
...
## Expected Outputs
## Notes and Caveats
```

## Code Block Formatting Rules

1. **Language identifier**: Always use triple backticks with `python` language tag
2. **No nesting**: Never nest fenced code blocks inside other fenced code blocks
3. **Triple-quoted strings**: If pseudocode contains docstrings, use single-quoted triple quotes in comments instead
4. **Multi-line strings**: Use comment notation rather than string literals
5. **Balanced fences**: Every opening ``` must have a closing ```
6. **One block per step**: Each Analysis Step subsection should have at most one fenced code block

## Provenance Metadata

All generated analysis documents include an HTML comment block with provenance:

```markdown
<!-- Generated by: scientific-analysis-architect v2.0.0 -->
<!-- Session: {session_id} -->
<!-- Phase: 5 -->
<!-- Agent: notebook-generator -->
<!-- Timestamp: {iso8601_timestamp} -->
<!-- Chapter: {N}, Analysis: {M} -->
<!-- Detail Level: {simple|standard|complex} -->
```

## Variable Naming

### Conventions

| Type | Convention | Example |
|------|------------|---------|
| Data objects | Descriptive snake_case | `adata_filtered`, `de_results` |
| Parameters | UPPER_SNAKE_CASE | `MIN_GENES`, `N_NEIGHBORS` |
| Functions | verb_noun snake_case | `load_data()`, `run_de_analysis()` |
| Paths | descriptive with suffix | `output_dir`, `data_path` |
| Figures | fig_descriptive | `fig_qc`, `fig_umap` |

### Consistency Rules

1. **Reuse standard names across analysis documents**:
   - `adata` for main AnnData object
   - `results` for analysis output DataFrames
   - `fig, ax` for matplotlib figures

2. **Document data flow** in prose or code comments:
   ```
   Input: adata (raw counts, shape: n_cells x n_genes)
   Output: adata_normalized (log-normalized, same shape)
   ```

3. **Use meaningful intermediate names**:
   ```
   Good: highly_variable_genes = ...
   Avoid: hvg = ...
   ```

## Output File Structure

```
{output_dir}/
+-- analysis-strategy-overview.md
+-- chapter1_data-atlas/
|   +-- analysis1_1_quality-control.md
|   +-- analysis1_2_normalization.md
|   +-- analysis1_3_clustering.md
+-- chapter2_hypothesis-testing/
|   +-- analysis2_1_differential-expression.md
|   +-- analysis2_2_pathway-enrichment.md
+-- chapter3_mechanism-exploration/
    +-- analysis3_1_trajectory-analysis.md
    +-- analysis3_2_gene-regulatory-networks.md
```

### Naming Convention

`analysis{chapter}_{number}_{slug}.md`

- `{chapter}`: Chapter number (1-7)
- `{number}`: Analysis number within chapter (1-N)
- `{slug}`: Kebab-case analysis name

## Validation

All analysis documents must pass structural validation:

```python
import os
import re

REQUIRED_SECTIONS = {
    "goal": [r'^##\s+(Goal|Objective|Goals)\b'],
    "statistical_approach": [r'^##\s+(Statistical Approach|Statistical Method|Methods)\b'],
    "analysis_steps": [r'^##\s+(Analysis Steps|Steps|Workflow Steps)\b'],
    "expected_outputs": [r'^##\s+(Expected Outputs|Outputs|Results)\b']
}

def validate_analysis_document(path: str) -> bool:
    """Validate markdown analysis document structure."""
    with open(path) as f:
        content = f.read()

    # Check required sections
    for section_name, patterns in REQUIRED_SECTIONS.items():
        if not any(re.search(p, content, re.MULTILINE | re.IGNORECASE) for p in patterns):
            return False

    # Check for at least one fenced code block
    if '```' not in content:
        return False

    # Check balanced fences
    if content.count('```') % 2 != 0:
        return False

    return True
```

## Template Selection Logic

```python
def select_detail_level(analysis: dict) -> str:
    """Select appropriate detail level for analysis."""

    # Complex: Critical analyses with statistical rigor requirements
    if analysis.get("statistical_complexity") == "high":
        return "complex"
    if analysis.get("critical_for_conclusions"):
        return "complex"
    if analysis.get("multiple_testing_required"):
        return "complex"

    # Simple: Exploratory or flexible implementation
    if analysis.get("exploratory"):
        return "simple"
    if analysis.get("implementation_flexible"):
        return "simple"

    # Default: Standard
    return "standard"
```

## Master Strategy Overview Template

The master strategy overview is generated as Step 1 of Phase 5, synthesizing approved content from Phases 1-4.

```markdown
# Analysis Strategy Overview: {Project Title}

## Project Objective
{1-2 paragraph summary of the research question and approach}

## Dataset Summary
{Key characteristics: data type, sample size, conditions}

## Strategy at a Glance

| Chapter | Title | Goal | Analyses | Key Method |
|---------|-------|------|----------|------------|
| 1 | ... | atlas | 4 | ... |
| 2 | ... | hypothesis | 3 | ... |
| ... | | | | |

## Chapter Summaries

### Chapter 1: {Title}
{2-4 sentences: what this chapter achieves and why}
- Key analyses: {list}
- Outputs: {what downstream chapters consume}

### Chapter 2: {Title}
...

## Data Flow
{Description of how data moves between chapters}

Chapter 1 (raw data) -> Chapter 2 (normalized + annotated) -> Chapter 3 (DE results) -> ...

## Consolidated Methods

| Analysis Type | Method | Justification |
|--------------|--------|---------------|
| Clustering | Leiden | Better resolution than Louvain |
| DE testing | Wilcoxon | Non-parametric, robust for scRNA-seq |
| ... | | |

## Required Libraries
- scanpy: Single-cell analysis
- pandas: Data manipulation
- ...

## Execution Order
1. Chapter 1 must complete first (provides base data)
2. Chapters 2 and 3 can run in parallel (independent analyses)
3. Chapter 4 requires Chapters 2 and 3 (interaction analysis)

## Assumptions and Limitations
- {List of key assumptions}
- {Known limitations}

## Generated by
scientific-analysis-architect v2.0.0
Session: {session_id}
Date: {date}
```

### Length Guidelines

- Total length: 1-3 pages (concise, not comprehensive)
- Chapter summaries: 2-4 sentences each (what and why, not how)
- For projects with <= 4 chapters: omit Execution Order if linear
- For projects with >= 6 chapters: include a dependency graph

---

## Audience Document Templates (Phase 7)

For audience-targeted documents generated in Phase 7 (researcher narrative plan, architect handoff, engineering translation), see:

[audience-document-templates.md](audience-document-templates.md)

These templates serve different audiences (domain researchers, analysis architects, systems engineers) and are generated from the finalized analysis artifacts after Phase 6 fact-checking.
