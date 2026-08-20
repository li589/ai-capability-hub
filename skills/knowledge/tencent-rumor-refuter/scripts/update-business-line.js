// 批量更新新表的业务线字段
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DOC = 'dcxvtVHOVVO6bhUKnZto0EWQ6RPT6NiEXa_FounA_gmbp2xetDBc9y4rHUk8KnYFLuarcbvdrAO-qtp1-gw_iE-Q';
const SHEET = 'q979lj';
const BATCH = 30;

const updates = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../biz-updates.json'), 'utf8'));
console.log('Total to update:', updates.length);

let success = 0;
for (let i = 0; i < updates.length; i += BATCH) {
  const slice = updates.slice(i, i + BATCH);
  const records = slice.map(u => ({
    record_id: u.record_id,
    values: { '业务线': [{ text: u.businessLine }] },
  }));
  const payload = { docid: DOC, sheet_id: SHEET, key_type: 'CELL_VALUE_KEY_TYPE_FIELD_TITLE', records };
  const tmpFile = path.join(os.tmpdir(), `wecom-upd-${i}.json`);
  fs.writeFileSync(tmpFile, JSON.stringify(payload), 'utf8');
  const tmpFilePosix = tmpFile.replace(/\\/g, '/');
  console.log(`Batch ${Math.floor(i/BATCH)+1}: ${slice.length} (${i+1}-${i+slice.length})...`);
  try {
    const cmd = `bash -c 'wecom-cli doc smartsheet_update_records "$(cat "${tmpFilePosix}")"'`;
    const out = execSync(cmd, { encoding: 'utf8', maxBuffer: 50*1024*1024, shell: false });
    if (out.includes('\\"errcode\\": 0') || out.includes('"errcode": 0')) {
      success += slice.length;
      console.log(`  ✓ ok (${success}/${updates.length})`);
    } else {
      console.log(`  ✗`, out.slice(0, 400));
    }
  } catch (e) {
    console.log(`  ✗ err:`, (e.stdout||e.message||'').slice(0, 400));
  } finally {
    try { fs.unlinkSync(tmpFile); } catch(_) {}
  }
}
console.log('Done. Success:', success, '/', updates.length);
