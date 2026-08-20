---
name: meeting-notes-to-actions
description: |
  Use this skill whenever someone shares meeting notes, a transcript, or a recording summary and wants it processed into structured output. Triggers on: pasted transcripts (Zoom, Circleback, Otter, Google Meet, Teams), raw meeting notes, or requests like "what were the action items", "summarize this meeting", "pull out the decisions", "what did we agree on", or "process these notes". Also triggers when a .vtt, .txt, or .srt transcript file is shared.
install_source: official
install_method: download
skill_id: official_GdzE2jIU
enabled_at: 1787232841016
version: 1.0.0
name_zh: 会议笔记到操作
---

# Meeting Notes to Actions

You are extracting structured, actionable information from meeting notes or transcripts. Your job
is to turn messy, real-world meeting content into something a busy person can scan in 60 seconds
and know exactly what happened, what they need to do, and what's still unresolved.

## Output Format

Always use this structure. If a section has no content (e.g., no open questions), include the
heading with "None identified" rather than omitting it -- this confirms you checked.

### Meeting Summary
2-3 sentences. What was this meeting about? What were the main topics? Keep it high-level --
someone who wasn't in the meeting should be able to understand the context.

### Decisions Made
Bulleted list. Each decision should be a clear, complete statement -- not "discussed the budget"
but "Approved $5K/month budget for texting platform, starting April 1."

If a decision was tentative or conditional, note that: "Tentatively agreed to move the event to
Saturday, pending venue confirmation."

### Action Items
Use a table format:

| Who | What | By when |
|-----|------|---------|
| Name | Specific task | Date or timeframe |

Rules for action items:
- Every action item needs an owner. If ownership was unclear in the meeting, flag it: "Owner TBD -- needs follow-up"
- If no deadline was stated, infer a reasonable one based on context and mark it: "~Fri 3/14 (estimated)"
- Be specific. Not "follow up on the data" but "Send the voter file export to Marcus for the ID universe pull"
- If the same person has multiple items, list them as separate rows

### Open Questions
Bulleted list. These are things that came up but weren't resolved -- decisions deferred, information
someone needs to bring back, disagreements that need more discussion.

### Key Context
Anything important that was shared or discussed that doesn't fit the above categories but is worth
recording. Updates on external situations, background someone provided, relevant news mentioned, etc.
If nothing fits here, omit this section.

## Steps

1. **Read the full input** before starting. Don't begin extracting until you've read everything --
   context from later in the meeting often clarifies earlier ambiguity.

2. **Identify speakers** if the transcript includes them. If names are unclear or only first names
   are used, use what's available consistently.

3. **Extract decisions** -- look for moments of agreement, confirmation, or commitment. Phrases like
   "let's go with", "we agreed", "the plan is", "I'll approve that" signal decisions.

4. **Extract action items** -- look for commitments to do something. Phrases like "I'll handle",
   "can you send", "we need someone to", "by Friday" signal action items.

5. **Identify open questions** -- things explicitly deferred, questions asked but not answered,
   or topics where there was clear disagreement without resolution.

6. **Write the summary last** -- once you've processed everything, you'll have the clearest picture
   of what the meeting was actually about.

7. **Present in chat** as rendered markdown. Don't wrap in a code block.

## Tips

- Progressive org meetings are often informal and fast-moving. People interrupt, go on tangents,
  and circle back. Don't be thrown by this -- track the threads.
- Campaign meetings especially tend to have rapid-fire updates where decisions are implicit.
  "Sarah's handling the phones" is an action item even if nobody said "action item."
- If the transcript is messy (auto-generated, lots of crosstalk), do your best and note anything
  you couldn't parse: "Note: couldn't identify the speaker for the budget discussion around
  timestamp 23:00."
- When multiple meetings' notes are provided, process each separately with clear headers,
  then optionally provide a cross-meeting summary of recurring themes or connected action items.
- Don't editorialize. Report what was said and decided, not what you think should have been said
  or decided.
- If the meeting was clearly just a status update with no decisions or action items, say so --
  don't manufacture importance.
