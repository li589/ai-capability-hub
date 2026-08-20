/**
 * MarkText 恢复英文版脚本
 * 用法: node hanhua-restore.js [MarkText安装目录]
 */

'use strict';

const fs   = require('fs');
const path = require('path');

let installDir = process.argv[2];

if (!installDir) {
  const candidates = [
    'D:\\Program Files\\MarkText',
    'C:\\Program Files\\MarkText',
    'C:\\Program Files (x86)\\MarkText',
    '/Applications/MarkText.app/Contents/Resources',
  ];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, 'resources', 'app.asar'))) {
      installDir = c;
      break;
    }
  }
}

if (!installDir) {
  console.error('[错误] 无法检测 MarkText 安装目录，请手动指定：');
  console.error('node hanhua-restore.js "D:\\Program Files\\MarkText"');
  process.exit(1);
}

const asarPath   = path.join(installDir, 'resources', 'app.asar');
const backupPath = path.join(installDir, 'resources', 'app.asar.backup');

if (!fs.existsSync(backupPath)) {
  console.error('[错误] 未找到备份文件: ' + backupPath);
  console.error('无法恢复，请重新安装 MarkText。');
  process.exit(1);
}

console.log('[恢复] 将备份文件还原为原始英文版...');
try {
  fs.copyFileSync(backupPath, asarPath);
  console.log('[恢复] 完成！请重启 MarkText。');
} catch (e) {
  console.error('[错误] 恢复失败（需要管理员权限）: ' + e.message);
  console.error('请以管理员身份运行，或手动执行：');
  console.error('copy /Y "' + backupPath + '" "' + asarPath + '"');
  process.exit(1);
}
