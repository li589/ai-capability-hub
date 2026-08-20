import { createRequire } from 'module';
import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
const require = createRequire(import.meta.url);

const global = execSync('npm root -g').toString().trim();
const file = path.join(global, '@keruyun/cli/bin/sdk.mjs');

if (!fs.existsSync(file)) {
  console.log('请先执行 kry-cli 安装命令');
  process.exit(1);
}

const sdk = require(file);

export default sdk;
