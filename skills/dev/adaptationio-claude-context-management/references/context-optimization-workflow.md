# Context Optimization Workflow

## Overview

This reference provides workflow patterns for implementing context management in production systems, with focus on infinite conversations, cost optimization, and real-world implementation.

---

## Progressive Disclosure Pattern

### Rationale

When processing large amounts of content, applying progressive disclosure (glob → grep → read) reduces upfront token cost:

**Traditional Approach**:
- Read all files immediately
- Large upfront token cost
- May exceed context window

**Progressive Disclosure**:
1. **Glob**: List files (cheap, minimal tokens)
2. **Grep**: Search relevant files (targeted, medium tokens)
3. **Read**: Get full content only for relevant items (focused, minimal tokens)

### Implementation

```python
# Stage 1: GLOB - Discover files
# Cost: ~100 tokens
files = glob.glob("project/**/*.py")

# Stage 2: GREP - Find relevant files
# Cost: ~500 tokens (only search relevant files)
relevant = grep(pattern="class.*Model", files=files)

# Stage 3: READ - Get full content
# Cost: ~5000 tokens (only relevant files)
content = read(relevant_files)
```

### Token Savings Example

```
Traditional (read all):
- 500 Python files × 1000 tokens = 500K tokens

Progressive (glob + grep + read):
- Glob: 100 tokens
- Grep: 500 tokens
- Read (50 relevant): 50K tokens
- Total: 50.6K tokens
- Savings: 89.8%
```

---

## Caching Strategies

### Pattern: Prompt Caching + Context Editing

Combine prompt caching (for repeated prefixes) with context clearing (for growing tails):

```
Request 1:
[System prompt]      ← Cached
[Initial context]    ← Cached
[Q1]                 ← New
→ Response 1

Request 2:
[System prompt]      ← Cache HIT
[Initial context]    ← Cache HIT
[Q1] [R1]           ← New
[Q2]                ← New
→ Response 2 (25% cheaper if using cache)

Request 3: (Context exceeds 100K)
[System prompt]      ← Cache HIT
[Summarized context] ← New (replaces old messages)
[Q3]                ← New
→ Response 3 (clearing costs write cost, but better than no clearing)
```

**Cost Trade-off**:
- With caching only: Grows indefinitely
- With clearing only: Loses cache benefits (invalidation)
- Balanced: Keep system prompt cached, clear conversation history

### Implementation

```python
import anthropic

client = anthropic.Anthropic()

# Enable both caching and context clearing
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "You are a helpful assistant"
        },
        {
            "type": "text",
            "text": "[Large static context - 50K tokens]",
            "cache_control": {"type": "ephemeral"}  # Cache this
        }
    ],
    messages=[
        {"role": "user", "content": "First question"}
    ],
    betas=["context-management-2025-06-27"],
    context_management={
        "edits": [{
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 100000}
        }]
    }
)
```

---

## Infinite Conversations Implementation

### Architecture

```
User Input
    ↓
[Context Check]
    ↓
[Is context > 80K?] ←→ NO → Add to conversation
    ↓ YES
[Memory Tool Warning]
    ↓
Claude proactively saves important info to memory
    ↓
[Context Clearing Triggered]
    ↓
[Next Turn Starts]
    ↓
Claude has access to memory from previous conversation
    ↓
Continue indefinitely
```

### Implementation Pattern

```python
import anthropic

client = anthropic.Anthropic()

class InfiniteChat:
    def __init__(self):
        self.messages = []
        self.conversation_id = "chat_001"

    def add_message(self, role: str, content: str):
        """Add message to conversation"""
        self.messages.append({
            "role": role,
            "content": content
        })

    def get_response(self, user_input: str) -> str:
        """Get Claude's response (handles infinite conversation)"""

        self.add_message("user", user_input)

        response = client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=self.messages,
            tools=[
                {"type": "memory_20250818", "name": "memory"}
            ],
            betas=["context-management-2025-06-27"],
            context_management={
                "edits": [{
                    "type": "clear_tool_uses_20250919",
                    "trigger": {"type": "input_tokens", "value": 100000},
                    "keep": {"type": "tool_uses", "value": 3}
                }]
            }
        )

        assistant_message = response.content[0].text
        self.add_message("assistant", assistant_message)

        return assistant_message

# Usage - Can run indefinitely
chat = InfiniteChat()

for turn in range(100):  # 100 turns = would exceed context
    user_input = input("You: ")
    response = chat.get_response(user_input)
    print(f"Claude: {response}\n")
```

### Auto-Summarization Pattern

For explicit control over summarization timing:

```python
import anthropic

client = anthropic.Anthropic()

def auto_summarize_conversation(messages: list) -> str:
    """Generate summary of conversation"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=messages + [{
            "role": "user",
            "content": """Summarize this conversation:
            - Key topics discussed
            - Decisions made
            - Important findings
            - Next steps

            Format: <summary>...</summary>"""
        }]
    )

    return response.content[0].text

# When conversation gets long
if total_tokens > 100000:
    summary = auto_summarize_conversation(messages)
    # Replace messages with summary
    messages = [{
        "role": "assistant",
        "content": summary
    }]
    # Continue conversation with fresh context
```

