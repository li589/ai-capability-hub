#!/usr/bin/env node

/**
 * PreToolUse Hook: UI Anti-Pattern Checker
 *
 * Intercepts Write/SearchReplace tool calls and warns when AI-flavored
 * UI patterns are detected in the content being written.
 *
 * Exit 0 = allow (with optional warning on stderr)
 * Exit 2 = block (only if severe anti-pattern found)
 *
 * Receives JSON via stdin:
 * { "tool_name": "Write", "params": { "file_path": "...", "file_content": "..." } }
 */

const ANTI_PATTERNS = [
  {
    id: 'purple-gradient',
    pattern: /from-purple-\d+.*to-(blue|indigo)-\d+/i,
    severity: 'warning',
    message: 'Detected purple-blue gradient. Consider using brand colors instead.'
  },
  {
    id: 'glassmorphism',
    pattern: /backdrop-blur-(xl|2xl).*bg-(white|black)\/[0-9]+/i,
    severity: 'warning',
    message: 'Detected glassmorphism pattern. Use solid surfaces for functional UI.'
  },
  {
    id: 'giant-hero',
    pattern: /text-(6xl|7xl|8xl|9xl)/i,
    severity: 'warning',
    message: 'Detected giant text size. Use text-2xl/text-3xl for app pages.'
  },
  {
    id: 'decorative-blob',
    pattern: /rounded-full\s+blur-(2xl|3xl).*opacity-[12]0/i,
    severity: 'warning',
    message: 'Detected decorative blob. Remove for cleaner functional UI.'
  },
  {
    id: 'all-large-radius',
    pattern: /rounded-(2xl|3xl)/g,
    severity: 'info',
    message: 'Large border-radius detected. Prefer rounded-md/rounded-lg for consistency.',
    threshold: 3
  }
];

async function main() {
  let input = '';

  try {
    for await (const chunk of process.stdin) {
      input += chunk;
    }
  } catch {
    // No stdin available, allow
    process.exit(0);
  }

  if (!input.trim()) {
    process.exit(0);
  }

  let context;
  try {
    context = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  // Collect content from Write (file_content) or SearchReplace (new_text, replacements[].new_text)
  let content = context?.params?.file_content || context?.params?.new_text || '';
  if (!content && Array.isArray(context?.params?.replacements)) {
    content = context.params.replacements
      .map(r => r.new_text || '')
      .join('\n');
  }

  if (!content) {
    process.exit(0);
  }

  // Only check files that look like UI code
  const filePath = context?.params?.file_path || '';
  const isUiFile = /\.(tsx|jsx|vue|svelte|html|css|scss)$/i.test(filePath);
  if (!isUiFile) {
    process.exit(0);
  }

  const warnings = [];

  for (const rule of ANTI_PATTERNS) {
    // Preserve original regex flags and ensure 'g' flag for matchAll counting
    const flags = rule.pattern.flags.includes('g')
      ? rule.pattern.flags
      : rule.pattern.flags + 'g';
    const regex = new RegExp(rule.pattern.source, flags);
    const matches = content.match(regex);
    if (matches) {
      if (!rule.threshold || matches.length >= rule.threshold) {
        warnings.push({
          pattern: rule.id,
          severity: rule.severity,
          message: rule.message,
          occurrences: matches.length
        });
      }
    }
  }

  if (warnings.length > 0) {
    const warningText = warnings
      .map(w => `[UI-TASTE-GUARD] ${w.severity.toUpperCase()}: ${w.message} (${w.occurrences}x)`)
      .join('\n');

    process.stderr.write(warningText + '\n');

    // Only block if severe patterns found (currently no blocking — warnings only)
    // To enable blocking, change severity to 'error' for any pattern above
    const hasErrors = warnings.some(w => w.severity === 'error');
    if (hasErrors) {
      process.exit(2);
    }
  }

  process.exit(0);
}

main().catch(() => process.exit(0));
