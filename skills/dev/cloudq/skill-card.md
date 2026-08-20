## Description:

CloudQ helps agents answer multi-cloud operations questions, visualize and assess cloud architectures, inspect resources, optimize cost, and route Tencent Cloud Smart Advisor workflows.

This skill is ready for commercial/non-commercial use.

## Publisher:

[1ncludesteven](https://clawhub.ai/user/1ncludesteven)

### License/Terms of Use:

MIT-0

## Use Case:

Developers, cloud operators, and external users use CloudQ to ask cloud and multi-cloud operations questions, inspect Tencent Cloud Smart Advisor architectures, assess risks, run AI operations workflows, and receive Markdown answers from CloudQ services.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: The skill stores Tencent Cloud credentials locally under ~/.tencent-cloudq/credential.json.

Mitigation: Use a dedicated least-privilege Tencent Cloud subaccount and periodically remove the credential file when the skill is no longer needed.

Risk: The skill can create, attach policies to, assume, and delete CAM roles as part of CloudQ setup and cleanup flows.

Mitigation: Review each role or policy operation before execution and proceed only after explicit user approval.

Risk: The skill sends cloud-operations questions and credential-backed requests to Tencent Cloud and CloudQ endpoints.

Mitigation: Install only in environments where those network calls and CloudQ credential use are acceptable.

## Reference(s):

- [CloudQ ClawHub release page](https://clawhub.ai/1ncludesteven/skills/cloudq)
- [Publisher profile: 1ncludesteven](https://clawhub.ai/user/1ncludesteven)
- [CloudQChatCompletions API reference](references/api/CloudQChatCompletions.md)
- [Tencent Cloud Smart Advisor console](https://console.cloud.tencent.com/advisor)
- [CloudQ console](https://console.cloud.tencent.com/advisor/cloudq)
- [Tencent Cloud CloudQ article](https://cloud.tencent.com/developer/article/2645159)

## Skill Output:

**Output Type(s):** [text, markdown, shell commands, configuration, guidance, API calls]

**Output Format:** [Markdown responses with inline shell commands and JSON API status payloads]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Remote CloudQ responses may include console links, task status, error codes, and cloud-operations guidance.]

## Skill Version(s):

1.9.0 (source: frontmatter and server release evidence)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
