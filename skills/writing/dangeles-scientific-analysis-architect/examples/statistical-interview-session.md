# Example: Statistical Interview Session

Examples of Phase 6 statistical fact-checking interview scenarios.

## Scenario 1: Single Concern Accepted

### Concern Presentation

```
Statistical Concern 1 of 1

Document: chapter2_hypothesis/analysis2_1_differential-expression.md
Section: Analysis Steps > Step 3: Compare Expression
Code Block: 0
Severity: Standard

Issue: T-test used for non-normal data

Current:
# Compare expression between groups
# result = scipy.stats.ttest_ind(group1_expr, group2_expr)
# significant = result.pvalue < 0.05

Concern: Gene expression data is typically not normally distributed,
especially in single-cell data. T-test assumes normality and may give
unreliable p-values.

Recommendation:
# Compare expression between groups (non-parametric)
# result = scipy.stats.mannwhitneyu(group1_expr, group2_expr, alternative='two-sided')
# significant = result.pvalue < 0.05
# Note: Mann-Whitney U test (Wilcoxon rank-sum) makes no distributional assumptions

Accept? [yes/no/skip/explain]
```

### User Response

```
User: yes

Correction accepted.

Summary:
- 1 correction accepted
- 0 corrections rejected
- 0 corrections skipped

Apply all accepted corrections now? [yes/no]

User: yes

Applying corrections...
  analysis2_1_differential-expression.md ... updated
  Validation passed.

Statistical review complete.
```

---

## Scenario 2: Concern Rejected (User Domain Knowledge)

### Concern Presentation

```
Statistical Concern 3 of 5

Document: chapter1_atlas/analysis1_2_normalization.md
Section: Analysis Steps > Step 2: Batch Effect Assessment
Code Block: 0
Severity: Standard

Issue: No normality test before parametric analysis

Current:
# Batch effect assessment
# F-statistic = one_way_anova(batch1, batch2, batch3)
# Check if batch explains significant variance

Concern: ANOVA assumes normally distributed residuals. Without testing this
assumption, p-values may be unreliable.

Recommendation:
# Batch effect assessment with assumption checking
#
# Step 1: Test normality of residuals
# stat, p = scipy.stats.shapiro(residuals)
# if p < 0.05: use Kruskal-Wallis instead
#
# Step 2: Apply appropriate test
# if normal:
#   F_stat, p = scipy.stats.f_oneway(batch1, batch2, batch3)
# else:
#   H_stat, p = scipy.stats.kruskal(batch1, batch2, batch3)

Accept? [yes/no/skip/explain]
```

### User Rejection

```
User: no

Briefly explain why (or press Enter to skip):

User: This ANOVA is used for diagnostics only, not hypothesis testing.
We're checking batch effects to decide whether to apply correction, not
making statistical claims. The exact p-value doesn't matter - we just need
a rough estimate of batch contribution.

Noted. (2 remaining)
```

### Final Summary

```
Interview Complete

Summary:
- 3 corrections accepted
- 1 correction rejected
- 1 correction skipped

Rejected corrections:
1. [Standard] Normality test for batch ANOVA (analysis 1.2)
   Reason: "Diagnostic use only, not formal hypothesis test"

...
```

---

## Scenario 3: Batch Mode (Many Concerns)

### Initial Summary

```
Statistical Review Found 15 Concerns

Summary by Severity:
- Critical: 3 (incorrect conclusions possible)
- Standard: 8 (best practice violations)
- Minor: 4 (improvement opportunities)

Summary by Chapter:
- Chapter 1: 4 concerns
- Chapter 2: 5 concerns
- Chapter 3: 3 concerns
- Chapter 4: 3 concerns

How would you like to proceed?

(A) Review all 15 concerns one-by-one
(B) Review only Critical (3) concerns
(C) Accept all Critical, review Standard (8)
(D) Accept all recommended corrections
(E) Skip statistical review (not recommended)

Enter choice [A/B/C/D/E]:
```

### User Chooses Option B

```
User: B

Reviewing 3 Critical concerns...
```

### Critical Concern 1

```
Statistical Concern 1 of 3 (Critical)

Document: chapter2_hypothesis/analysis2_1_de-analysis.md
Section: Analysis Steps > Step 4: Differential Expression
Code Block: 0
Severity: Critical

Issue: No multiple testing correction for 20,000+ tests

...

Accept? [yes/no/skip/explain]

User: yes
```

### After Critical Review

```
Critical review complete.

You reviewed 3 critical concerns:
- 3 accepted
- 0 rejected
- 0 skipped

Remaining concerns (12):
- Standard: 8
- Minor: 4

How would you like to handle remaining concerns?

(A) Review remaining one-by-one
(B) Accept all remaining
(C) Skip all remaining
(D) Accept Standard, skip Minor

Enter choice [A/B/C/D]:

User: D

Accepting 8 Standard corrections...
Skipping 4 Minor concerns...

Summary:
- 11 corrections accepted (3 Critical + 8 Standard)
- 0 corrections rejected
- 4 corrections skipped (Minor)

Apply all accepted corrections now? [yes/no]

User: yes
```

---

## Scenario 4: High Rejection Rate

### After Multiple Rejections

