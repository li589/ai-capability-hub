#!/usr/bin/env node
import sdk from './log-sdk.mjs';

const SKILL_NAME = 'kry-business-analysis';
const log = sdk.logger.child({ tag: SKILL_NAME });

log.info('skill init', { skillName: SKILL_NAME });
console.error(`[init-report] 上报成功: skill=${SKILL_NAME}`);
