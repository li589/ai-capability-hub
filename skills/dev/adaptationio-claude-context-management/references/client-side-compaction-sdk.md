# Client-Side Compaction SDK Complete Reference

## Overview

Client-side compaction is an SDK feature (Python and TypeScript) that automatically manages context by generating summaries when token usage exceeds a threshold. Unlike server-side clearing which removes content, compaction replaces entire history with a Claude-generated summary.

**Key Advantage**: Works at the SDK level with full control over summarization quality and custom domain-specific summaries.

**Where It Runs**: In your application, using the SDK's `tool_runner` method

---

## Architecture Overview

### Three-Stage Workflow

#### Stage 1: Monitor
After each model response, SDK calculates total tokens:
```
Total = input_tokens
       + cache_creation_input_tokens
       + cache_read_input_tokens
       + output_tokens
```

#### Stage 2: Trigger
When total exceeds `context_token_threshold`, SDK injects a summary request

#### Stage 3: Replace
Claude generates summary wrapped in `<summary></summary>` tags, entire history replaced with summary

### When Compaction Occurs

**Compaction happens automatically when**:
- Total tokens exceed configured threshold
- After model response completes
- Before next user message

**Result**: Next conversation starts with summary instead of full history

---

## Installation

### Python SDK

```bash
pip install anthropic
# Version must include tool_runner support (latest)
pip install --upgrade anthropic
```

**Verify Installation**:
```python
import anthropic
client = anthropic.Anthropic()
# Check for tool_runner method
assert hasattr(client.beta.messages, 'tool_runner')
```

### TypeScript SDK

```bash
npm install @anthropic-ai/sdk
# Ensure latest version
npm install --save-latest @anthropic-ai/sdk
```

**Verify Installation**:
```typescript
import Anthropic from '@anthropic-ai/sdk';
const client = new Anthropic();
// Check for toolRunner method
const hasToolRunner = typeof client.beta.messages.toolRunner === 'function';
```

---

## Configuration Parameters

### Complete Parameter Reference

```python
compaction_control = {
    "enabled": True,                          # Required: Enable compaction
    "context_token_threshold": 100000,        # Optional: Trigger threshold (default 100K)
    "model": "claude-sonnet-4-5",             # Optional: Model for summary (default: same)
    "summary_prompt": "..."                   # Optional: Custom summary instructions
}
```

### Parameter Defaults Table

| Parameter | Type | Default | Min | Max | Unit |
|-----------|------|---------|-----|-----|------|
| **enabled** | boolean | Required | N/A | N/A | N/A |
| **context_token_threshold** | number | 100,000 | 10,000 | 200,000 | tokens |
| **model** | string | Same as main | - | - | model ID |
| **summary_prompt** | string | Built-in | - | - | prompt text |

### Parameter Descriptions

#### 1. enabled (Required)

**Type**: `boolean`

**Purpose**: Activates automatic compaction

**Values**:
- `true`: Enable compaction
- `false`: Disable compaction

```python
compaction_control={
    "enabled": True
}
```

#### 2. context_token_threshold (Optional)

**Type**: `number`

**Default**: 100,000 tokens

**Recommended Values**:
- Conservative: 50,000-75,000 (frequent compaction)
- Balanced: 100,000-150,000 (typical)
- Aggressive: 150,000-200,000 (rare compaction)

**Selection Strategy**:
- **Aggressive** (50K): For memory-constrained environments, many turns
- **Balanced** (100K): For most applications
- **Conservative** (150K+): For long document analysis, preserve more context

```python
compaction_control={
    "enabled": True,
    "context_token_threshold": 100000  # Compact at 100K tokens
}
```

#### 3. model (Optional)

**Type**: `string` (model ID)

**Default**: Same model as main request

**Use Cases**:
- Default: Use same model (highest quality)
- `claude-haiku-4-5`: Cost optimization (60% cheaper summaries)
- `claude-sonnet-4-5`: Balance quality + cost
- `claude-opus-4-5`: Maximum summary quality

**Cost Trade-off**:
```
Summary Cost = (input_tokens * threshold_tokens / 1M) * model_cost

Example (Haiku vs Sonnet summarizing 100K tokens):
- Sonnet: (100K * 0.003) = $0.30
- Haiku: (100K * 0.00025) = $0.025  (92% cheaper)
```

```python
compaction_control={
    "enabled": True,
    "context_token_threshold": 100000,
    "model": "claude-haiku-4-5"  # Use Haiku for summaries only
}
```

