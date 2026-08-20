/**
 * 把 references/rumor-database.md 转成 IMA 批量导入的 JSON 草稿
 * 输出：ima-import-draft.json（数组，每元素一条谣言笔记）
 *
 * 字段约定（IMA 笔记 content 用 markdown，便于阅读）：
 *   - title:       谣言一句话标题
 *   - businessLine: WXG / IEG / PCG / CSIG / MA / 集团 / 老板
 *   - level:        完全虚假 / 部分失实 / 不利表述 / 恶意解读 / 其他
 *   - infoPoint:    业务造谣 / 隐私和安全 / 垄断 / ...
 *   - reason:       辟谣理由（原文）
 *   - keywords:     抽取标题里的关键词（用于召回）
 *   - tags:         ["腾讯辟谣", 业务线, 分级]
 *   - content:      markdown 拼装好的笔记正文（直接上传到 IMA）
 */
const fs = require('fs');
const path = require('path');

const MD_PATH = path.resolve(__dirname, '..', 'references/rumor-database.md');
const OUT_PATH = path.resolve(__dirname, '..', 'ima-import-draft.json');

const md = fs.readFileSync(MD_PATH, 'utf8');
const lines = md.split(/\r?\n/);

// 业务线归一化
function normalizeSection(name) {
  const n = name.trim().replace(/\s+/g, '').replace(/业务$/, '');
  if (/WXG/i.test(n)) return 'WXG';
  if (/IEG/i.test(n)) return 'IEG';
  if (/PCG/i.test(n)) return 'PCG';
  if (/CSIG/i.test(n)) return 'CSIG';
  if (/MA/i.test(n))  return 'MA';
  if (/集团/.test(n)) return '集团';
  if (/老板/.test(n)) return '老板';
  return n;
}

// 抽取关键词（粗粒度：去掉助词/标点后的中文/英文 token）
function extractKeywords(title) {
  const stop = new Set(['的','是','了','和','与','或','在','吗','呢','为','把','被','给','让','向']);
  const tokens = new Set();
  const cleaned = title.replace(/[，。、！？：；""''（）()【】《》「」～~\-—\.\,\!\?\:\;]/g, ' ');
  for (const w of cleaned.split(/\s+/)) {
    if (!w) continue;
    if (stop.has(w)) continue;
    if (w.length === 1 && /[\u4e00-\u9fa5]/.test(w)) continue;
    tokens.add(w);
  }
  // 主要实体：腾讯/微信/QQ/王者/马化腾/张小龙等也单独加
  const entities = ['腾讯','微信','QQ','王者荣耀','和平精英','马化腾','张小龙','张军','视频号','小程序','支付','元宝'];
  for (const e of entities) if (title.includes(e)) tokens.add(e);
  return [...tokens];
}

const items = [];
let curSection = null;
let cur = null;

function flush() {
  if (!cur) return;
  // 拼装 markdown 笔记
  const lvl = cur.level || '未分级';
  const ip = cur.infoPoint || '';
  const reason = cur.reason || '';
  const businessLine = curSection || '其他';
  const keywords = extractKeywords(cur.title);

  const content = [
    `# ${cur.title}`,
    ``,
    `- **业务线**：${businessLine}`,
    `- **分级**：${lvl}`,
    ip ? `- **信息点**：${ip}` : '',
    ``,
    `## 辟谣要点`,
    reason || '（原始库未补充辟谣理由，以官方渠道为准）',
    ``,
    `## 关键词`,
    keywords.join(' / '),
    ``,
    `> 来源：腾讯公司辟谣资料库（已证实条目）`,
  ].filter(Boolean).join('\n');

  items.push({
    id: items.length + 1,
    title: cur.title,
    businessLine,
    level: lvl,
    infoPoint: ip,
    reason,
    keywords,
    tags: ['腾讯辟谣', businessLine, lvl].filter(Boolean),
    content,
  });
  cur = null;
}

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  const mSec = line.match(/^##\s+(.+?)\s*$/);
  if (mSec) {
    flush();
    curSection = normalizeSection(mSec[1]);
    continue;
  }
  const mItem = line.match(/^###\s+\d+\.\s+(.+?)\s*$/);
  if (mItem) {
    flush();
    cur = { title: mItem[1].trim(), level: '', infoPoint: '', reason: '' };
    continue;
  }
  if (!cur) continue;
  const mLvl = line.match(/^-\s*\*\*分级\*\*:\s*(.+?)\s*$/);
  if (mLvl) { cur.level = mLvl[1].trim(); continue; }
  const mIp = line.match(/^-\s*\*\*信息点\*\*:\s*(.+?)\s*$/);
  if (mIp) { cur.infoPoint = mIp[1].trim(); continue; }
  const mR = line.match(/^-\s*\*\*辟谣理由\*\*:\s*(.+?)\s*$/);
  if (mR) { cur.reason = mR[1].trim(); continue; }
}
flush();

// 统计
const stat = items.reduce((a, x) => { a[x.businessLine] = (a[x.businessLine]||0) + 1; return a; }, {});
fs.writeFileSync(OUT_PATH, JSON.stringify(items, null, 2), 'utf8');
console.log('Total:', items.length);
console.log('By business line:', stat);
console.log('Saved:', OUT_PATH);
