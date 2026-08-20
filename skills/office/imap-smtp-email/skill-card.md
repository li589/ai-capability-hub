## Description: <br>
Read and send email via IMAP/SMTP, including checking unread messages, fetching content, searching mailboxes, marking messages, and sending emails with attachments across supported providers. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[gzlicanyi](https://clawhub.ai/user/gzlicanyi) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and agent users use this skill to manage mailbox workflows from an agent, including reading, searching, downloading attachments, marking messages, and sending email through user-configured IMAP and SMTP accounts. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill handles email credentials and mailbox contents. <br>
Mitigation: Use provider app passwords or authorization codes where available, store configuration with owner-only permissions, and install only when the account access is appropriate for the agent. <br>
Risk: Attachment and body-file workflows can read from or write to local files. <br>
Mitigation: Keep ALLOWED_READ_DIRS and ALLOWED_WRITE_DIRS narrow and review files before sending or downloading attachments. <br>
Risk: Dependency installation can change runtime behavior if dependencies are resolved loosely. <br>
Mitigation: Prefer reproducible installation from the included package-lock.json before using the skill. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/gzlicanyi/skills/imap-smtp-email) <br>
- [Publisher profile](https://clawhub.ai/user/gzlicanyi) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with shell commands and JSON command output from the mail scripts] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires Node.js, npm, provider credentials, and user-scoped file read/write directories for attachment workflows.] <br>

## Skill Version(s): <br>
0.0.19 (source: ClawHub release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