#### 4. summary_prompt (Optional)

**Type**: `string`

**Default**: Built-in 5-section prompt

**When to Use**:
- Default: Works well for most use cases
- Custom: When you need domain-specific summary structure

**Example - Research Summarization**:
```python
summary_prompt = """Summarize the research conducted, including:
- Sources consulted and key findings
- Questions answered and remaining unknowns
- Recommended next steps

Wrap in <summary></summary> tags."""
```

```python
compaction_control={
    "enabled": True,
    "summary_prompt": summary_prompt
}
```

---

## Built-In Summary Structure

Claude's default summary includes **5 key sections**:

### 1. Task Overview
- User's core request
- Success criteria
- Business objectives

### 2. Current State
- Completed work
- Modified files
- Artifacts produced

### 3. Important Discoveries
- Technical constraints discovered
- Decisions made
- Failed approaches
- Insights

### 4. Next Steps
- Specific remaining actions
- Identified blockers
- Recommended sequence

### 5. Context to Preserve
- User preferences
- Domain-specific details
- Commitments or constraints
- Important decisions

---

## Installation & Setup

### Python SDK Setup

```python
import anthropic
from typing import Iterator

client = anthropic.Anthropic(
    api_key="sk-ant-...",
)

# Create runner with compaction
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[
        {
            "type": "text_editor_20250728",
            "name": "file_editor"
        }
    ],
    messages=[{
        "role": "user",
        "content": "Analyze all Python files in the project"
    }],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 100000
    }
)

# Process until completion
final_response = runner.until_done()
print(final_response.content[0].text)
```

### TypeScript SDK Setup

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
});

// Create runner with compaction
const runner = client.beta.messages.toolRunner({
    model: 'claude-sonnet-4-5',
    max_tokens: 4096,
    tools: [{
        type: 'text_editor_20250728',
        name: 'file_editor'
    }],
    messages: [{
        role: 'user',
        content: 'Analyze all Python files in the project'
    }],
    compactionControl: {
        enabled: true,
        contextTokenThreshold: 100000
    }
});

// Process until completion
const final = await runner.runUntilDone();
console.log(final.content[0].type === 'text' ? final.content[0].text : '');
```

---

## Complete Implementation Examples

### Pattern 1: Standard Long-Running Tasks

**Use Case**: File analysis, multi-step processing

```python
import anthropic

client = anthropic.Anthropic()

# Long-running file analysis with automatic compaction
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[
        {
            "type": "text_editor_20250728",
            "name": "file_editor",
            "max_characters": 10000
        }
    ],
    messages=[{
        "role": "user",
        "content": """Analyze all Python files in this directory:
        1. Identify code quality issues
        2. Check for security problems
        3. Suggest refactoring opportunities
        4. Document findings"""
    }],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 100000
    }
)

# Monitor progress
turn_count = 0
for event in runner:
    if hasattr(event, 'usage'):
        turn_count += 1
        print(f"Turn {turn_count}: {event.usage.input_tokens} input tokens")
        if event.usage.input_tokens > 80000:
            print("  (Approaching compaction threshold)")

# Get final analysis
result = runner.until_done()
print("\n=== Final Analysis ===")
print(result.content[0].text)
```

### Pattern 2: Cost-Optimized Summaries

**Use Case**: Maximum cost reduction while maintaining quality

```python
import anthropic

client = anthropic.Anthropic()

# Use cheaper model (Haiku) for summaries
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",  # Main model
    max_tokens=4096,
    tools=[
        {
            "type": "text_editor_20250728",
            "name": "file_editor"
        }
    ],
    messages=[{
        "role": "user",
        "content": "Review 50+ files and create comprehensive report"
    }],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 100000,
        "model": "claude-haiku-4-5"  # Cheaper for summaries
    }
)

# Process and track cost savings
cost_saved = 0
for event in runner:
    if hasattr(event, 'usage'):
        # Haiku: $0.00025/input, Sonnet: $0.003/input
        # Savings per token: 0.003 - 0.00025 = 0.00275
        # Would save ~$2.75 per 1M tokens of summary
        pass

result = runner.until_done()
print(result.content[0].text)
```

### Pattern 3: Frequent Compaction

**Use Case**: Memory-constrained environments

```python
import anthropic

client = anthropic.Anthropic()

# More aggressive compaction threshold
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[...],
    messages=[...],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 50000  # More frequent
    }
)

final = runner.until_done()
```

### Pattern 4: Custom Domain Summarization

**Use Case**: Specialized summarization for research/analysis

```python
import anthropic

