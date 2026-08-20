# Verification Runner Rules

## Always Apply — After Any Code Modification

### Run Available Checks After Changes

After modifying any code file, attempt to run (in order):
1. **Lint** — Fast syntax/style feedback
2. **TypeCheck** — Type safety verification
3. **Test** — Logic correctness (targeted tests first)
4. **Build** — Integration correctness

Skip only if the check is genuinely unavailable (no command exists) or the environment prevents it (no database, no network). Always state WHY a check was skipped.

### Report Only What Actually Ran

- PASS: You ran it and it passed. Include the command and output summary.
- FAIL: You ran it and it failed. Include the error and your fix.
- SKIP: You couldn't run it. Include the reason and manual alternative.

NEVER claim a check passed without running it. This is a critical integrity rule.

### Fix Before Proceeding

When a check fails:
1. Read the actual error message carefully
2. Fix the root cause (don't suppress or ignore)
3. Re-run the specific check
4. Only proceed when it passes or you have a documented reason to continue

### Browser Verification for UI Changes

For web/UI changes, when a dev server is available:
- Verify the page is not blank
- Check console for errors
- Verify text is readable (no overlap, no truncation)
- Test interactive elements work
- Check at desktop (1280px) and mobile (375px) widths

If browser is unavailable, provide manual verification steps.

### What NOT to Do

- Don't add `// @ts-ignore` to suppress type errors
- Don't disable lint rules to pass linting
- Don't modify tests to make them pass (fix the code instead)
- Don't skip verification silently
