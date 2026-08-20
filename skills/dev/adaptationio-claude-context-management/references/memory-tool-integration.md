# Memory Tool Integration Complete Reference

## Overview

The memory tool enables persistent storage across API calls, paired with context editing for automatic context preservation. When context approaches clearing thresholds, Claude receives automatic warnings to save important information before content is removed.

**Key Innovation**: Proactive preservation - Claude is warned before clearing occurs and can write summaries to persistent storage.

**Use Cases**:
- Long-running projects spanning days/weeks
- Multi-session workflows requiring state persistence
- Knowledge accumulation across conversations
- Agentic tasks needing cross-session memory

---

## How Memory Tool Works

### Basic Concept

Memory is key-value storage persistent across API calls:
- **Keys**: Identifiers for memory items (e.g., "project_status", "findings")
- **Values**: Any text content (up to 128K characters per item)
- **Scope**: Per-conversation (conversation ID isolation)
- **Access**: Via Claude's memory tool

### Memory Tool API

```python
{
    "type": "memory_20250818",
    "name": "memory"
}
```

**Operations**:
1. **Read**: Retrieve value by key
2. **Write**: Create or update key-value pair
3. **List**: See all keys in memory
4. **Delete**: Remove key-value pair

---

## Integration with Context Clearing

### Automatic Warning System

**Flow**:
1. Context approaching configured threshold
2. API sends **automatic warning** to Claude
3. Claude receives notice: "Context clearing approaching"
4. Claude can proactively use memory tool
5. Content is cleared from active conversation
6. Memory persists for future access

### What Claude Knows When Warned

```
You are approaching the context management threshold.
Important information will be cleared from the conversation.
Consider using the memory tool to preserve critical details.
```

### How Claude Responds

Typically:
1. Summarizes current progress
2. Writes summary to memory with descriptive key
3. Saves important findings
4. Documents next steps
5. Notes any workarounds or solutions

---

## API Implementation

### Python Example - Memory + Context Clearing

```python
import anthropic

client = anthropic.Anthropic()

# Enable both memory tool and context clearing
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Research and document the history of AI"
        }
    ],
    tools=[
        {
            "type": "memory_20250818",
            "name": "memory"
        },
        {
            "type": "web_search_20250305",
            "name": "web_search"
        }
    ],
    betas=["context-management-2025-06-27"],
    context_management={
        "edits": [
            {
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 100000},
                "keep": {"type": "tool_uses", "value": 3}
            }
        ]
    }
)

# Claude automatically uses memory before clearing
print(response.content[0].text)
```

### TypeScript Example - Memory Integration

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

const response = await client.beta.messages.create({
    model: 'claude-sonnet-4-5',
    max_tokens: 4096,
    messages: [{
        role: 'user',
        content: 'Research climate change impacts and document findings'
    }],
    tools: [
        {
            type: 'memory_20250818',
            name: 'memory'
        },
        {
            type: 'web_search_20250305',
            name: 'web_search'
        }
    ],
    betas: ['context-management-2025-06-27'],
    context_management: {
        edits: [{
            type: 'clear_tool_uses_20250919',
            trigger: { type: 'input_tokens', value: 100000 }
        }]
    }
});