```
[After user rejects 5 of 6 concerns]

High Rejection Rate Detected

You've rejected 5 of 6 concerns (83%).

This may indicate:
- Domain knowledge the fact-checker lacks
- Different statistical philosophy
- Concerns not applicable to your context

Would you like to:
(A) Continue reviewing (your expertise is respected)
(B) Explain your reasoning (helps improve future reviews)
(C) Skip remaining statistical review

Enter choice [A/B/C]:

User: B

Please briefly explain your statistical approach:

User: I'm using a Bayesian framework throughout this analysis. The classical
frequentist concerns about multiple testing and p-values don't apply. I'm
using posterior probabilities with appropriate priors, which naturally
handles multiplicity through shrinkage.

Thank you for the explanation. This context is valuable.

Logging: "User employs Bayesian framework; frequentist corrections not applicable"

Continue with remaining concerns? [yes/skip-all]

User: skip-all

Skipping remaining concerns (user employs Bayesian framework).
```

---

## Scenario 5: Zero Concerns

### Justification Display

```
Statistical Review Complete

No statistical concerns identified.

Justification:
- 8 analysis documents reviewed
- 12 statistical methods examined

Methods validated:
1. Wilcoxon rank-sum test (non-parametric, appropriate for scRNA-seq)
2. Benjamini-Hochberg correction (applied to all multi-test scenarios)
3. Negative binomial regression (appropriate for count data)
4. Permutation test for interaction (non-parametric, valid)

Assumptions verified:
- No parametric tests applied to non-normal data
- Multiple testing corrections present where needed
- Effect sizes reported alongside p-values
- Sample sizes adequate for statistical power

Confidence: High

Proceed to completion? [yes/request-second-review]

User: yes

No corrections needed. Proceeding to completion.
```

---

## Scenario 6: Explanation Request

### Detailed Explanation

```
Statistical Concern 2 of 4

Document: chapter3_mechanism/analysis3_1_trajectory.md
Section: Analysis Steps > Step 4: Gene-Pseudotime Correlation
Code Block: 0
Severity: Standard

Issue: Pseudotime correlation without multiple testing correction

Current:
# Correlate gene expression with pseudotime
# correlations = []
# for gene in genes:
#     r, p = scipy.stats.spearmanr(pseudotime, expression[gene])
#     if p < 0.05:
#         correlations.append((gene, r, p))

Concern: Testing thousands of genes for pseudotime correlation without
correction will yield many false positives.

Recommendation: Apply FDR correction to p-values.

Accept? [yes/no/skip/explain]

User: explain
```

### Extended Explanation

```
Extended Explanation:

Statistical Background:
When testing N hypotheses at significance level alpha, the expected number of
false positives (Type I errors) is N * alpha. For 10,000 genes at alpha=0.05:
- Expected false positives: 500 genes
- These appear significant purely by chance

This is the "multiple testing problem" - making many comparisons inflates
the overall false positive rate.

Why This Matters for Pseudotime:
Pseudotime analysis often identifies trajectory-correlated genes to understand
biological processes. If 500+ genes are false positives:
- Downstream analysis (e.g., GO enrichment) becomes unreliable
- Biological interpretation is misleading
- Reproducibility suffers

Correction Methods:

1. Benjamini-Hochberg (FDR)
   - Controls False Discovery Rate
   - Less conservative than Bonferroni
   - Widely accepted for genomics
   - Implementation: statsmodels.stats.multitest.multipletests(..., method='fdr_bh')

2. Bonferroni
   - Controls Family-Wise Error Rate
   - Very conservative (may miss true positives)
   - Use when false positives are costly

3. Permutation-based FDR
   - Empirical null distribution
   - More accurate for correlated tests
   - Computationally expensive

Recommendation for your case:
BH correction is standard for gene-level testing. With typical scRNA-seq
(10,000-20,000 genes), expect:
- Before correction: ~1000 "significant" genes at p<0.05
- After BH (FDR<0.05): ~100-500 significant genes
- The reduction removes likely false positives

References:
- Benjamini & Hochberg, 1995: Original FDR paper
- Storey & Tibshirani, 2003: q-value approach
- Efron, 2012: Large-scale inference textbook

Accept? [yes/no/skip]

User: yes

Correction accepted. (2 remaining)
```

---

## Scenario 7: Interview Interruption and Resume

### Interruption

```
Statistical Concern 4 of 8

Document: chapter2_hypothesis/analysis2_2_gsea.md
...

Accept? [yes/no/skip/explain]

[User presses Ctrl+C]

Session interrupted.
Saving interview progress...
  Concerns reviewed: 3 of 8
  Decisions: 2 accepted, 1 skipped
  State saved to: session-state.json

Session saved. Resume with: /scientific-analysis-architect
```

### Resume Session

```
/scientific-analysis-architect

Found incomplete session from 2026-02-04 14:30
Project: Aging Effects in Mouse Brain scRNA-seq
Status: Phase 6 (Statistical Fact-Checking)
Completed: Phases 0-5

Resume from Phase 6? [yes/no]

User: yes

Resuming Statistical Review...

Progress: 3 of 8 concerns reviewed
Last concern reviewed: Concern 3 (skipped)

Continue from concern 4? [yes/restart]

User: yes

Statistical Concern 4 of 8

Document: chapter2_hypothesis/analysis2_2_gsea.md
...
```

---

## Summary of User Options

### During Individual Concern Review

| Option | Meaning |
|--------|---------|
| yes | Accept correction, add to apply list |
| no | Reject correction, optionally explain why |
| skip | Defer decision, move to next concern |
| explain | Request detailed explanation, then re-prompt |

### Batch Options (after 5 concerns or >5 total)

| Option | Effect |
|--------|--------|
| A | Continue one-by-one |
| B | Accept critical only |
| C | Accept all remaining |
| D | Reject all remaining |
| E | Accept critical+standard, skip minor |

### At Interview End

| Option | Effect |
|--------|--------|
| yes | Apply all accepted corrections to analysis documents |
| no | Save manifest for later, do not modify documents |
