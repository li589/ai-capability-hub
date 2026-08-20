# Example: RNA-seq Analysis Plan

Complete walkthrough of the scientific-analysis-architect workflow for a single-cell RNA-seq project.

## Initial Request

User invokes the skill:

```
/scientific-analysis-architect

I have single-cell RNA-seq data from mouse brain tissue. I want to identify
cell types and find differentially expressed genes between conditions to
understand aging effects.
```

## Phase 0: Initialization

**Duration**: 1 minute

### Session Setup

```
Creating session directory...
  Primary location: /Users/researcher/projects/aging-brain/.scientific-analysis-session/
  Session ID: session-20260204-143022-12345

Validating output directory...
  Path: /Users/researcher/projects/aging-brain/
  Writable: Yes

Session initialized.
```

### Quality Gate 0: PASSED

---

## Phase 1: Birds-Eye Planning

**Duration**: 10 minutes

### User Interaction

```
Please describe your dataset and research goals in more detail.

Include:
- Data type and technology (10X, Smart-seq, etc.)
- Sample size and conditions
- Main research questions

User: I have 10X Genomics data from mouse brain. 50,000 cells across 4
conditions: wild-type young, wild-type old, mutant young, mutant old.
I want to understand how aging affects gene expression differently in
the mutant vs wild-type.
```

### Uncertainty Check

No high uncertainty detected (user provided clear goals).

### Generated research-structure.md

```markdown
# Research Structure: Aging Effects in Mouse Brain scRNA-seq

## Overview
This project analyzes single-cell RNA-seq data from mouse brain tissue to
understand how aging affects gene expression, with particular focus on
differences between wild-type and mutant conditions. The analysis will
identify cell types, compare gene expression across conditions, and explore
biological mechanisms underlying aging-related changes.

## Dataset Description
- Technology: 10X Genomics
- Cells: ~50,000
- Conditions: 4 (WT-young, WT-old, MUT-young, MUT-old)
- Tissue: Mouse brain

## Chapters

### Chapter 1: Data Atlas
**Goal**: atlas
**Analyses**:
1. Quality control and filtering
2. Normalization and batch correction
3. Dimensionality reduction (PCA, UMAP)
4. Cell type clustering and annotation
**Dependencies**: None

### Chapter 2: Aging Effects in Wild-Type
**Goal**: hypothesis
**Analyses**:
1. Differential expression: WT-old vs WT-young
2. Gene set enrichment analysis
3. Cell type proportion changes with aging
**Dependencies**: Chapter 1

### Chapter 3: Aging Effects in Mutant
**Goal**: hypothesis
**Analyses**:
1. Differential expression: MUT-old vs MUT-young
2. Gene set enrichment analysis
3. Comparison with WT aging signature
**Dependencies**: Chapter 1, Chapter 2

### Chapter 4: Genotype x Aging Interaction
**Goal**: mechanism
**Analyses**:
1. Interaction analysis (genotype x age)
2. Pathway analysis of interaction genes
3. Cell type-specific interaction effects
**Dependencies**: Chapter 1, Chapter 2, Chapter 3
```

### Quality Gate 1: PASSED

- 4 chapters (within 3-7 range)
- All chapters have goals and analyses
- Dependencies are valid (no circular)

---

## Phase 2: Subsection Planning

**Duration**: 14 minutes (4 chapters)

### Chapter 1 Consultant Fan-Out

**statistician-consultant** (3 min):
```
For Quality Control:
- Use MAD-based outlier detection for QC metrics
- Recommended thresholds: genes/cell, UMIs/cell, %mito
- No multiple testing needed (filtering, not testing)

For Clustering:
- Leiden algorithm recommended (better than Louvain for resolution)
- Use silhouette score to evaluate cluster quality
- Consider multiple resolutions, report stability
```

**mathematician-consultant** (2 min):
```
For Dimensionality Reduction:
- PCA: Keep components explaining 90% variance (typically 30-50)
- UMAP: n_neighbors=15, min_dist=0.1 for balanced local/global

For Batch Correction:
- Harmony recommended for speed: O(n*k) where k=batches
- Alternative: scVI if strong batch effects (GPU required)
```

