/**
 * MarkText 汉化一键执行脚本
 * 用法: node hanhua-apply.js [MarkText安装目录]
 *
 * 示例:
 *   node hanhua-apply.js
 *   node hanhua-apply.js "D:\Program Files\MarkText"
 *
 * 默认安装目录: C:\Program Files\MarkText (Windows)
 *              /Applications/MarkText.app/Contents/Resources (macOS)
 */

'use strict';

const { execSync } = require('child_process');
const fs   = require('fs');
const path = require('path');
const os   = require('os');

// ── 1. 确定安装路径 ──────────────────────────────────────────
let installDir = process.argv[2];

if (!installDir) {
  if (process.platform === 'darwin') {
    installDir = '/Applications/MarkText.app/Contents/Resources';
  } else {
    // Windows: 尝试常见路径
    const candidates = [
      'D:\\Program Files\\MarkText',
      'C:\\Program Files\\MarkText',
      'C:\\Program Files (x86)\\MarkText',
    ];
    for (const c of candidates) {
      if (fs.existsSync(path.join(c, 'resources', 'app.asar'))) {
        installDir = c;
        break;
      }
    }
  }
}

if (!installDir) {
  console.error('[错误] 无法自动检测 MarkText 安装目录');
  console.error('请手动指定：node hanhua-apply.js "D:\\Program Files\\MarkText"');
  process.exit(1);
}

const asarPath   = path.join(installDir, 'resources', 'app.asar');
const backupPath = path.join(installDir, 'resources', 'app.asar.backup');

if (!fs.existsSync(asarPath)) {
  console.error('[错误] 未找到 app.asar: ' + asarPath);
  process.exit(1);
}

console.log('========================================');
console.log('      MarkText 汉化一键脚本');
console.log('========================================');
console.log('安装目录: ' + installDir);

// ── 2. 备份原始 asar ─────────────────────────────────────────
if (!fs.existsSync(backupPath)) {
  console.log('\n[1/5] 备份原始 app.asar...');
  fs.copyFileSync(asarPath, backupPath);
  console.log('      备份已保存: ' + backupPath);
} else {
  console.log('\n[1/5] 检测到已有备份，跳过备份步骤');
}

// ── 3. 解包 ──────────────────────────────────────────────────
const tempDir = path.join(os.tmpdir(), 'marktext-hanhua-' + Date.now());
console.log('\n[2/5] 解包 app.asar...');
try {
  execSync('asar extract "' + asarPath + '" "' + tempDir + '"', { stdio: 'inherit' });
} catch (e) {
  console.error('[错误] asar 解包失败。请确认已安装: npm install -g @electron/asar');
  process.exit(1);
}

// ── 4. 执行汉化 ───────────────────────────────────────────────
console.log('\n[3/5] 执行汉化...');
const coreScript = path.join(__dirname, 'hanhua-core.js');
process.env.HANHUA_UNPACKED_DIR = tempDir;
try {
  execSync('node "' + coreScript + '"', { stdio: 'inherit', env: process.env });
} catch (e) {
  console.error('[错误] 汉化脚本执行失败: ' + e.message);
  process.exit(1);
}

// ── 5. 重新打包 ───────────────────────────────────────────────
const outputAsar = path.join(os.tmpdir(), 'app.asar.patched');
console.log('\n[4/5] 重新打包...');
try {
  execSync('asar pack "' + tempDir + '" "' + outputAsar + '"', { stdio: 'inherit' });
} catch (e) {
  console.error('[错误] 打包失败: ' + e.message);
  process.exit(1);
}

// ── 6. 替换 ──────────────────────────────────────────────────
console.log('\n[5/5] 替换 app.asar（需要管理员权限）...');
try {
  fs.copyFileSync(outputAsar, asarPath);
} catch (e) {
  console.error('[错误] 替换失败！');
  console.error('  原因: ' + e.message);
  console.error('  解决方案: 以管理员身份运行本脚本，或手动复制：');
  console.error('  copy /Y "' + outputAsar + '" "' + asarPath + '"');
  process.exit(1);
}

// ── 7. 清理临时文件 ───────────────────────────────────────────
try {
  fs.rmSync(tempDir, { recursive: true, force: true });
  fs.unlinkSync(outputAsar);
} catch (_) {}

console.log('\n========================================');
console.log('  汉化完成！请重启 MarkText 查看效果。');
console.log('  如需恢复英文版，请将备份文件还原:');
console.log('  ' + backupPath + ' → ' + asarPath);
console.log('========================================\n');
