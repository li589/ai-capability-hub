#!/usr/bin/env node

/**
 * Qoder Quality Suite — Self-Check Script
 * 
 * Validates the plugin directory structure, file integrity, and content quality.
 * Run: node scripts/self-check.js
 * 
 * Checks:
 * 1. Directory structure completeness
 * 2. plugin.json validity
 * 3. All SKILL.md files have required frontmatter
 * 4. All rule files exist
 * 5. Reference files are properly linked
 * 6. No broken internal links
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const errors = [];
const warnings = [];
const passed = [];

function check(condition, message, isWarning = false) {
  if (condition) {
    passed.push(`✓ ${message}`);
  } else if (isWarning) {
    warnings.push(`⚠ ${message}`);
  } else {
    errors.push(`✗ ${message}`);
  }
}

function fileExists(relativePath) {
  return fs.existsSync(path.join(ROOT, relativePath));
}

function readFile(relativePath) {
  const fullPath = path.join(ROOT, relativePath);
  if (!fs.existsSync(fullPath)) return null;
  return fs.readFileSync(fullPath, 'utf-8');
}

function hasFrontmatter(content, requiredFields) {
  if (!content) return false;
  const normalized = content.replace(/\r\n/g, '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return false;
  const fm = match[1];
  return requiredFields.every(f => fm.includes(`${f}:`));
}

// === 1. Directory Structure ===
console.log('\n📁 Checking directory structure...\n');

const requiredDirs = [
  '.qoder-plugin',
  'skills/evidence-guard',
  'skills/evidence-guard/references',
  'skills/context-cartographer',
  'skills/context-cartographer/references',
  'skills/ui-taste-guard',
  'skills/ui-taste-guard/references',
  'skills/verification-runner',
  'skills/verification-runner/references',
  'rules',
  'agents',
  'commands',
  'hooks',
  'assets',
];

requiredDirs.forEach(dir => {
  check(
    fs.existsSync(path.join(ROOT, dir)),
    `Directory exists: ${dir}`
  );
});

// === 2. Plugin Manifest ===
console.log('📋 Checking plugin manifest...\n');

const pluginJson = readFile('.qoder-plugin/plugin.json');
check(pluginJson !== null, 'plugin.json exists');

if (pluginJson) {
  try {
    const manifest = JSON.parse(pluginJson);
    check(manifest.name === 'quality-guardian', 'Plugin name is correct');
    check(manifest.version !== undefined, 'Version is defined');
    check(manifest.description !== undefined, 'Description is defined');
    check(manifest.skills === './skills/', 'Skills path is correct');
    check(manifest.rules === './rules/', 'Rules path is correct');
    check(manifest.agents === './agents/', 'Agents path is correct');
    check(manifest.commands === './commands/', 'Commands path is correct');
    check(manifest.hooks === './hooks/hooks.json', 'Hooks path is correct');
    if (manifest.logo) {
      check(fileExists(manifest.logo.replace('./', '')), `Logo file exists: ${manifest.logo}`);
    }
  } catch (e) {
    errors.push(`✗ plugin.json is invalid JSON: ${e.message}`);
  }
}

// === 3. Skill Files ===
console.log('📝 Checking skill files...\n');

const skills = [
  { name: 'evidence-guard', ref: 'references/evidence-ledger-examples.md' },
  { name: 'context-cartographer', ref: 'references/context-mapping-examples.md' },
  { name: 'ui-taste-guard', ref: 'references/anti-pattern-catalog.md' },
  { name: 'verification-runner', ref: 'references/verification-templates.md' },
];

skills.forEach(skill => {
  const skillPath = `skills/${skill.name}/SKILL.md`;
  const refPath = `skills/${skill.name}/${skill.ref}`;

  check(fileExists(skillPath), `SKILL.md exists: ${skillPath}`);
  check(fileExists(refPath), `Reference file exists: ${refPath}`);

  const content = readFile(skillPath);
  check(
    hasFrontmatter(content, ['name', 'description']),
    `Frontmatter has name + description: ${skillPath}`
  );

  if (content) {
    const lines = content.split('\n').length;
    check(
      lines <= 500,
      `SKILL.md under 500 lines (${lines} lines): ${skillPath}`
    );

    // Check for broken internal links
    const linkMatches = content.matchAll(/\[.*?\]\((.*?)\)/g);
    for (const match of linkMatches) {
      const link = match[1];
      if (!link.startsWith('http') && !link.startsWith('#')) {
        const resolvedPath = path.join(ROOT, 'skills', skill.name, link);
        check(
          fs.existsSync(resolvedPath),
          `Internal link resolves: ${link} in ${skillPath}`
        );
      }
    }
  }
});

// === 4. Rule Files ===
console.log('📏 Checking rule files...\n');

const ruleFiles = [
  'rules/evidence-guard.md',
  'rules/context-cartographer.md',
  'rules/ui-taste-guard.md',
  'rules/verification-runner.md',
];

ruleFiles.forEach(rule => {
  check(fileExists(rule), `Rule file exists: ${rule}`);
  const content = readFile(rule);
  check(content && content.length > 100, `Rule has content: ${rule}`);
});

// === 5. Agent Files ===
console.log('🤖 Checking agent files...\n');

check(fileExists('agents/quality-reviewer.md'), 'Quality reviewer agent exists');

// === 6. Command Files ===
console.log('⚡ Checking command files...\n');

check(fileExists('commands/quality-check.md'), 'Quality check command exists');

// === 7. Hook Files ===
console.log('🪝 Checking hook files...\n');

check(fileExists('hooks/hooks.json'), 'hooks.json exists');
check(fileExists('hooks/check-ui-anti-patterns.js'), 'UI anti-pattern hook exists');
check(fileExists('hooks/post-task-reminder.js'), 'Post-task reminder hook exists');

const hooksJson = readFile('hooks/hooks.json');
if (hooksJson) {
  try {
    const hooks = JSON.parse(hooksJson);
    check(hooks.hooks !== undefined, 'hooks.json has hooks config');
    check(hooks.hooks.PreToolUse !== undefined, 'PreToolUse hook configured');
    check(hooks.hooks.Stop !== undefined, 'Stop hook configured');
  } catch (e) {
    errors.push(`✗ hooks/hooks.json is invalid JSON: ${e.message}`);
  }
}

// === 8. Config Template ===
console.log('⚙️  Checking config template...\n');

const configTemplate = readFile('config.template.json');
check(configTemplate !== null, 'config.template.json exists');

if (configTemplate) {
  try {
    const config = JSON.parse(configTemplate);
    check(config.qualitySuite !== undefined, 'Config has qualitySuite section');
    check(config.qualitySuite.maxContextFiles !== undefined, 'maxContextFiles defined');
    check(config.qualitySuite.enableEvidenceLedger !== undefined, 'enableEvidenceLedger defined');
    check(config.qualitySuite.enableUiAntiAiReview !== undefined, 'enableUiAntiAiReview defined');
  } catch (e) {
    errors.push(`✗ config.template.json is invalid JSON: ${e.message}`);
  }
}

// === Summary ===
console.log('\n' + '═'.repeat(50));
console.log('\n📊 Self-Check Summary\n');

passed.forEach(p => console.log(`  ${p}`));
if (warnings.length) {
  console.log('');
  warnings.forEach(w => console.log(`  ${w}`));
}
if (errors.length) {
  console.log('');
  errors.forEach(e => console.log(`  ${e}`));
}

console.log(`\n  Results: ${passed.length} passed, ${warnings.length} warnings, ${errors.length} errors\n`);

if (errors.length > 0) {
  console.log('❌ Self-check FAILED. Fix the errors above.\n');
  process.exit(1);
} else {
  console.log('✅ Self-check PASSED. Plugin structure is valid.\n');
  process.exit(0);
}
