# Server-Side Context Editing Complete Reference

## Overview

Server-side context editing operates at the API level before Claude processes your request. The API automatically removes or summarizes content based on configured triggers, reducing input tokens before Claude sees the conversation history.

**Key Advantage**: Content removed before Claude processes it, so no disruption to Claude's reasoning process.

**Two Complementary Strategies**:
1. **clear_tool_uses_20250919**: Removes tool results (web search, file operations, etc.)
2. **clear_thinking_20251015**: Manages extended thinking blocks

**Required Beta Header**: `context-management-2025-06-27`

---

## Strategy 1: clear_tool_uses_20250919

### Purpose

Removes older tool results while preserving N most recent tool uses. Essential for tool-heavy workflows where web search results, file operations, or API responses accumulate.

### Complete Parameter Reference

```json
{
  "type": "clear_tool_uses_20250919",
  "trigger": {
    "type": "input_tokens" | "tool_uses",
    "value": number
  },
  "keep": {
    "type": "tool_uses",
    "value": number
  },
  "clear_at_least": {
    "type": "input_tokens",
    "value": number
  },
  "exclude_tools": ["tool_name_1", "tool_name_2"],
  "clear_tool_inputs": boolean
}
```

### Parameter Descriptions

#### 1. trigger (Required)

**trigger.type**:
- `"input_tokens"`: Trigger clearing when cumulative input tokens exceed value
  - Use when: Concerned about overall context size
  - Value: 50000-200000 (typical: 100000)
- `"tool_uses"`: Trigger clearing when number of tool uses exceed value
  - Use when: Tool count matters more than token size
  - Value: 5-50 (typical: 20)

**Example - Token-Based Trigger**:
```python
"trigger": {
    "type": "input_tokens",
    "value": 100000  # Clear when input exceeds 100K tokens
}
```

**Example - Tool-Count Trigger**:
```python
"trigger": {
    "type": "tool_uses",
    "value": 20  # Clear when more than 20 tool uses accumulated
}
```

#### 2. keep (Required)

**keep.type**: Only supports `"tool_uses"`

**keep.value**: How many of the most recent tool uses to preserve
- Recommended: 3-5
- Conservative: 10+ (fewer clearing events)
- Aggressive: 1-2 (maximum token reduction)

**Rationale**: Recent tool results usually most relevant; older results less important

**Example**:
```python
"keep": {
    "type": "tool_uses",
    "value": 3  # Always preserve most recent 3 tool uses
}
```

#### 3. clear_at_least (Optional)

**Purpose**: Minimum tokens to clear per event to avoid constant small clears

**Value**: Number of input tokens
- Recommended: 5000-10000 (batch clearing)
- If omitted: Clears only when keep items exceed

**Why**: Prevents inefficient clearing of small amounts

**Example**:
```python
"clear_at_least": {
    "type": "input_tokens",
    "value": 5000  # Only clear if removing 5K+ tokens
}
```

#### 4. exclude_tools (Optional)

**Purpose**: Tools never to clear results from

**Use Cases**:
- Web search results (often critical)
- Important lookups (database queries)
- File operations (recent changes)
- API calls with high-value responses

**Example - Web Search Excluded**:
```python
"exclude_tools": ["web_search"]
```

**Example - Multiple Tools**:
```python
"exclude_tools": [
    "web_search",
    "database_query",
    "file_read"
]
```

**Impact**: Results from excluded tools persist longer, other tools cleared normally

#### 5. clear_tool_inputs (Optional)

**Purpose**: Whether to clear the original tool request alongside results

**Default**: false (keep tool inputs, clear results)

**Values**:
- `false`: Remove results, keep "you called web_search with query X" context
- `true`: Remove both inputs and results (maximum token reduction)

**Trade-off**:
- false: Slightly larger (keeping inputs), but Claude sees what was searched
- true: More aggressive (remove all), less context about what was tried