---

## Cost Optimization Checklist

### Pre-Deployment Checklist (10+ items)

- [ ] **Model Selection**
  - [ ] Using cheapest appropriate model (Haiku for simple, Sonnet for complex)?
  - [ ] Considered effort parameter for Opus 4.5?
  - [ ] Right model for summaries (using Haiku for compaction)?

- [ ] **Context Management**
  - [ ] Context editing configured?
  - [ ] Appropriate trigger threshold set (100K typical)?
  - [ ] Important tools excluded from clearing?
  - [ ] Memory tool enabled for persistence?

- [ ] **Request Optimization**
  - [ ] Removing redundant context?
  - [ ] Using progressive disclosure (glob → grep → read)?
  - [ ] Batching requests where possible?
  - [ ] Implementing caching for repeated prefixes?

- [ ] **Tool Optimization**
  - [ ] Using tool search for 10+ tools?
  - [ ] Using programmatic calling for 3+ dependent calls?
  - [ ] Keeping only 3-5 tools always loaded?
  - [ ] Deferring rarely-used tools?

- [ ] **Monitoring**
  - [ ] Tracking input tokens per request?
  - [ ] Monitoring cost per task?
  - [ ] Alerting on unexpected token usage?
  - [ ] Logging clearing events?

- [ ] **Testing**
  - [ ] Tested quality with context clearing enabled?
  - [ ] Verified no important information lost?
  - [ ] Measured actual token savings?
  - [ ] Load tested with realistic workloads?

### Production Monitoring (10+ items)

- [ ] **Daily Checks**
  - [ ] Average tokens per request within expected range?
  - [ ] No unexpected clearing patterns?
  - [ ] Memory growing as expected?
  - [ ] Response latency acceptable?

- [ ] **Weekly Reviews**
  - [ ] Cost trending correctly?
  - [ ] Quality maintained throughout weeks?
  - [ ] Any clearing events impacting users?
  - [ ] Tool usage distribution optimal?

- [ ] **Monthly Optimization**
  - [ ] Review and adjust trigger thresholds?
  - [ ] Identify new optimization opportunities?
  - [ ] Archive old memory?
  - [ ] Update model selection based on usage patterns?

---

## Token Savings Calculations

### Example 1: Web Search Workflow

**Scenario**: Research task with 30 web searches

```
Without context clearing:
- Initial context: 2K tokens
- Each search: 3K tokens input + 2K tokens response
- 30 searches: 30 × (3K + 2K) = 150K tokens
- Final question: 5K tokens
- Total: 157K tokens

With context clearing (clear tool uses at 100K):
- Initial: 2K tokens
- Searches 1-20: 100K tokens accumulated
- CLEARING TRIGGERED: Removes 15 oldest searches (75K tokens freed)
- Searches 21-30: 50K tokens
- Final question: 5K tokens
- Total: 157K - 75K = 82K tokens
- Savings: 47.8%
```

### Example 2: File Analysis Workflow

**Scenario**: Analyze 100 files with file operations

```
Without compaction:
- Initial context: 1K tokens
- Each file operation: 2K input + 1K output
- 100 files: ~300K tokens
- Summary request: ~50K tokens
- Total: 351K tokens

With client-side compaction (threshold 100K):
- Initial: 1K tokens
- Files 1-40: 100K tokens reached
- COMPACTION TRIGGERED: Generates summary (15K tokens)
- Replace with summary: 15K tokens
- Files 41-100: 100K tokens accumulated
- COMPACTION TRIGGERED again: Generates summary (15K tokens)
- Replace with summary: 15K tokens
- Final report: 50K tokens
- Total: 1K + 100K + 15K + 100K + 15K + 50K = 281K tokens
- Savings: 19.9% + ability to handle unlimited files
```

### Example 3: Extended Thinking Workflow

**Scenario**: Complex problem solving with extended thinking

```
Without thinking block clearing:
- Thinking blocks: 30K tokens
- Problem setup: 5K tokens
- Response: 3K tokens
- Next turn: Must keep all 30K + 5K + 3K = 38K
- After 5 turns: 38K × 5 = 190K tokens (just thinking!)

With clear_thinking_20251015 (keep=2):
- Turn 1: 30K thinking + 5K + 3K
- Turn 2: 30K thinking + 5K + 3K + (OLD thinking cleared)
- Turn 3-5: Same pattern
- Total: ~5K + 3K repeated = 80K tokens after 5 turns
- Savings: 57.9%
```

---

## Real-World Scenarios

### Scenario 1: Customer Support Chatbot

