---
name: audio-meeting-summary
description: Transcribe an audio file and turn it into meeting minutes. Use when the user wants spoken audio converted into a meeting-style summary with decisions, action items, open questions, and a readable meeting record.
install_source: official
install_method: download
skill_id: official_jDR2euMF
enabled_at: 1787232832343
version: 1.0.0
name_zh: 音频会议摘要
---

# Audio Meeting Summary

First transcribe the audio, then reshape the transcript into meeting minutes.

## Workflow

1. Use the `audio-transcription` workflow to produce the transcript from the audio file in `/Users/ishikawaryuusuke/Desktop/aidev/aidevforclaude`.
2. Read the transcript fully before summarizing so the meeting flow is not distorted by partial extraction.
3. Produce a meeting-style output in Japanese unless the user requests another language.
4. Keep the structure flexible. Do not invent sections that are unsupported by the source audio.

## Default Output Shape

- Title or short label for the meeting if it is inferable.
- Summary of the discussion.
- Decisions or confirmed points, if any.
- Action items or follow-ups, if any.
- Open questions or unresolved topics, if any.

## Guardrails

- If speaker identities are unclear, say so instead of assigning names.
- If the audio is not actually a meeting, say that the requested format may not fit cleanly and adapt lightly instead of forcing a fake meeting record.
- Separate what was explicitly said from what is inferred.

## Command

```bash
cd /Users/ishikawaryuusuke/Desktop/aidev/aidevforclaude
npm run transcribe -- ./audio/example.m4a --language ja
```