**Example**:
```python
"clear_tool_inputs": true  # Remove both request and response
```

### When Each Strategy Is Best

| Parameter | Best For | Example |
|-----------|----------|---------|
| input_tokens trigger | Overall context size management | Budget-constrained project |
| tool_uses trigger | Tool-count management | 50+ web searches in session |
| keep=3 | Balance recent+cost | Most conversations |
| keep=1 | Aggressive cost reduction | Simple Q&A |
| keep=10 | Conservative (rare clearing) | Complex analysis |
| exclude web_search | Preserve search history | Research task |
| exclude database | Preserve queries | Data analysis |
| clear_tool_inputs=true | Maximum cost reduction | High-volume processing |

### Complete Python Example

```python
import anthropic

client = anthropic.Anthropic()

# Tool-heavy research workflow with context clearing
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Search for the latest breakthroughs in AI safety and summarize findings"
        }
    ],
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
    betas=["context-management-2025-06-27"],
    context_management={
        "edits": [
            {
                "type": "clear_tool_uses_20250919",
                # Trigger when input accumulates
                "trigger": {
                    "type": "input_tokens",
                    "value": 100000
                },
                # Always keep 3 most recent searches
                "keep": {
                    "type": "tool_uses",
                    "value": 3
                },
                # Only clear if 5K+ tokens can be removed
                "clear_at_least": {
                    "type": "input_tokens",
                    "value": 5000
                },
                # Never clear web_search results (research is key)
                "exclude_tools": ["web_search"],
                # Keep tool inputs for context
                "clear_tool_inputs": False
            }
        ]
    }
)

# Check if clearing was applied
if hasattr(response, 'context_management'):
    edits = response.context_management.get('applied_edits', [])
    for edit in edits:
        print(f"Clearing event: Removed {edit['cleared_tool_uses']} tools")
        print(f"Tokens freed: {edit['cleared_input_tokens']}")

print(response.content[0].text)
```

### Complete TypeScript Example

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
});

// Tool-heavy research workflow
const response = await client.beta.messages.create({
    model: 'claude-sonnet-4-5',
    max_tokens: 4096,
    messages: [{
        role: 'user',
        content: 'Search for latest AI safety research and compile findings'
    }],
    tools: [
        {
            type: 'web_search_20250305',
            name: 'web_search'
        },
        {
            type: 'web_fetch_20250305',
            name: 'web_fetch'
        }
    ],
    betas: ['context-management-2025-06-27'],
    context_management: {
        edits: [{
            type: 'clear_tool_uses_20250919',
            trigger: {
                type: 'input_tokens',
                value: 100000
            },
            keep: {
                type: 'tool_uses',
                value: 3
            },
            clear_at_least: {
                type: 'input_tokens',
                value: 5000
            },
            exclude_tools: ['web_search'],
            clear_tool_inputs: false
        }]
    }
});

// TypeScript type safe access
if ('context_management' in response && response.context_management) {
    const appliedEdits = response.context_management.applied_edits || [];
    appliedEdits.forEach(edit => {
        console.log(`Clearing event: ${edit.cleared_tool_uses} tools removed`);
        console.log(`Tokens freed: ${edit.cleared_input_tokens}`);
    });
}

