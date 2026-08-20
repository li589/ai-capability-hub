## Description: <br>
AndonQ is a Tencent Cloud smart customer-service agent for ticket lookup, requirement management, product Q&A, and cloud resource queries through the AndonQ gateway. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[cyuxlif](https://clawhub.ai/user/cyuxlif) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Tencent Cloud users and support-oriented agents use this skill to answer cloud product questions, inspect tickets and requirements, and query cloud resource information without switching to a separate support console. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill may ask users to provide a Tencent Cloud OAuth2 temporary code, which should be treated as a credential. <br>
Mitigation: Prefer the local terminal binding flow, keep the code out of chat when possible, store it only in the local auth file with restricted permissions, and mask it whenever displaying status. <br>
Risk: The skill connects to Tencent Cloud support and resource-query services using the user's authorized context. <br>
Mitigation: Install only when this Tencent Cloud access is intended, and avoid using the skill with accounts or resource context that should not be exposed to the AndonQ gateway. <br>


## Reference(s): <br>
- [ChatCompletionsAndonQ API reference](references/api/ChatCompletionsAndonQ.md) <br>
- [AndonQ gateway](https://andon.cloud.tencent.com) <br>
- [Tencent Cloud](https://cloud.tencent.com) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Shell commands, Guidance] <br>
**Output Format:** [Markdown responses with inline shell commands and streamed service output] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires Python 3 and a Tencent Cloud OAuth2 temporary code stored locally with restricted file permissions.] <br>

## Skill Version(s): <br>
2.0.1 (source: frontmatter and server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