console.log(response.content[0].type === 'text' ? response.content[0].text : '');
```

---

## Persistent Storage Patterns

### Pattern 1: Session Progress Tracking

**Use Case**: Track progress across multi-turn conversations

```python
# Claude typically writes progress like:
memory_write = {
    "key": "session_progress",
    "value": """
    Progress Report - Day 2

    Completed:
    - Analyzed 15 documents
    - Identified 3 key trends
    - Drafted recommendations

    In Progress:
    - Cost-benefit analysis
    - Stakeholder impact assessment

    Next Steps:
    - Complete analysis
    - Create presentation
    - Schedule review meeting

    Important Findings:
    - Trend #1: X, with implications Y
    - Trend #2: A, with implications B
    - Trend #3: P, with implications Q
    """
}
```

### Pattern 2: Knowledge Accumulation

**Use Case**: Build knowledge base across sessions

```python
memory_write = {
    "key": "technical_findings",
    "value": """
    Technical Knowledge Base

    Architecture Insights:
    - System uses event-driven pattern
    - Database transactions are ACID-compliant
    - Cache invalidation strategy: TTL-based

    Performance Characteristics:
    - Average response time: 50ms
    - Peak load: 10K requests/sec
    - Bottleneck: Database writes

    Security Findings:
    - Authentication: OAuth 2.0
    - Data encryption: AES-256
    - Known CVEs: None in current version
    """
}
```

### Pattern 3: Decision Log

**Use Case**: Record decisions for future reference

```python
memory_write = {
    "key": "decisions_made",
    "value": """
    Decision Log

    Decision #1: Use Claude Sonnet for analysis
    - Rationale: Cost-effective, good quality
    - Date: 2025-11-25
    - Owner: Project lead
    - Status: Active

    Decision #2: Focus on tool optimization
    - Rationale: 85% efficiency gains available
    - Date: 2025-11-25
    - Owner: Tech lead
    - Status: In progress

    Decision #3: Implement automatic compaction
    - Rationale: Reduce long conversation costs
    - Date: 2025-11-25
    - Owner: Tech lead
    - Impact: 50% cost reduction estimated
    """
}
```

### Pattern 4: Troubleshooting Notes

**Use Case**: Document issues and solutions for recurring problems

```python
memory_write = {
    "key": "troubleshooting_guide",
    "value": """
    Known Issues and Solutions

    Issue: Tool results being cleared too aggressively
    Solution: Increase clear_at_least parameter to 5000
    Status: Resolved
    Date: 2025-11-24

    Issue: Web search results lost before analysis
    Solution: Add web_search to exclude_tools list
    Status: Active
    Date: 2025-11-24

    Issue: Summary quality degraded with Haiku model
    Solution: Use Sonnet for summaries, Haiku for analysis only
    Status: Testing
    Date: 2025-11-25
    """
}
```

---

## Primary Use Cases

### Use Case 1: Long-Running Projects

**Scenario**: Multi-day code analysis or research project

```python
# Day 1
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Analyze codebase"}],
    tools=[memory_tool, file_editor],
    context_management=context_editing
)
# Claude saves: "day_1_analysis", "architecture_notes", "findings"

# Day 2
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "user", "content": "Continue from where we left off"}
        # Claude can read memory from Day 1
    ],
    tools=[memory_tool, file_editor],
    context_management=context_editing
)
# Claude continues work, references memory from Day 1
```

### Use Case 2: Multi-Session Workflows

**Scenario**: Multiple analysis sessions on same project

```
Session 1: Data collection and exploration
Session 2: Pattern identification (uses Session 1 memory)
Session 3: Hypothesis testing (uses Sessions 1-2 memory)
Session 4: Final report (uses all previous sessions)
```

### Use Case 3: Knowledge Accumulation

**Scenario**: Building domain knowledge over time

```python
# Session 1: Research Topic A
# Memory: findings_topic_a
response1 = client.beta.messages.create(...)

# Session 2: Research Topic B
# Memory: findings_topic_b
# Claude can combine with Topic A knowledge
response2 = client.beta.messages.create(...)

# Session 3: Synthesis
# Claude combines all memory items
response3 = client.beta.messages.create(...)
```

---

## Integration Examples

### Example 1: Multi-Step Research with Memory

```python
import anthropic

client = anthropic.Anthropic()