console.log(response.content[0].type === 'text' ? response.content[0].text : '');
```

### Response Structure

When clearing is applied, response includes metrics:

```json
{
  "context_management": {
    "applied_edits": [
      {
        "type": "clear_tool_uses_20250919",
        "cleared_tool_uses": 8,
        "cleared_input_tokens": 50000
      }
    ]
  }
}
```

**Interpretation**:
- `cleared_tool_uses`: Number of tool results removed
- `cleared_input_tokens`: Input tokens freed up
- Helps measure efficiency

---

## Strategy 2: clear_thinking_20251015

### Purpose

Manages extended thinking blocks when using extended thinking mode. Preserves recent reasoning while clearing older thinking to save tokens.

**Important**: For cache optimization, you can preserve ALL thinking blocks (cache hits more valuable than token savings)

### Complete Parameter Reference

```json
{
  "type": "clear_thinking_20251015",
  "keep": {
    "type": "thinking_turns" | "all",
    "value": number  // only for "thinking_turns"
  }
}
```

### Parameter Descriptions

#### 1. keep.type

**"thinking_turns"**: Keep N most recent turns with thinking
```python
"keep": {
    "type": "thinking_turns",
    "value": 2  # Keep thinking from most recent 2 turns
}
```

**"all"**: Preserve all thinking blocks (for cache optimization)
```python
"keep": {
    "type": "all"
}
```

#### 2. keep.value (Only for thinking_turns)

**Recommended Values**:
- 1: Most aggressive (keep only latest thinking)
- 2: Balanced (keep recent 2 thinking blocks)
- 5: Conservative (keep recent 5 thinking blocks)
- Omit: Use "all" type instead

### When to Use Each Approach

| Scenario | Approach | Reason |
|----------|----------|--------|
| Thinking getting expensive | `thinking_turns: 2` | Balance reasoning visibility + tokens |
| Using prompt caching | `all` | Cache hits more valuable than token savings |
| Research-heavy task | `thinking_turns: 1-2` | Keep latest reasoning only |
| Multi-step problem solving | `thinking_turns: 5` | Preserve more analytical steps |

### Complete Python Example

```python
import anthropic

client = anthropic.Anthropic()

# Extended thinking with clearing
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Analyze this complex algorithm and explain the time complexity"
        }
    ],
    thinking={
        "type": "extended",
        "budget_tokens": 10000
    },
    betas=["context-management-2025-06-27"],
    context_management={
        "edits": [
            {
                "type": "clear_thinking_20251015",
                # Keep most recent 2 turns of thinking
                "keep": {
                    "type": "thinking_turns",
                    "value": 2
                }
            }
        ]
    }
)

print(response.content[0].text)
```

### Cache Optimization Example

```python
import anthropic

client = anthropic.Anthropic()

# Preserve thinking for cache hits (cache > tokens)
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Solve this multi-part reasoning problem step by step"
        }
    ],
    thinking={
        "type": "extended",
        "budget_tokens": 10000
    },
    betas=["context-management-2025-06-27"],
    context_management={
        "edits": [
            {
                "type": "clear_thinking_20251015",
                # Keep ALL thinking for cache optimization
                "keep": {
                    "type": "all"
                }
            }
        ]
    }
)

print(response.content[0].text)
```

### Complete TypeScript Example

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// Thinking block clearing with cache optimization
const response = await client.beta.messages.create({
    model: 'claude-sonnet-4-5',
    max_tokens: 4096,
    messages: [{
        role: 'user',
        content: 'Explain quantum computing principles with detailed reasoning'
    }],
    thinking: {
        type: 'extended',
        budget_tokens: 10000
    },
    betas: ['context-management-2025-06-27'],
    context_management: {
        edits: [{
            type: 'clear_thinking_20251015',
            keep: {
                type: 'all'  // Preserve for cache optimization
            }
        }]
    }
});

console.log(response.content[0].type === 'text' ? response.content[0].text : '');
```

---

## Combining Multiple Strategies

Both strategies work together. **Important**: Thinking must be listed first.

### Combined Example

```python
import anthropic

client = anthropic.Anthropic()

# Use both clearing strategies together
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[...],
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    thinking={"type": "extended", "budget_tokens": 10000},
    betas=["context-management-2025-06-27"],
    context_management={
        "edits": [
            # IMPORTANT: Thinking must be first
            {
                "type": "clear_thinking_20251015",
                "keep": {"type": "thinking_turns", "value": 2}
            },
            # Then tool clearing
            {
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 100000},
                "keep": {"type": "tool_uses", "value": 3}
            }
        ]
    }
)
```

---

## Cache Integration Considerations

