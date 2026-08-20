---
name: second-brain-triage
description: Intelligent information triage system based on Tiago Forte's PARA method (Projects/Areas/Resources/Archive) for automatic categorization and priority scoring. Use when the user wants to organize notes, classify content, prioritize tasks, or manage their second brain knowledge base.
install_source: official
install_method: download
skill_id: official_xMUxMCrB
enabled_at: 1787232758901
version: 1.0.0
name_zh: 第二大脑分拣
---

# Second Brain Triage

Intelligent information triage system based on Tiago Forte's PARA method (Projects/Areas/Resources/Archive) for automatic categorization and priority scoring.

## Features

- **Content Analyzer**: Automatically identify content types (articles, videos, tasks, code, etc.) and extract metadata
- **PARA Classifier**: Smart categorization into Projects/Areas/Resources/Archive
- **Urgency Scorer**: Multi-dimensional algorithm to evaluate processing priority (1-10 scale)
- **Relatedness Detector**: Discover similarities and relationships between content items

## Usage

### Basic Usage

```javascript
const { SecondBrainTriage } = require('./src');

const triage = new SecondBrainTriage();

// Triage single content item
const result = triage.triage('TODO: Complete project report, due this Friday');
console.log(result.summary);
// {
//   title: "Complete project report, due this Friday",
//   type: "task",
//   category: "Projects",
//   urgency: "High urgency",
//   urgencyScore: 8,
//   action: "Process today: recommend completing within 24 hours"
// }

// Batch triage
const results = triage.triageBatch([
  'https://github.com/user/repo',
  'Notes on learning React Hooks',
  'TODO: Fix login bug',
]);

// Export report
const report = triage.exportReport(results, 'markdown');
```

### CLI Usage

```bash
# Analyze single content item
node scripts/triage.js "Text content to process"

# Analyze file
node scripts/triage.js --file ./notes.txt

# Batch analysis
node scripts/triage.js --batch ./items.json --output report.md
```

## Classification Guide

### PARA Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Projects** | Items with clear goals and deadlines | "Develop new feature", "Complete report" |
| **Areas** | Long-term responsibilities and standards | "Health management", "Skill development" |
| **Resources** | Topics of interest and reference materials | "Technical articles", "Learning notes" |
| **Archive** | Completed or inactive items | "Finished projects", "Historical records" |
| **Inbox** | Temporary storage for uncategorized items | Content that cannot be determined |

### Urgency Levels

| Score | Level | Description | Recommendation |
|-------|-------|-------------|----------------|
| 9-10 | Critical | Process immediately | Take action now |
| 7-8 | High | Process today | Complete within 24 hours |
| 5-6 | Medium | Process this week | Schedule within the week |
| 3-4 | Low | Low priority | Can be deferred |
| 1-2 | Minimal | Archive for reference | No immediate action needed |

## Technical Architecture

```
src/
├── content-analyzer.js    # Content type recognition and metadata extraction
├── para-classifier.js     # PARA classification algorithm
├── urgency-scorer.js      # Urgency scoring algorithm
├── relatedness-detector.js # Relatedness detection
└── index.js               # Main entry and API
```

## Scoring Algorithm

### Urgency Scoring Dimensions

1. **Time Sensitivity** (30%): Deadlines, time keywords
2. **Action Requirement** (25%): Action verbs like must/plan/maybe
3. **Consequences** (20%): Potential impact of not processing
4. **Context Signals** (15%): Blockers, external dependencies
5. **User Preferences** (10%): Configurable priorities

### Relatedness Detection

- Tag similarity (Jaccard coefficient)
- Title/description text similarity (Cosine similarity)
- Semantic similarity (based on semantic groups)
- Type matching

## Configuration Options

```javascript
const triage = new SecondBrainTriage({
  enableRelatedness: true,    // Enable relatedness detection
  urgencyThreshold: 5,        // Urgency threshold
});
```

## Output Formats

Supported export formats:
- JSON (complete data)
- Markdown (readable format)
- CSV (spreadsheet format)

## Dependencies

- Node.js >= 14
- No external dependencies (pure JavaScript implementation)

## License

MIT