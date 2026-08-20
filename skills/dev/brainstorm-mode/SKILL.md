---
name: brainstorm-mode
description: Run an iterative brainstorming loop. ask focused questions, tighten scope, and end with a structured concept summary.
install_source: official
install_method: download
skill_id: official_bSmyPQ31
enabled_at: 1787232939198
version: 1.0.0
name_zh: 头脑风暴模式
---

# Brainstorm Mode

Activation: when user wants to brainstorm or says "brainstorm mode"
- Initial concept or idea could be entered as part of prompt.
- If initial concept is not entered, Ask user to share the initial idea
- Capture the concept and enter the loop

Loop:
1. Execute the `brainstorm` skill — ask focused questions, one or two at a time
2. Prioritize scope discovery: what's in, what's out
3. Summarize back periodically for confirmation
4. Continue until user signals they're done
5. Produce the structured summary per the brainstorm skill

Exit condition:
- When user says "done", "enough", "that's it", or otherwise signals completion
- mention all areas of low confidence in a bullet point list that user can choose to explore
    - if they choose to explore, enter loop again
- Output the final structured summary
- Exit brainstorming mode

Rules:
- Do not exit until user signals completion
- Do not write files unless explicitly requested
- If writing a markdown file is requested, write it under `/<project-root>/.agent/`
- Stay in the mode even if the user diverges — gently steer back
- Keep questions to one or two at a time
- Final output must be the structured summary before exiting
