// 把共享表数据迁移到新表，并自动判定分级
const fs = require('fs');
const path = require('path');

const records = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../source-parsed.json'), 'utf8'));

// 分级判定规则（启发式）：
// - 谣言内容明显与事实相反（虚构事件、虚构政策、伪造声明）→ 完全虚假
// - 谣言内容是断章取义/夸大/曲解事实 → 部分失实
// - 谣言内容是带情绪的负面评价（如"垄断""吃相难看""害人"）但无具体虚假事实 → 不利表述
// - 故意扭曲解读官方信息 → 恶意解读
// - 其余无法判断 → 部分失实（保守策略，比"完全虚假"更稳健）

function judgeLevel(title, reason, infoPoint) {
  const t = (title || '').toLowerCase();
  const r = (reason || '').toLowerCase();
  const ip = infoPoint || '';

  // 强信号关键词
  const FULL_FAKE_KW = ['不实谣言', '为不实', '纯属谣言', '完全虚假', '从未', '并未', '未发生', '系造谣', 'AI生成', '伪造', '虚构', '编造', '蹭流量恶意引流', 'AI伪造', '虚假物料'];
  const PARTIAL_KW = ['断章取义', '部分失实', '夸大', '事实不全', '存在误导', '混淆', '误导', '细节不实'];
  const NEGATIVE_KW = ['垄断', '吃相难看', '害人', '精神鸦片', '抹黑', '不利表述', '恶意诋毁'];
  const MALICIOUS_KW = ['恶意解读', '歪曲事实', '扭曲', '恶意联想', '断章歪曲'];

  // 信息点维度的兜底判定
  if (ip === 'AI生成虚假物料' || ip === '编造老板言论') return '完全虚假';
  if (ip === '游戏害人' || ip === '垄断' || ip === '业务吃相难看') return '不利表述';

  // 关键词
  for (const k of MALICIOUS_KW) if (r.includes(k.toLowerCase()) || t.includes(k.toLowerCase())) return '恶意解读';
  for (const k of FULL_FAKE_KW) if (r.includes(k.toLowerCase()) || t.includes(k.toLowerCase())) return '完全虚假';
  for (const k of PARTIAL_KW) if (r.includes(k.toLowerCase()) || t.includes(k.toLowerCase())) return '部分失实';
  for (const k of NEGATIVE_KW) if (r.includes(k.toLowerCase()) || t.includes(k.toLowerCase())) return '不利表述';

  // 默认：部分失实
  return '部分失实';
}

const out = [];
for (const rec of records) {
  const v = rec.values || {};
  const title = v['谣言内容']?.[0]?.text || '';
  const reason = v['口径应对']?.[0]?.text || '';
  const infoPoint = v['谣言信息点']?.[0]?.text || '';
  const link = v['代表链接']?.[0]?.text || '';
  if (!title) continue;
  const level = judgeLevel(title, reason, infoPoint);
  out.push({ title, reason, infoPoint, link, level });
}

console.log('Total prepared:', out.length);
const stats = out.reduce((a,x) => { a[x.level] = (a[x.level]||0)+1; return a; }, {});
console.log('Level stats:', stats);
console.log('Sample[0]:', out[0]);
fs.writeFileSync(path.resolve(__dirname, '../migrated-records.json'), JSON.stringify(out, null, 2));