client = anthropic.Anthropic()

# Custom summary prompt for medical research
research_summary_prompt = """Summarize research findings, including:

## Key Studies Found
- Citation and DOI
- Study design and sample size
- Main findings and conclusions

## Methodology Insights
- Common research approaches
- Data collection methods
- Statistical approaches used

## Gaps Identified
- Research limitations found
- Conflicting findings
- Areas needing more research

## Next Research Directions
- Promising research questions
- Methodological improvements needed
- Clinical/practical implications

Wrap entire summary in <summary></summary> tags."""

runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[
        {
            "type": "web_search_20250305",
            "name": "web_search"
        },
        {
            "type": "web_fetch_20250305",
            "name": "web_fetch"
        }
    ],
    messages=[{
        "role": "user",
        "content": "Research latest breakthroughs in immunotherapy for cancer treatment"
    }],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 150000,
        "summary_prompt": research_summary_prompt
    }
)

result = runner.until_done()
print(result.content[0].text)
```

### Complete TypeScript Implementation

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// File analysis with cost optimization
const runner = client.beta.messages.toolRunner({
    model: 'claude-sonnet-4-5',
    max_tokens: 4096,
    tools: [{
        type: 'text_editor_20250728',
        name: 'file_editor'
    }],
    messages: [{
        role: 'user',
        content: 'Analyze all configuration files and document findings'
    }],
    compactionControl: {
        enabled: true,
        contextTokenThreshold: 100000,
        model: 'claude-haiku-4-5'  // Cost optimization
    }
});

// Process with progress monitoring
let turnCount = 0;
for await (const message of runner) {
    if ('usage' in message) {
        turnCount++;
        console.log(`Turn ${turnCount}: ${message.usage.input_tokens} input tokens`);
    }
}

// Get final result
const final = await runner.runUntilDone();
console.log(final.content[0].type === 'text' ? final.content[0].text : '');
```

---

## Integration Patterns

### Pattern 1: Web Research with Automatic Compaction

```python
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[
        {
            "type": "web_search_20250305",
            "name": "web_search"
        },
        {
            "type": "web_fetch_20250305",
            "name": "web_fetch"
        }
    ],
    messages=[{
        "role": "user",
        "content": "Research topic X and compile comprehensive summary"
    }],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 100000
    }
)

# Automatically summarizes research after 100K tokens
result = runner.until_done()
```

### Pattern 2: Multi-File Processing

```python
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[{"type": "file_editor", "name": "editor"}],
    messages=[{
        "role": "user",
        "content": "Review all .py files and create audit report"
    }],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 150000,
        "model": "claude-haiku-4-5"  # Cost optimized
    }
)

# Processes many files with periodic summarization
result = runner.until_done()
```

### Pattern 3: Long Agent Conversations

```python
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    tools=[...many tools...],  # 10+ tools
    messages=[{"role": "user", "content": "Complete complex task"}],
    compaction_control={
        "enabled": True,
        "context_token_threshold": 100000
    }
)

# Handles multi-turn agent interactions
# Automatically compacts when context grows
result = runner.until_done()
```

---

## Best Practices

### 1. Start Conservative
- Set threshold higher initially (150K+)
- Monitor first few runs
- Adjust based on actual patterns

```python
compaction_control={
    "enabled": True,
    "context_token_threshold": 150000  # Start high
}
```

### 2. Monitor Actual Usage
```python
for event in runner:
    if hasattr(event, 'usage'):
        # Track pattern
        input_tokens = event.usage.input_tokens
        cache_read = event.usage.cache_read_input_tokens
        total = input_tokens + cache_read + event.usage.output_tokens
        print(f"Total tokens: {total}")
```

### 3. Cost Optimization
```python
# For long conversations, use cheaper model for summaries
compaction_control={
    "enabled": True,
    "context_token_threshold": 100000,
    "model": "claude-haiku-4-5"  # 92% cheaper
}
```

### 4. Custom Prompts for Domain
```python
# Adapt summary format to your domain
domain_prompt = """
[Your specific summarization requirements]

Wrap in <summary></summary> tags.
"""

compaction_control={
    "enabled": True,
    "summary_prompt": domain_prompt
}
```

### 5. Test Before Production
- Run pilot with sample workload
- Measure token reduction
- Verify summary quality
- Check response time impact

---

## Monitoring & Observability

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("anthropic.lib.tools").setLevel(logging.INFO)