### Impact on Caching

**Tool Result Clearing**:
- **Impact**: Removes content, may invalidate cached prefix
- **Cost**: Requires write cost recovery for new cache
- **Optimization**: Clear less frequently to maximize cache hits

**Thinking Block Preservation** (`keep: "all"`):
- **Impact**: Preserves content for caching
- **Benefit**: Cache hits on thinking tokens (valuable)
- **Recommendation**: When using caching, preserve thinking

### Strategy: Cache vs Tokens

| Priority | Approach | Rationale |
|----------|----------|-----------|
| Cost reduction | Keep cache, clear tools | Cache savings > token savings |
| Token efficiency | Clear aggressively | Focus on input reduction |
| Balanced | Clear tools, preserve thinking | Best of both |

---

## Strategy Selection Decision Tree

**Question 1**: Are you using tools (web search, file operations, etc.)?
- **Yes** → Use `clear_tool_uses_20250919`
- **No** → Skip to Q2

**Question 2**: Are you using extended thinking?
- **Yes** → Use `clear_thinking_20251015`
- **No** → Done

**Question 3**: How aggressively reduce tokens?
- **Maximum**: `keep=1-2`, `clear_tool_inputs=true`
- **Balanced**: `keep=3-5`, `clear_tool_inputs=false`
- **Conservative**: `keep=10+`, exclude important tools

**Question 4**: Using prompt caching?
- **Yes**: Preserve thinking (`keep: "all"`)
- **No**: Can clear more aggressively

---

## Troubleshooting

### Issue: Important information being cleared

**Problem**: Content is cleared but Claude needs it

**Solutions**:
1. Reduce trigger threshold (clear less frequently)
2. Increase `keep` parameter (preserve more items)
3. Add tool to `exclude_tools`
4. Combine with memory tool for preservation

### Issue: Clearing not happening

**Problem**: Expected clearing but no `applied_edits` in response

**Causes**:
- Input tokens below trigger threshold
- Request too short (single turn)
- All content protected by `keep` or `exclude_tools`

**Solution**: Send longer conversation to exceed threshold

### Issue: Token savings lower than expected

**Problem**: Not seeing 30-50% reduction

**Causes**:
- Trigger threshold too high (rare clearing)
- `keep` parameter too high (preserving too much)
- `exclude_tools` protecting large responses

**Solution**: Adjust parameters more aggressively

### Issue: Response quality degraded after clearing

**Problem**: Claude's answers worse after clearing

**Cause**: Lost important context during clearing

**Solutions**:
1. Exclude more tools from clearing
2. Combine with memory tool
3. Preserve more items (`keep` value)
4. Reduce trigger threshold (clear earlier)

---

## Best Practices

1. **Start Conservative**: Use `keep=5`, high threshold, then optimize
2. **Monitor Impact**: Check `applied_edits` in responses to measure savings
3. **Protect Critical Tools**: Use `exclude_tools` for research, lookups
4. **Combine Strategies**: Use both tool and thinking clearing for maximum effect
5. **Test Before Production**: Verify quality not affected in pilot
6. **Integrate Memory Tool**: For important information preservation
7. **Track Efficiency**: Measure token reduction vs response quality
8. **Version Your Config**: Document parameter choices for reproducibility

---

## Response Metrics Reference

```python
# Check clearing metrics
if response.context_management:
    for edit in response.context_management.applied_edits:
        if edit.type == "clear_tool_uses_20250919":
            print(f"Tool uses cleared: {edit.cleared_tool_uses}")
            print(f"Input tokens freed: {edit.cleared_input_tokens}")
            # Token reduction percentage
            reduction_pct = (edit.cleared_input_tokens / response.usage.input_tokens) * 100
            print(f"Reduction: {reduction_pct:.1f}%")
```

---

**Last Updated**: November 2025
**Reference Quality**: Comprehensive (all 6 parameters documented)
**Citation**: Official Anthropic documentation
