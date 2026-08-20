// 给新表的232条记录填充业务线字段
// 数据源：本地 references/rumor-database.md（标题→业务线 映射字典）
// 新条目（不在本地库里的）按关键词规则兜底归类

const fs = require('fs');
const path = require('path');

const MD_PATH = path.resolve(__dirname, '..', 'references/rumor-database.md');
const md = fs.readFileSync(MD_PATH, 'utf8');
const lines = md.split(/\r?\n/);

// 1) 解析本地库 → 字典 {标题 → 业务线}
const dict = {};
let curSection = null;
function normSection(name) {
  const n = (name || '').trim().replace(/\s+/g, '').replace(/业务$/, '');
  if (/WXG/i.test(n)) return 'WXG';
  if (/IEG/i.test(n)) return 'IEG';
  if (/PCG/i.test(n)) return 'PCG';
  if (/CSIG/i.test(n)) return 'CSIG';
  if (/^MA$/i.test(n)) return 'MA';
  if (/集团/.test(n)) return '集团';
  if (/老板/.test(n)) return '老板';
  return null;
}
for (const line of lines) {
  const mSec = line.match(/^##\s+(.+?)\s*$/);
  if (mSec) { curSection = normSection(mSec[1]); continue; }
  const mItem = line.match(/^###\s+\d+\.\s+(.+?)\s*$/);
  if (mItem && curSection) {
    dict[mItem[1].trim()] = curSection;
  }
}
console.log('Dict size:', Object.keys(dict).length);

// 2) 关键词兜底规则
function classifyByKeyword(title, infoPoint, reason) {
  const t = (title + ' ' + (reason || '')).toLowerCase();
  const ip = infoPoint || '';

  // 老板专属
  if (/马化腾|pony|马老板|大老板|龙叔|张小龙[^团队]|刘炽平|腾讯创始|马云换姓|腾讯老板/i.test(t)) {
    if (ip === '大老板隐私' || ip === '编造老板言论' || ip === '高管薪酬和生活' || ip === '民营企业家') return '老板';
    if (/马化腾|pony|马老板|大老板/i.test(t)) return '老板';
  }

  // WXG = 微信/QQ/视频号/小程序/支付/财付通
  if (/微信|wechat|wx|qq[^a-z]|qq |q币|视频号|小程序|公众号|微信支付|财付通|支付分|微粒贷|微众/i.test(t)) return 'WXG';

  // IEG = 游戏
  if (/游戏|王者|和平精英|英雄联盟|lol|地下城|dnf|穿越火线|cf[^a-z]|qq飞车|逆战|天天系列|手游|网游|nexon|supercell|riot|腾讯游戏|腾讯互娱|腾讯ieg|未成年人.*游戏|防沉迷|精神鸦片|游戏害人|腾讯系游戏|腾讯出品.*游戏/i.test(t)) return 'IEG';
  if (ip === '游戏害人') return 'IEG';

  // PCG = 视频/腾讯视频/QQ音乐/腾讯新闻/动漫/阅文
  if (/腾讯视频|qq音乐|腾讯新闻|腾讯动漫|阅文|起点中文|腾讯影业|腾讯体育|nba.*腾讯|weishi|微视|nba版权|腾讯文学/i.test(t)) return 'PCG';

  // CSIG = 云/教育/会议/医疗/政企
  if (/腾讯云|腾讯会议|tmeet|腾讯教育|腾讯医疗|腾讯安全|企业微信|wecom|腾讯coding|腾讯地图|腾讯文档|腾讯乐享|腾讯电子签|csig|政企/i.test(t)) return 'CSIG';

  // MA = 投资并购、对外合作、AI大模型、混元
  if (/混元|hunyuan|hy3|大模型|llm|腾讯ai|腾讯元宝|ima知识库|腾讯投资|腾讯系|入股|收购|并购|上市|ipo|股权|减持|增持|入资|领投|跟投|腾讯持股/i.test(t)) return 'MA';
  if (ip === '投资' || ip === '商业合作' || ip === '股权结构' || ip === '商业竞对' || ip === 'AI生成虚假物料') return 'MA';

  // 集团 = 法务/HR/纳税/慈善/意识形态/企业文化/营收
  if (/腾讯法务|南山必胜客|起诉|诉讼|腾讯起诉|被起诉|腾讯纳税|腾讯捐赠|公益|慈善|腾讯薪资|腾讯裁员|腾讯绩效|腾讯加班|腾讯文化|腾讯总部|集团/i.test(t)) return '集团';
  if (['法务','HR事务','员工薪酬福利','行政','纳税','慈善公益','企业文化','意识形态','营收和利润','垄断','业务吃相难看','民营企业家'].includes(ip)) return '集团';

  // 默认兜底 → 集团
  return '集团';
}

// 3) 加载新表数据（先要去拉一次最新的）
const newRecPath = path.resolve(__dirname, '..', 'new-records-fresh.json');
if (!fs.existsSync(newRecPath)) {
  console.log('Need new-records-fresh.json first. Run fetch step.');
  process.exit(1);
}
const raw = JSON.parse(fs.readFileSync(newRecPath, 'utf8'));
const data = JSON.parse(raw.result.content[0].text);
const records = data.records;
console.log('New table records:', records.length);

// 4) 对每条记录决定业务线
const updates = [];
let exactHit = 0, kwHit = 0;
const stats = {};
for (const rec of records) {
  const v = rec.values || {};
  const title = v['谣言内容']?.[0]?.text || '';
  const infoPoint = v['谣言信息点']?.[0]?.text || '';
  const reason = v['口径应对']?.[0]?.text || '';
  if (!title) continue;
  let bl = dict[title];
  if (bl) exactHit++;
  else { bl = classifyByKeyword(title, infoPoint, reason); kwHit++; }
  stats[bl] = (stats[bl] || 0) + 1;
  updates.push({ record_id: rec.record_id, businessLine: bl });
}

console.log('Exact hits:', exactHit, '/ keyword hits:', kwHit);
console.log('Distribution:', stats);
fs.writeFileSync(path.resolve(__dirname, '..', 'biz-updates.json'), JSON.stringify(updates, null, 2));