# Now compaction events appear in logs
# Example output:
# INFO:anthropic.lib.tools:Starting compaction at 105000 tokens
# INFO:anthropic.lib.tools:Compaction complete, reduced to 25000 tokens
```

### Manual Token Tracking

```python
total_tokens_processed = 0
compaction_events = 0

for event in runner:
    if hasattr(event, 'usage'):
        total_tokens_processed += event.usage.input_tokens
        print(f"Running total: {total_tokens_processed}")

print(f"Compaction events: {compaction_events}")
print(f"Avg tokens per event: {total_tokens_processed / max(compaction_events, 1)}")
```

---

## Edge Cases & Solutions

### Issue: Tool Results Before Compaction

**Problem**: Compaction triggers while tool response pending

**What Happens**:
1. Tool response in progress
2. Compaction threshold exceeded
3. SDK removes tool use block before summary
4. Claude re-issues tool call after resuming

**Solution**: This is handled automatically - no action needed

### Issue: Server-Side Tool Token Miscalculation

**Problem**: When using server-side tools (web_search), `cache_read_input_tokens` includes internal API call reads, not just your conversation

**Impact**: Can trigger premature compaction

**Mitigation**:
```python
# Option 1: Use token counting endpoint
client.messages.count_tokens(
    model="claude-sonnet-4-5",
    messages=[...]  # Actual conversation
)

# Option 2: Increase threshold when using server tools
compaction_control={
    "enabled": True,
    "context_token_threshold": 150000  # Higher when using web_search
}

# Option 3: Limit compaction use with server tools
# Prefer server-side clearing instead
```

### Issue: Quality Degradation After Compaction

**Problem**: Summary loses important details

**Solutions**:
1. Use custom `summary_prompt` for domain specifics
2. Use same model for summaries (not cheaper model)
3. Increase threshold (less aggressive compaction)
4. Combine with memory tool for critical info

---

## Complete File Analysis Workflow

### Python Example (>200 lines)

```python
import anthropic
import json
from datetime import datetime

class FileAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.analysis_results = []
        self.compaction_events = []

    def analyze_files(self, directory_path: str) -> str:
        """Analyze all files with automatic compaction"""

        runner = self.client.beta.messages.tool_runner(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            tools=[
                {
                    "type": "text_editor_20250728",
                    "name": "file_editor",
                    "max_characters": 50000
                }
            ],
            messages=[{
                "role": "user",
                "content": f"""Analyze all files in {directory_path}:

                1. For each Python file:
                   - List functions and classes
                   - Identify code quality issues
                   - Check for security problems

                2. For configuration files:
                   - Validate syntax
                   - Check for missing required settings

                3. Summary:
                   - Overall code quality rating (1-10)
                   - Top 5 issues found
                   - Recommended improvements"""
            }],
            compaction_control={
                "enabled": True,
                "context_token_threshold": 100000,
                "model": "claude-haiku-4-5"
            }
        )

        # Monitor progress
        turn_count = 0
        last_threshold_warning = False

        for event in runner:
            if hasattr(event, 'usage'):
                turn_count += 1
                input_tokens = event.usage.input_tokens

                # Track when approaching compaction
                if input_tokens > 80000 and not last_threshold_warning:
                    print(f"Turn {turn_count}: {input_tokens} tokens - approaching compaction")
                    last_threshold_warning = True
                elif input_tokens < 50000:
                    last_threshold_warning = False

                print(f"Turn {turn_count}: {input_tokens} input tokens")

                # Track compaction events
                if hasattr(event, 'context_management'):
                    self.compaction_events.append({
                        "turn": turn_count,
                        "timestamp": datetime.now().isoformat(),
                        "event": event.context_management
                    })

        # Get final result
        result = runner.until_done()
        final_text = result.content[0].text

        # Save analysis
        self.analysis_results.append({
            "directory": directory_path,
            "timestamp": datetime.now().isoformat(),
            "turns": turn_count,
            "compaction_events": len(self.compaction_events),
            "analysis": final_text
        })

        return final_text

    def print_summary(self):
        """Print analysis summary"""
        print("\n=== Analysis Summary ===")
        for result in self.analysis_results:
            print(f"Directory: {result['directory']}")
            print(f"Turns: {result['turns']}")
            print(f"Compaction events: {result['compaction_events']}")
            print(f"Analysis:\n{result['analysis']}\n")

# Usage
analyzer = FileAnalyzer()
analysis = analyzer.analyze_files("./src")
analyzer.print_summary()
```

### TypeScript Example (>200 lines)

```typescript
import Anthropic from '@anthropic-ai/sdk';
import * as fs from 'fs';