**programmer-consultant** (2 min):
```
Data Requirements:
- Input: raw_counts.h5ad (AnnData format)
- Intermediate: adata_qc.h5ad, adata_normalized.h5ad
- Output: adata_annotated.h5ad with cluster labels

Libraries: scanpy, harmonypy, matplotlib, seaborn
```

### Generated chapter1-notebook-plans.md (excerpt)

```markdown
# Chapter 1: Data Atlas - Notebook Plans

## Notebook 1.1: Quality Control

### Goal
Filter low-quality cells and genes to ensure reliable downstream analysis.

### Statistical Approach
- MAD-based outlier detection for adaptive thresholds
- Thresholds: 3 MAD from median for each QC metric
- Metrics: n_genes, total_counts, pct_mito

### Algorithm Requirements
- Complexity: O(n_cells) for QC metrics
- No specialized algorithms

### Data Requirements
- Input: raw_counts.h5ad
- Output: adata_qc.h5ad, qc_report.pdf

### Pseudocode
```python
# Cell 1: Load data
# sc.read_h5ad("raw_counts.h5ad")
# Expected: (50000, ~20000) cells x genes

# Cell 2: Calculate QC metrics
# sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)

# Cell 3: Visualize QC distributions
# Plot: n_genes, total_counts, pct_mito distributions by sample

# Cell 4: Apply MAD-based filtering
# For each metric:
#   median = np.median(values)
#   mad = np.median(np.abs(values - median))
#   lower = median - 3*mad
#   upper = median + 3*mad
#   filter cells outside range

# Cell 5: Report filtering results
# Print: cells before/after, genes before/after
```

## Notebook 1.2: Normalization

### Goal
Remove technical variation while preserving biological signal.

### Statistical Approach
- Total count normalization to 10,000 per cell
- Log1p transformation for variance stabilization
- Highly variable gene selection: top 2000 by dispersion

### Data Requirements
- Input: adata_qc.h5ad
- Output: adata_normalized.h5ad

### Pseudocode
```python
# Cell 1: Normalize counts
# sc.pp.normalize_total(adata, target_sum=1e4)
# sc.pp.log1p(adata)

# Cell 2: Identify highly variable genes
# sc.pp.highly_variable_genes(adata, n_top_genes=2000)
# Plot: mean vs dispersion

# Cell 3: Save raw counts in layer
# adata.layers['raw'] = adata.X.copy()
```

...
```

### Chapters 2-4

Similar consultant fan-out and analysis plan generation for remaining chapters.

### Quality Gate 2: PASSED

- All 4 chapter plans generated
- Each analysis has statistical approach
- No unresolved conflicts

---

## Phase 3: Structure Review

**Duration**: 4 minutes

### structure-review-report.md

```markdown
# Structure Review Report

## Summary
- Chapters: 4
- Total analyses: 11
- Issues identified: 3 (0 critical, 2 major, 1 minor)

## Issues

### Major Issues

**M1: Missing batch correction validation**
Location: Chapter 1, Notebook 1.3
Issue: Batch correction applied but no validation step
Recommendation: Add UMAP colored by batch before/after correction

**M2: No power analysis for DE**
Location: Chapter 2, Notebook 2.1
Issue: Sample sizes not mentioned in DE analysis
Recommendation: Add cell count per condition check, mention statistical power

### Minor Issues

**m1: Redundant GSEA**
Location: Chapter 2 and 3
Issue: GSEA run separately, could be combined
Recommendation: Consider consolidating in Chapter 4

## Overall Assessment
Structure is sound. Major issues addressable without restructuring.
```

### USER APPROVAL GATE 1

```
Structure Review Complete

Summary:
- 4 chapters planned
- 11 analyses total
- 3 issues identified (0 critical, 2 major, 1 minor)

Major Issues:
1. Missing batch correction validation (Chapter 1)
2. No power analysis for DE (Chapter 2)

Approve / Request changes / Reject? [A/c/r]
```

**User enters**: A (Approve)

```
Structure approved. Proceeding to plan review.
```

---

## Phase 4: Plan Review

**Duration**: 8 minutes (parallel)

### notebook-review-report.md (excerpt)