def research_workflow():
    """Research task with automatic memory preservation"""

    # Step 1: Initial research
    response1 = client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": "Research Topic: Quantum Computing Fundamentals"
        }],
        tools=[
            {"type": "memory_20250818", "name": "memory"},
            {"type": "web_search_20250305", "name": "web_search"}
        ],
        betas=["context-management-2025-06-27"],
        context_management={
            "edits": [{
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 100000},
                "exclude_tools": ["web_search"]
            }]
        }
    )
    print("Step 1 - Initial Research Complete")
    print(response1.content[0].text)

    # Step 2: Deeper analysis (Claude can reference Step 1 memory)
    response2 = client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": """Continue research:
            Deep dive into quantum algorithms.
            Reference previous findings from memory."""
        }],
        tools=[
            {"type": "memory_20250818", "name": "memory"},
            {"type": "web_search_20250305", "name": "web_search"}
        ],
        betas=["context-management-2025-06-27"],
        context_management={
            "edits": [{
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 100000},
                "exclude_tools": ["web_search"]
            }]
        }
    )
    print("\nStep 2 - Deeper Analysis Complete")
    print(response2.content[0].text)

    # Step 3: Synthesis (Claude combines all memory)
    response3 = client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": """Create comprehensive report:
            Synthesize all research from memory.
            Include both fundamentals and algorithms.
            Provide actionable recommendations."""
        }],
        tools=[
            {"type": "memory_20250818", "name": "memory"}
        ]
    )
    print("\nStep 3 - Final Report")
    print(response3.content[0].text)

research_workflow()
```

### Example 2: Agentic Task with State Persistence

```python
import anthropic
from typing import Optional

client = anthropic.Anthropic()

class ProjectAgent:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.client = anthropic.Anthropic()

    def execute_phase(self, phase_num: int, task: str):
        """Execute one phase of multi-phase project"""

        # Claude can reference memory from previous phases
        user_message = f"""
        Project Phase {phase_num}: {task}

        Context:
        - Review previous phases from memory
        - Build upon earlier work
        - Update progress in memory before clearing
        """

        response = self.client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": user_message}],
            tools=[
                {"type": "memory_20250818", "name": "memory"},
                {"type": "text_editor_20250728", "name": "editor"}
            ],
            betas=["context-management-2025-06-27"],
            context_management={
                "edits": [{
                    "type": "clear_tool_uses_20250919",
                    "trigger": {"type": "input_tokens", "value": 100000}
                }]
            }
        )

        return response.content[0].text

# Usage
agent = ProjectAgent("AI Safety Analysis")

# Phase 1: Data Collection
phase1 = agent.execute_phase(
    1,
    "Collect 50+ research papers on AI safety"
)
print("Phase 1 Complete")

# Phase 2: Analysis (references Phase 1 memory)
phase2 = agent.execute_phase(
    2,
    "Analyze papers and identify key themes"
)
print("Phase 2 Complete")

# Phase 3: Synthesis (references Phases 1-2)
phase3 = agent.execute_phase(
    3,
    "Create comprehensive report with recommendations"
)
print("Phase 3 Complete")
```

### Example 3: TypeScript Workflow

```typescript
import Anthropic from '@anthropic-ai/sdk';

interface PhaseResult {
    phase: number;
    output: string;
    timestamp: Date;
}

class DocumentAnalyzer {
    private client: Anthropic;
    private results: PhaseResult[] = [];

    constructor() {
        this.client = new Anthropic();
    }

    async analyzePhase(phase: number, task: string): Promise<string> {
        const response = await this.client.beta.messages.create({
            model: 'claude-sonnet-4-5',
            max_tokens: 4096,
            messages: [{
                role: 'user',
                content: `Phase ${phase}: ${task}

                Review memory from previous phases.
                Save progress and findings before context clears.`
            }],
            tools: [
                { type: 'memory_20250818', name: 'memory' },
                { type: 'text_editor_20250728', name: 'editor' }
            ],
            betas: ['context-management-2025-06-27'],
            context_management: {
                edits: [{
                    type: 'clear_tool_uses_20250919',
                    trigger: { type: 'input_tokens', value: 100000 }
                }]
            }
        });

        const output = response.content[0].type === 'text' ?
            response.content[0].text : '';

        this.results.push({
            phase,
            output,
            timestamp: new Date()
        });

        return output;
    }

    async runAnalysis(): Promise<void> {
        // Phase 1: Collection
        await this.analyzePhase(1, 'Collect and catalog all documents');

        // Phase 2: Analysis (references Phase 1)
        await this.analyzePhase(2, 'Analyze documents for key information');

        // Phase 3: Report (references all phases)
        await this.analyzePhase(3, 'Create comprehensive analysis report');

        console.log('Analysis Complete');
        this.results.forEach(r => {
            console.log(`Phase ${r.phase}: ${r.output.substring(0, 100)}...`);
        });
    }
}

// Usage
const analyzer = new DocumentAnalyzer();
analyzer.runAnalysis();
```

---

## Best Practices

### 1. Use Descriptive Keys

```python
# Good
"ai_safety_research_findings"
"quantum_computing_algorithms"
"project_phase_3_decisions"

# Avoid
"data_1"
"temp_info"
"x"
```

### 2. Structure Memory Content

```python
memory_write = {
    "key": "analysis_summary",
    "value": """## Analysis Summary

