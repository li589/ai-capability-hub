#!/usr/bin/env node

import { parseArgs, runCommand } from './fbs-connector-bridge.mjs';

const args = parseArgs(process.argv);
if (!process.argv.includes('--transport') && !process.argv.includes('--use-connector-config')) {
  args.transport = 'direct';
}

runCommand(args).catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
