# Evidence Guard Rules

## Always Apply

### Factual Claims Must Have Sources

When stating any fact about the project (file locations, API behavior, library capabilities, configuration values), you MUST have verified it through one of these sources:
- Reading the actual file (Read tool)
- Searching the codebase (Grep/Glob/LSP)
- Running a command (Bash tool)
- Checking official documentation (WebFetch)
- User's explicit statement

If you have NOT verified a claim, you MUST mark it:
```
> **ASSUMPTION**: [claim]
> How to verify: [steps]
```

### No Fabricated Paths, APIs, or Results

- Never reference a file path you haven't confirmed exists
- Never cite an API method you haven't checked in docs or source
- Never report test results you haven't actually executed
- Never claim a build succeeded without running it

### Third-Party Library Verification

Before using any library API:
1. Confirm it's in the project's dependency list
2. Verify the installed version
3. Check the specific API exists (docs or source)

### Final Report Must Include Verification Status

Every task completion MUST include:
- **Verified**: Claims with evidence sources
- **Unverified**: Assumptions that need user confirmation
- **Remaining Risks**: What could go wrong