### Key Findings
- Finding 1: ...
- Finding 2: ...

### Recommendations
1. ...
2. ...

### Next Steps
- ...
"""
}
```

### 3. Update Instead of Create New Keys

```python
# Instead of creating new keys each time:
# key: "findings_v1", "findings_v2", "findings_v3"

# Update single key:
memory_write = {
    "key": "findings",  # Same key
    "value": "Updated findings with new information"
}
```

### 4. Include Metadata

```python
memory_write = {
    "key": "project_status",
    "value": """Date: 2025-11-25
    Version: 3
    Status: In Progress

    Content:
    ...
    """
}
```

### 5. Archive Old Memory

```python
# After extensive updates, consider:
memory_delete = {
    "key": "outdated_findings"
}

memory_write = {
    "key": "current_findings",
    "value": "Latest consolidated findings"
}
```

---

## Troubleshooting

### Issue: Claude Not Using Memory Tool

**Problem**: Claude isn't saving to memory before clearing

**Solution**:
1. Ensure memory tool in tools list
2. Ensure context_management configured
3. Set appropriate threshold (should trigger within conversation)
4. Check Claude receives warning message

```python
# Verify configuration
tools=[
    {"type": "memory_20250818", "name": "memory"},  # REQUIRED
    ...
]

context_management={
    "edits": [{
        "type": "clear_tool_uses_20250919",
        "trigger": {"type": "input_tokens", "value": 100000}
    }]
}
```

### Issue: Memory Not Persisting Across Sessions

**Problem**: Memory from one session not available in next

**Cause**: Conversation context isolation - different conversation = different memory

**Solution**: Design for manual retrieval in next conversation

```python
# Session 1: Claude saves findings
response1 = client.beta.messages.create(...)

# Session 2: Ask Claude to recall from memory
response2 = client.beta.messages.create(
    messages=[{
        "role": "user",
        "content": "Recall findings from memory and continue analysis"
    }],
    tools=[
        {"type": "memory_20250818", "name": "memory"}  # Access memory from S1
    ]
)
```

### Issue: Memory Getting Large

**Problem**: Memory items accumulating to huge sizes

**Solution**:
1. Summarize old memory periodically
2. Archive to separate keys
3. Delete obsolete entries
4. Keep memory focused and organized

```python
# Cleanup old memory
client.beta.messages.create(
    model="claude-sonnet-4-5",
    messages=[{
        "role": "user",
        "content": """Clean up memory:
        1. Summarize old_findings into findings_summary
        2. Delete old_findings
        3. Archive by date"""
    }],
    tools=[
        {"type": "memory_20250818", "name": "memory"}
    ]
)
```

---

## Key Concepts

**Memory**: Persistent key-value storage across API calls

**Scope**: Per-conversation (conversation ID isolation)

**Automatic Warning**: API notifies Claude before clearing occurs

**Proactive Preservation**: Claude can write to memory when warned

**Integration**: Works seamlessly with both clearing strategies

**Persistence**: Survives context clearing events

---

## Related Features

- **clear_tool_uses_20250919**: Tool result clearing (triggers memory warning)
- **clear_thinking_20251015**: Thinking block clearing (complements memory)
- **Context Window**: Maximum tokens available (memory helps manage)
- **Prompt Caching**: Alternative optimization (memory for persistence)

---

## Supported Models

Memory tool works with all Claude 3.5+ models:
- Claude Opus 4.5
- Claude Opus 4.1
- Claude Sonnet 4.5
- Claude Sonnet 4
- Claude Haiku 4.5

---

**Last Updated**: November 2025
**Reference Quality**: Comprehensive (proactive preservation, 3 use cases, integration examples)
**Citation**: Official Anthropic documentation