```markdown
# Notebook Review Report

## Chapter 1: Data Atlas
- Notebooks: 4
- Issues: 2

Issues:
1. [Major] Notebook 1.1: Missing mitochondrial gene pattern specification
   - Current: qc_vars=['mt']
   - Should specify: pattern="^mt-" for mouse

2. [Minor] Notebook 1.4: Cluster annotation could use marker genes

## Chapter 2: Aging Effects in Wild-Type
- Notebooks: 3
- Issues: 1

Issues:
1. [Standard] Notebook 2.1: Should specify Wilcoxon vs t-test choice rationale

...
```

### USER APPROVAL GATE 2

```
Notebook Review Complete

Per-Chapter Summary:
- Chapter 1: 4 analyses, 2 issues
- Chapter 2: 3 analyses, 1 issue
- Chapter 3: 2 analyses, 1 issue
- Chapter 4: 2 analyses, 0 issues

Critical Issues: None

Approve / Request changes / Reject? [A/c/r]
```

**User enters**: A

---

## Phase 5: Document Generation

**Duration**: 8 minutes (Step 1: overview + Step 2: parallel generation)

### Step 1: Master Strategy Overview

```
Generating master strategy overview...
  Reading research-structure.md and 4 chapter plans...
  Writing analysis-strategy-overview.md ... OK
```

### Step 2: Generated Analysis Documents

```
Generating analysis documents...

Chapter 1:
  analysis1_1_quality-control.md ... OK
  analysis1_2_normalization.md ... OK
  analysis1_3_batch-correction.md ... OK
  analysis1_4_clustering.md ... OK

Chapter 2:
  analysis2_1_de-wt-aging.md ... OK
  analysis2_2_gsea-wt.md ... OK
  analysis2_3_composition-wt.md ... OK

Chapter 3:
  analysis3_1_de-mut-aging.md ... OK
  analysis3_2_gsea-mut.md ... OK

Chapter 4:
  analysis4_1_interaction-analysis.md ... OK
  analysis4_2_pathway-interaction.md ... OK

Validating analysis documents...
  All 11 documents have required sections and valid structure.
  Master strategy overview validated.

Copying to session directory...
  Backup complete.
```

### Quality Gate 5: PASSED

- 11/11 analysis documents generated
- All have required sections (Goal, Statistical Approach, Analysis Steps, Expected Outputs)
- Master strategy overview present with required sections
- Backups created

---

## Phase 6: Statistical Fact-Checking

**Duration**: 12 minutes

### Interview Session

**Concern 1 of 4**:

```
Statistical Concern 1 of 4

Document: chapter2_aging-wt/analysis2_1_de-wt-aging.md
Section: Analysis Steps > Step 3: Run Differential Expression
Code Block: 0
Severity: Critical

Issue: Multiple testing correction method not specified

Current pseudocode:
```python
# Run differential expression
# sc.tl.rank_genes_groups(adata, groupby='age', groups=['old'], reference='young')
# Filter: pvals_adj < 0.05
```

Concern: rank_genes_groups uses Benjamini-Hochberg by default, but this should
be explicit. Also, with ~20,000 genes, consider whether FDR 0.05 is appropriate
or if stricter threshold needed.

Recommendation:
```python
# Run differential expression with explicit correction
# sc.tl.rank_genes_groups(
#     adata,
#     groupby='age',
#     groups=['old'],
#     reference='young',
#     method='wilcoxon',
#     corr_method='benjamini-hochberg'  # Explicit
# )
# Note: FDR 0.05 used; for exploratory analysis, consider 0.1
# Filter: pvals_adj < 0.05 AND |log2FC| > 0.5
```

Accept? [yes/no/skip/explain]
```

**User**: yes

```
Correction accepted. (3 remaining)
```

**Concern 2 of 4**:

