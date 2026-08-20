// 通过 git bash + cat 文件方式传JSON
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DOC = 'dcxvtVHOVVO6bhUKnZto0EWQ6RPT6NiEXa_FounA_gmbp2xetDBc9y4rHUk8KnYFLuarcbvdrAO-qtp1-gw_iE-Q';
const SHEET = 'q979lj';
const BATCH_SIZE = 30;

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../ima-import-draft.json'), 'utf8'));
console.log('Total to push:', data.length);

const startIndex = 1;

function buildRecord(item) {
  const values = {
    '谣言内容': [{ type: 'text', text: item.title }],
    '业务线': [{ text: item.businessLine }],
    '分级': [{ text: item.level || '未分级' }],
  };
  if (item.infoPoint) values['谣言信息点'] = [{ text: item.infoPoint }];
  if (item.reason) values['口径应对'] = [{ type: 'text', text: item.reason }];
  return { values };
}

let success = 0, failed = [];

for (let i = startIndex; i < data.length; i += BATCH_SIZE) {
  const batch = data.slice(i, i + BATCH_SIZE);
  const payload = { docid: DOC, sheet_id: SHEET, records: batch.map(buildRecord) };
  const tmpFile = path.join(os.tmpdir(), `wecom-payload.json`);
  fs.writeFileSync(tmpFile, JSON.stringify(payload), 'utf8');
  const tmpFilePosix = tmpFile.replace(/\\/g, '/');

  console.log(`Batch ${Math.floor(i/BATCH_SIZE)+1}: ${batch.length} records (${i+1}-${i+batch.length})...`);
  try {
    // 用 bash -c "wecom-cli doc smartsheet_add_records \"$(cat file)\""
    const cmd = `bash -c 'wecom-cli doc smartsheet_add_records "$(cat "${tmpFilePosix}")"'`;
    const out = execSync(cmd, { encoding: 'utf8', maxBuffer: 50*1024*1024, shell: false });
    const m = out.match(/"errcode":\s*(\d+)/);
    if (m && m[1] === '0') {
      success += batch.length;
      console.log(`  ✓ ok (cumulative: ${success+1}/${data.length})`);
    } else {
      console.log(`  ✗ failed:`, out.slice(0, 400));
      failed.push({ idx: i, err: out.slice(0, 400) });
    }
  } catch (e) {
    console.log(`  ✗ exec err:`, (e.stdout||e.message||'').slice(0, 400));
    failed.push({ idx: i, err: (e.stdout||e.message||'').slice(0, 400) });
  }
}

console.log('\n===== Done =====');
console.log(`Success: ${success}/${data.length-startIndex} (+ 1 test record = ${success+1} total in sheet)`);
console.log('Failed:', failed.length);
if (failed.length) console.log(JSON.stringify(failed.slice(0,2), null, 2));
