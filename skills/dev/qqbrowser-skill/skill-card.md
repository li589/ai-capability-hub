## Description:

Browser automation CLI for AI agents that helps agents open, navigate, interact with, extract data from, screenshot, download from, and replay tasks on websites.

This skill is ready for commercial/non-commercial use.

## Publisher:

[qqbrowserteam](https://clawhub.ai/user/qqbrowserteam)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and AI agent operators use this skill to automate real browser tasks such as navigation, form interaction, screenshots, downloads, structured extraction, and reusable playbook replay.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: The skill can control a browser for real web tasks, including posting, purchasing, deleting, messaging, and submitting forms.

Mitigation: Require explicit user approval before side-effecting actions and prefer drafts, test data, or manual review for non-idempotent workflows.

Risk: Reusable playbooks can replay browser actions and may repeat side effects if run without review.

Mitigation: Review saved playbooks before reuse and verify replay behavior safely before using live targets.

Risk: The skill supports downloads and JavaScript-based extraction on web pages that may contain sensitive information.

Mitigation: Use downloads and JavaScript extraction only on intended pages and avoid exposing sensitive page content unless needed for the task.

## Reference(s):

- [ClawHub Skill Page](https://clawhub.ai/qqbrowserteam/skills/qqbrowser-skill)
- [QQ Browser Homepage](https://browser.qq.com/)
- [PyPI Package](https://pypi.org/project/qqbrowser-skill/)
- [QQBrowserSkillReport](https://bak.res.qq.com/nav/qqbrowser_skills/QQBrowserSkillReport.html)
- [Command Reference](references/commands.md)
- [Session Lifecycle](references/session-lifecycle.md)
- [Playbook Guide](references/playbook.md)

## Skill Output:

**Output Type(s):** [Shell commands, Code, Configuration, Markdown, JSON, Guidance]

**Output Format:** [Markdown guidance with inline shell commands, JSON playbooks, and browser task results]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [May produce browser screenshots, downloaded files, structured page data, and reusable playbook files when the user requests those actions.]

## Skill Version(s):

1.0.7 (source: server release metadata)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
