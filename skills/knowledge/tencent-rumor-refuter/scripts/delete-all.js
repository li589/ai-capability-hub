// 批量删除新表所有records
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DOC = 'dcxvtVHOVVO6bhUKnZto0EWQ6RPT6NiEXa_FounA_gmbp2xetDBc9y4rHUk8KnYFLuarcbvdrAO-qtp1-gw_iE-Q';
const SHEET = 'q979lj';
const BATCH = 100;

const ids = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../new-record-ids.json'), 'utf8'));
console.log('Total to delete:', ids.length);

let success = 0;
for (let i = 0; i < ids.length; i += BATCH) {
  const slice = ids.slice(i, i + BATCH);
  const payload = { docid: DOC, sheet_id: SHEET, record_ids: slice };
  const tmpFile = path.join(os.tmpdir(), `wecom-del-${i}.json`);
  fs.writeFileSync(tmpFile, JSON.stringify(payload), 'utf8');
  const tmpFilePosix = tmpFile.replace(/\\/g, '/');
  console.log(`Deleting ${slice.length} (${i+1}-${i+slice.length})...`);
  try {
    const cmd = `bash -c 'wecom-cli doc smartsheet_delete_records "$(cat "${tmpFilePosix}")"'`;
    const out = execSync(cmd, { encoding: 'utf8', maxBuffer: 50*1024*1024, shell: false });
    if (out.includes('"errcode": 0') || out.includes('\\"errcode\\": 0')) {
      success += slice.length;
      console.log('  ✓ ok');
    } else {
      console.log('  ✗', out.slice(0, 300));
    }
  } catch (e) {
    console.log('  ✗ err:', (e.stdout||e.message).slice(0, 300));
  } finally {
    try { fs.unlinkSync(tmpFile); } catch(_) {}
  }
}
console.log('Deleted:', success, '/', ids.length);
