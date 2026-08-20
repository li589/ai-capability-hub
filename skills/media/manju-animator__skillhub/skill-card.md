## Description: <br>
Manju Animator helps agents turn static comic storyboards into image-to-video prompts with camera movement, subtle motion details, tool settings, and stability guidance for Kling, Pika Labs, and Runway Gen-3. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[samwang-001](https://clawhub.ai/user/samwang-001) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Creators and developers use this skill to convert vertical comic storyboard shots into video-generation prompts and parameters while preserving character and scene stability. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Broad animation terms may trigger this skill during ordinary animation discussions where manju-style video prompting is not intended. <br>
Mitigation: Review the generated plan for relevance before using it, especially when the request did not explicitly involve comic storyboard image-to-video prompts. <br>
Risk: Generated prompt plans can still propose motion that destabilizes character faces, clothing, or scenes in downstream video tools. <br>
Mitigation: Prefer the artifact's low-motion settings and downgrade high-risk shots to subtle natural motion before production use. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/samwang-001/skills/manju-animator) <br>
- [Server-resolved GitHub provenance](https://github.com/samwang-001/manju-skills/tree/main/manju-animator) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, guidance, configuration] <br>
**Output Format:** [Markdown with structured per-shot prompt plans, tool parameters, and risk notes] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces image-to-video prompt guidance for 9:16 comic storyboard shots; no executable code, credential use, file access, or hidden data handling is indicated by the security evidence.] <br>

## Skill Version(s): <br>
0.1.0 (source: server release metadata; artifact frontmatter lists 1.0.0) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
