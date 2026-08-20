#!/usr/bin/env node
import { fileURLToPath } from 'url';
import { runChannelPack } from './lib/channel-pack.mjs';

export function runCodeBuddyPack() {
  return runChannelPack({
    version: '3.0.0',
    packageName: 'fbs-bookwriter-v300-codebuddy',
    packageRootName: 'fbs-bookwriter',
    channelLabel: 'CodeBuddy Plugin',
    requiredDirs: [
      'codebuddy/',
      'workbuddy/',
      '.codebuddy/agents/',
      '.codebuddy/providers/',
      '.codebuddy-plugin/',
    ],
    coreFiles: [
      'codebuddy/channel-manifest.json',
      'workbuddy/channel-manifest.json',
      '.codebuddy/agents/fbs-team-lead.md',
      '.codebuddy/providers/provider-registry.yml',
      '.codebuddy-plugin/plugin.json',
      'releases/codebuddy-review-v3.0.0.md',
    ],
  });
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1] === fileURLToPath(import.meta.url)) {
  runCodeBuddyPack();
}