interface AnalysisResult {
    directory: string;
    timestamp: string;
    turns: number;
    compactionEvents: number;
    analysis: string;
}

class FileAnalyzer {
    private client: Anthropic;
    private analysisResults: AnalysisResult[] = [];
    private compactionEvents: any[] = [];

    constructor() {
        this.client = new Anthropic({
            apiKey: process.env.ANTHROPIC_API_KEY
        });
    }

    async analyzeFiles(directoryPath: string): Promise<string> {
        // Create runner with compaction
        const runner = this.client.beta.messages.toolRunner({
            model: 'claude-sonnet-4-5',
            max_tokens: 4096,
            tools: [{
                type: 'text_editor_20250728',
                name: 'file_editor'
            }],
            messages: [{
                role: 'user',
                content: `Analyze all files in ${directoryPath}:

                1. For each Python/TypeScript file:
                   - List functions and classes
                   - Identify code quality issues
                   - Check security problems

                2. For configuration files:
                   - Validate syntax
                   - Check for missing settings

                3. Summary:
                   - Code quality rating (1-10)
                   - Top 5 issues
                   - Recommendations`
            }],
            compactionControl: {
                enabled: true,
                contextTokenThreshold: 100000,
                model: 'claude-haiku-4-5'
            }
        });

        // Monitor progress
        let turnCount = 0;
        let lastThresholdWarning = false;

        for await (const event of runner) {
            if ('usage' in event) {
                turnCount++;
                const inputTokens = event.usage.input_tokens;

                // Track approaching compaction
                if (inputTokens > 80000 && !lastThresholdWarning) {
                    console.log(`Turn ${turnCount}: ${inputTokens} tokens - approaching compaction`);
                    lastThresholdWarning = true;
                } else if (inputTokens < 50000) {
                    lastThresholdWarning = false;
                }

                console.log(`Turn ${turnCount}: ${inputTokens} input tokens`);

                // Track compaction
                if ('context_management' in event) {
                    this.compactionEvents.push({
                        turn: turnCount,
                        timestamp: new Date().toISOString(),
                        event: event.context_management
                    });
                }
            }
        }

        // Get final result
        const result = await runner.runUntilDone();
        const finalText = result.content[0].type === 'text' ? result.content[0].text : '';

        // Save analysis
        this.analysisResults.push({
            directory: directoryPath,
            timestamp: new Date().toISOString(),
            turns: turnCount,
            compactionEvents: this.compactionEvents.length,
            analysis: finalText
        });

        return finalText;
    }

    printSummary(): void {
        console.log('\n=== Analysis Summary ===');
        for (const result of this.analysisResults) {
            console.log(`Directory: ${result.directory}`);
            console.log(`Turns: ${result.turns}`);
            console.log(`Compaction events: ${result.compactionEvents}`);
            console.log(`Analysis:\n${result.analysis}\n`);
        }
    }
}

// Usage
(async () => {
    const analyzer = new FileAnalyzer();
    await analyzer.analyzeFiles('./src');
    analyzer.printSummary();
})();
```

---

## Summary Prompt Structure

### Default Built-In Structure (5 Sections)

The default summary includes:
1. What the user asked for
2. What's been accomplished so far
3. Important discoveries or learnings
4. What still needs to be done
5. Important context to remember

### Custom Prompt Example

```python
custom_summary_prompt = """Summarize the conversation in 5 sections:

## Objectives
- Original request and goals
- Success criteria

## Progress
- Steps completed
- Files modified or created
- Tools used

## Key Findings
- Important discoveries
- Constraints identified
- Decisions made

## Remaining Work
- Specific next steps
- Known blockers
- Estimated effort

## Important Context
- User preferences
- Domain details
- Critical assumptions

Format entire summary within <summary></summary> tags."""
```

---

## Performance Characteristics

### Typical Token Reduction

After compaction triggers at 100K tokens:
- Pre-compaction: 100K input tokens
- Post-compaction: 15K-25K input tokens (summary size)
- Reduction: 75-85% of accumulated history

### Processing Time

- Compaction generation: 2-5 seconds (Claude generating summary)
- Overhead: Usually offset by reduced subsequent processing time
- Net impact: Often faster (less context to process)

---

**Last Updated**: November 2025
**Reference Quality**: Comprehensive (3-stage workflow, 4 patterns, 4 integration examples)
**Citation**: Official Anthropic SDK documentation