```python
# Long customer conversations with context management
class SupportBot:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.messages = []
        self.client = anthropic.Anthropic()

    def handle_message(self, user_message: str) -> str:
        """Handle customer message with cost optimization"""

        self.messages.append({"role": "user", "content": user_message})

        response = self.client.beta.messages.create(
            model="claude-haiku-4-5",  # Cheaper model
            max_tokens=1024,
            messages=self.messages,
            tools=[{"type": "memory_20250818", "name": "memory"}],
            betas=["context-management-2025-06-27"],
            context_management={
                "edits": [{
                    "type": "clear_tool_uses_20250919",
                    "trigger": {"type": "input_tokens", "value": 50000},
                    "keep": {"type": "tool_uses", "value": 5}
                }]
            }
        )

        assistant_response = response.content[0].text
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

# Optimize customer support costs
bot = SupportBot("CUSTOMER_123")
# Each conversation can be indefinitely long without cost explosion
while True:
    user_input = input("Customer: ")
    response = bot.handle_message(user_input)
    print(f"Support: {response}")
```

### Scenario 2: Research Paper Analyzer

```python
# Analyze 50+ research papers across multiple sessions
class ResearchAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def analyze_papers(self, paper_ids: list) -> str:
        """Analyze papers with automatic compaction"""

        runner = self.client.beta.messages.tool_runner(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            tools=[
                {"type": "web_fetch_20250305", "name": "fetch_paper"}
            ],
            messages=[{
                "role": "user",
                "content": f"""Analyze these {len(paper_ids)} papers:
                {paper_ids}

                For each paper:
                1. Summarize methodology
                2. Key findings
                3. Implications
                4. Limitations

                Create final comparative analysis."""
            }],
            compaction_control={
                "enabled": True,
                "context_token_threshold": 100000,
                "model": "claude-haiku-4-5"  # Haiku summarizes
            }
        )

        result = runner.until_done()
        return result.content[0].text

# Can analyze any number of papers
analyzer = ResearchAnalyzer()
analysis = analyzer.analyze_papers([
    "paper_1", "paper_2", ..., "paper_50"  # All 50 papers
])
```

### Scenario 3: Long Code Review

```python
# Review large codebases across sessions
class CodeReviewer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.client = anthropic.Anthropic()
        self.session_num = 0

    def review_session(self, session_task: str) -> str:
        """One review session (can be days apart)"""

        self.session_num += 1

        response = self.client.beta.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""Code Review Session {self.session_num}:
                {session_task}

                If this is not session 1:
                - Recall findings from memory (previous sessions)
                - Build on previous review work
                - Note any regressions or improvements

                Save findings to memory before context clears."""
            }],
            tools=[
                {"type": "memory_20250818", "name": "memory"},
                {"type": "text_editor_20250728", "name": "editor"}
            ],
            betas=["context-management-2025-06-27"],
            context_management={
                "edits": [{
                    "type": "clear_tool_uses_20250919",
                    "trigger": {"type": "input_tokens", "value": 150000},
                    "exclude_tools": []  # Let clearing work
                }]
            }
        )

        return response.content[0].text

# Multi-session review
reviewer = CodeReviewer("./my-large-repo")

# Session 1: Monday
review1 = reviewer.review_session("Review authentication module")

# Session 2: Wednesday (can reference Session 1 memory)
review2 = reviewer.review_session("Review payment processing")

# Session 3: Friday (can reference Sessions 1-2)
review3 = reviewer.review_session("Create final report with all findings")
```

---

## Optimization Decision Tree

**Q1**: Do you have more than 10 tools?
- YES → Implement tool search
- NO → Skip tool optimization

**Q2**: Is context growing indefinitely?
- YES → Implement context clearing
- NO → Monitor and prepare

**Q3**: Do you have 3+ dependent tool calls?
- YES → Consider programmatic calling
- NO → Use standard tool use

**Q4**: Is cost a primary concern?
- YES → Use cheaper model for summaries
- NO → Use same model

**Q5**: Do you need cross-session persistence?
- YES → Integrate memory tool
- NO → Optional

**Q6**: Using expensive model?
- YES → Consider effort parameter for Opus 4.5
- NO → Skip effort optimization

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Configure server-side context clearing
- [ ] Test with representative workload
- [ ] Measure token reduction
- [ ] Verify quality maintained

### Week 2: Enhancement
- [ ] Add memory tool integration
- [ ] Implement progressive disclosure pattern
- [ ] Add monitoring/logging
- [ ] Document configurations

### Week 3: Optimization
- [ ] Consider client-side compaction
- [ ] Implement tool search (if applicable)
- [ ] Optimize model selection
- [ ] Create cost tracking dashboard

### Week 4+: Production
- [ ] Deploy to production
- [ ] Monitor real-world performance
- [ ] Fine-tune parameters
- [ ] Plan quarterly optimizations

---

## Recommended Reading

- `server-side-context-editing.md`: Complete parameter reference
- `client-side-compaction-sdk.md`: SDK integration patterns
- `memory-tool-integration.md`: Persistence strategies
- `claude-advanced-tool-use.md` (related skill): Tool optimization
- `claude-cost-optimization.md` (related skill): Cost tracking

---

**Last Updated**: November 2025
**Focus**: Workflow patterns and production implementation
**Citation**: Official Anthropic documentation + production patterns