```
Statistical Concern 2 of 4

Document: chapter4_interaction/analysis4_1_interaction-analysis.md
Section: Analysis Steps > Step 2: Interaction Model
Code Block: 0
Severity: Critical

Issue: Interaction test methodology unclear

Current pseudocode:
```python
# Test genotype x age interaction
# For each gene:
#   model: expression ~ genotype + age + genotype:age
#   test interaction term
```

Concern: Linear model assumes normal residuals. Single-cell data is typically
zero-inflated and non-normal. Consider appropriate model.

Recommendation:
```python
# Test genotype x age interaction
# Option 1: Pseudobulk approach (recommended for interaction)
#   Aggregate cells by sample -> bulk-like data
#   Use DESeq2/edgeR with interaction term
#
# Option 2: Mixed model (if keeping single-cell resolution)
#   Account for cell-level variation within samples
#   Library: statsmodels MixedLM or lme4 (R)
#
# Note: Pseudobulk recommended for 4-condition design
```

Accept? [yes/no/skip/explain]
```

**User**: explain

```
Extended Explanation:

Statistical Background:
Single-cell RNA-seq data violates linear model assumptions:
1. Zero-inflation: Many genes have 0 counts in most cells
2. Non-normal: Count data follows negative binomial, not normal
3. Heteroscedasticity: Variance depends on mean

For interaction tests, these violations can cause:
- Inflated false positives
- Reduced power
- Unreliable p-values

Why Pseudobulk Works:
1. Aggregating cells per sample averages out zeros
2. Central limit theorem: aggregates approach normality
3. Reduces to well-understood bulk RNA-seq statistics
4. Published benchmarks show pseudobulk outperforms single-cell methods for DE

For your design (2 genotypes x 2 ages), pseudobulk gives:
- 4 conditions with biological replicates
- Well-powered interaction test
- Established statistical framework

Alternative Approaches:
1. MAST: Zero-inflated regression for single-cell
2. Mixed models: Account for cell-level variation
3. Permutation tests: Non-parametric but computationally expensive

References:
- Squair et al. 2021: Pseudobulk benchmark
- Zimmerman et al. 2021: Interaction testing in scRNA-seq

Accept? [yes/no/skip]
```

**User**: yes

```
Correction accepted. (2 remaining)
```

**Concern 3 of 4** and **Concern 4 of 4**: User accepts both.

### Interview Summary

```
Interview Complete

Summary:
- 4 corrections accepted
- 0 corrections rejected
- 0 corrections skipped

Accepted corrections:
1. [Critical] Explicit multiple testing in DE (analysis 2.1)
2. [Critical] Pseudobulk for interaction test (analysis 4.1)
3. [Standard] Add effect size filter to DE (analysis 2.1)
4. [Standard] Clarify clustering resolution selection (analysis 1.4)

Apply all accepted corrections now? [yes/no]
```

**User**: yes

```
Applying corrections...
  analysis2_1_de-wt-aging.md ... updated
  analysis4_1_interaction-analysis.md ... updated
  analysis1_4_clustering.md ... updated

Refreshing master strategy overview...
  analysis-strategy-overview.md ... updated

Validating updated documents...
  All analysis documents pass validation.

Statistical review complete.
```

### Quality Gate 6: PASSED

---

## Final Output Summary

```
Workflow Complete

Session: session-20260204-143022-12345
Duration: 52 minutes

Generated Files:
  /Users/researcher/projects/aging-brain/
  +-- analysis-strategy-overview.md
  +-- chapter1_data-atlas/
  |   +-- analysis1_1_quality-control.md
  |   +-- analysis1_2_normalization.md
  |   +-- analysis1_3_batch-correction.md
  |   +-- analysis1_4_clustering.md
  +-- chapter2_aging-wt/
  |   +-- analysis2_1_de-wt-aging.md (corrected)
  |   +-- analysis2_2_gsea-wt.md
  |   +-- analysis2_3_composition-wt.md
  +-- chapter3_aging-mut/
  |   +-- analysis3_1_de-mut-aging.md
  |   +-- analysis3_2_gsea-mut.md
  +-- chapter4_interaction/
      +-- analysis4_1_interaction-analysis.md (corrected)
      +-- analysis4_2_pathway-interaction.md

Session artifacts saved to:
  .scientific-analysis-session/

Next steps:
1. Review analysis-strategy-overview.md for the full plan
2. Review individual analysis documents
3. Implement pseudocode from each .md file
4. Run analyses in order (Chapter 1 -> 2 -> 3 -> 4)
5. Consider using programming-pm for implementation assistance (provide .md files as input)
```
