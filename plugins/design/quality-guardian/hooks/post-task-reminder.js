#!/usr/bin/env node

/**
 * Stop Hook: Post-Task Verification Reminder
 *
 * Runs when the agent stops responding. Checks if the response likely
 * involved code changes and reminds about verification if needed.
 *
 * Exit 0 = allow agent to stop
 * Exit 2 = force agent to continue (not used here — reminders only)
 *
 * Receives JSON via stdin with conversation context.
 */

async function main() {
  let input = '';

  try {
    for await (const chunk of process.stdin) {
      input += chunk;
    }
  } catch {
    process.exit(0);
  }

  if (!input.trim()) {
    process.exit(0);
  }

  // Parse context
  let context;
  try {
    context = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  const response = context?.response || context?.message || '';

  // Check if code files were likely modified in this conversation
  const codeChangeSignals = [
    /created?\s+(src|lib|app|components)\//i,
    /wrote\s+.*\.(tsx?|jsx?|py|rs|go|vue|svelte)/i,
    /modified\s+.*\.(tsx?|jsx?|py|rs|go|vue|svelte)/i,
    /updated?\s+.*\.(tsx?|jsx?|py|rs|go|vue|svelte)/i
  ];

  const hasCodeChanges = codeChangeSignals.some(p => p.test(response));

  // Check if verification was mentioned
  const verificationSignals = [
    /verification\s+(report|result|status)/i,
    /npm\s+run\s+(lint|test|build)/i,
    /npx\s+tsc/i,
    /cargo\s+(check|test|clippy)/i,
    /pytest/i,
    /go\s+(test|vet)/i
  ];

  const hasVerification = verificationSignals.some(p => p.test(response));

  if (hasCodeChanges && !hasVerification) {
    // Remind the agent about verification — output to stderr (non-blocking)
    process.stderr.write(
      '[VERIFICATION-RUNNER] Code changes detected but no verification report found. ' +
      'Consider running lint, typecheck, test, or build commands before completing.\n'
    );
  }

  // Never block — just warn
  process.exit(0);
}

main().catch(() => process.exit(0));
