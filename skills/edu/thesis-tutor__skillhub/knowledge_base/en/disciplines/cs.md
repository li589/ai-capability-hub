# Computer Science - Thesis Writing Guide

## Overview
Computer science thesis writing emphasizes innovation, reproducibility, and practical value. The core assessment criteria are: problem significance, methodological innovation, experimental validation, and engineering implementation.

## Thesis Types

### 1. Algorithm Research
- **Features**: Propose new algorithms or significantly improve existing ones
- **Structure**: Problem definition → Related work → Algorithm design → Complexity analysis → Experimental validation
- **Key Points**: Theoretical proof must be rigorous, experimental data must be sufficient

### 2. System Development
- **Features**: Design and implement large-scale software systems
- **Structure**: Requirements analysis → Architecture design → Module implementation → Testing validation → Performance evaluation
- **Key Points**: Code volume should be substantial, architecture must be reasonable

### 3. Theoretical Research
- **Features**: Prove new theorems or establish new theoretical frameworks
- **Structure**: Problem background → Definitions and lemmas → Main theorem → Proof process → Application examples
- **Key Points**: Logical rigor, no gaps in proof

## Chapter Structure

### Chapter 1: Introduction (8-10 pages)
1. Research background and significance
2. Problem statement (what problem to solve)
3. Research objectives and content
4. Thesis structure arrangement

### Chapter 2: Related Work (10-15 pages)
1. Research history
2. Current status (classical methods, latest progress)
3. Analysis of existing problems
4. Positioning of this research

### Chapter 3: Methodology (15-20 pages)
1. Core algorithm/system design
2. Theoretical analysis (if applicable)
3. Implementation details
4. Innovation highlights

### Chapter 4: Experiments/Validation (10-15 pages)
1. Experimental setup
2. Dataset description
3. Baseline methods
4. Main results (tables + charts)
5. Ablation studies
6. Case analysis

### Chapter 5: Conclusion (3-5 pages)
1. Summary of main contributions
2. Limitations
3. Future work

## Writing Standards

### Algorithm Description
- Use pseudocode format (reference to CLRS style)
- Include time/space complexity analysis
- Provide proof of correctness (if applicable)

### Experimental Presentation
- Dataset: Include size, source, preprocessing methods
- Metrics: Clearly define evaluation metrics
- Baselines: Select representative comparison methods
- Results: Use tables for precise data, charts for trends
- Statistical tests: Multiple runs, report mean and standard deviation

### Code Standards
- Include key code in appendix
- Code comments should be detailed
- Provide open-source links (if applicable)

## Common Issues

1. **Insufficient innovation**: Only simple combination or application of existing methods
2. **Inadequate experiments**: Single dataset, no comparison with SOTA
3. **Weak theoretical analysis**: No complexity analysis or proof of correctness
4. **Poor reproducibility**: Missing key hyperparameters or random seeds

## Recommended Tools
- LaTeX (academic typesetting)
- Python + Jupyter (experimental code)
- Git (version control)
- Overleaf (collaborative writing)

## Citation Format
- IEEE format (common in CS field)
- Ensure all cited papers are actually read
- Prioritize high-quality conferences and journals

## Quality Checklist
- [ ] Is the problem clearly defined?
- [ ] Is the method innovative enough?
- [ ] Are the experiments sufficient?
- [ ] Is the writing clear and logical?
- [ ] Are all citations accurate?
- [ ] Is the code/data available?
