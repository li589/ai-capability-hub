// 把 migrated-records.json 推到新表
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DOC = 'dcxvtVHOVVO6bhUKnZto0EWQ6RPT6NiEXa_FounA_gmbp2xetDBc9y4rHUk8KnYFLuarcbvdrAO-qtp1-gw_iE-Q';
const SHEET = 'q979lj';
const BATCH = 30;

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../migrated-records.json'), 'utf8'));
console.log('Total to push:', data.length);

function buildRecord(item) {
  const values = {
    '谣言内容': [{ type: 'text', text: item.title }],
    '分级': [{ text: item.level }],
  };
  if (item.infoPoint) values['谣言信息点'] = [{ text: item.infoPoint }];
  if (item.reason) values['口径应对'] = [{ type: 'text', text: item.reason }];
  if (item.link) values['代表链接'] = [{ type: 'text', text: item.link }];
  return { values };
}

let success = 0, failed = [];

for (let i = 0; i < data.length; i += BATCH) {
  const batch = data.slice(i, i + BATCH);
  const payload = { docid: DOC, sheet_id: SHEET, records: batch.map(buildRecord) };
  const tmpFile = path.join(os.tmpdir(), `wecom-push-${i}.json`);
  fs.writeFileSync(tmpFile, JSON.stringify(payload), 'utf8');
  const tmpFilePosix = tmpFile.replace(/\\/g, '/');
  console.log(`Batch ${Math.floor(i/BATCH)+1}: ${batch.length} records (${i+1}-${i+batch.length})...`);
  try {
    const cmd = `bash -c 'wecom-cli doc smartsheet_add_records "$(cat "${tmpFilePosix}")"'`;
    const out = execSync(cmd, { encoding: 'utf8', maxBuffer: 50*1024*1024, shell: false });
    if (out.includes('\\"errcode\\": 0') || out.includes('"errcode": 0')) {
      success += batch.length;
      console.log(`  ✓ ok (cumulative ${success}/${data.length})`);
    } else {
      console.log(`  ✗`, out.slice(0, 400));
      failed.push({ idx: i, err: out.slice(0, 400) });
    }
  } catch (e) {
    console.log(`  ✗ err:`, (e.stdout||e.message||'').slice(0, 400));
    failed.push({ idx: i, err: (e.stdout||e.message||'').slice(0, 400) });
  } finally {
    try { fs.unlinkSync(tmpFile); } catch(_) {}
  }
}
console.log('\n===== Done =====');
console.log('Success:', success, '/', data.length);
console.log('Failed:', failed.length);
