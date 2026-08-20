#!/usr/bin/env node
/**
 * 公有云迁移工作量评估报告生成脚本 v4.1
 *
 * 计算参数与 references/resource-models.md、references/calculation-guide.md 保持一致
 * （对话评估与导出报告口径统一）。
 *
 * 用法:
 *   node generate-report.js --input data.json --format docx --output 迁移评估报告.docx
 *   node generate-report.js --input data.json --format xlsx --output 迁移工时明细.xlsx
 *
 * 依赖（导出报告时需要，纯计算不需要）:
 *   npm install docx exceljs
 *   - docx    : 用于生成 .docx 报告
 *   - exceljs : 用于生成 .xlsx 报告
 *   若未安装，脚本会给出清晰的安装指引后退出，不会崩溃。
 *
 * 输入: data.json（格式见 references/data-schema.md）
 */

const fs = require('fs');
const path = require('path');

// 依赖检查与降级指引：缺少 docx/exceljs 时给出友好提示，而非直接抛栈
function requireOrGuide(moduleName) {
    try {
        return require(moduleName);
    } catch (e) {
        console.error(`\n[依赖缺失] 未找到 npm 包 "${moduleName}"。`);
        console.error(`请在本脚本所在目录执行以下命令安装后重试：`);
        console.error(`    npm install docx exceljs\n`);
        console.error(`（提示：纯工时计算不依赖这两个包，仅"导出报告"功能需要。）`);
        process.exit(1);
    }
}

// ============== 解析命令行参数 ==============
const args = {};
for (let i = 2; i < process.argv.length; i += 2) {
    const key = process.argv[i].replace(/^--/, '');
    args[key] = process.argv[i + 1];
}

if (!args.input) {
    console.error('用法: node generate-report.js --input data.json --format docx|xlsx [--output filename]');
    process.exit(1);
}

const format = args.format || 'docx';
const inputData = JSON.parse(fs.readFileSync(args.input, 'utf-8'));

// ============== 迁移阶段定义 ==============
const MIGRATION_PHASES = [
    { id: 'planning',  name: '规划设计及方案确认' },
    { id: 'infra',     name: '基础环境搭建' },
    { id: 'provision', name: '资源开通与验证' },
    { id: 'migration', name: '数据同步与迁移' },
    { id: 'deploy',    name: '业务系统部署改造' },
    { id: 'testing',   name: '全面测试与割接上线' },
];

// ============== 资源类型工时模型 v4.1 ==============
// 参数权威来源：references/resource-models.md（工时=人工决策+验证时间，不含工具自动等待）
const RESOURCE_TYPE_MODELS = {
    '云服务器': { keywords: ['CVM','ECS','云主机','云服务器','vCPU','EC2','VM','虚拟机','BMS','裸金属','物理机'], complexity:'medium', phaseWork:{planning:0.05,infra:0.02,provision:0.10,migration:0.30,deploy:0.15,testing:0.10}, totalPerInstance:0.72 },
    '云数据库': { keywords: ['MySQL','TDSQL','数据库','RDS','TiDB','PostgreSQL','MariaDB','SQL Server','Oracle','PolarDB','DRDS'], complexity:'high', phaseWork:{planning:0.15,infra:0.05,provision:0.20,migration:0.80,deploy:0.30,testing:0.30}, totalPerInstance:1.8 },
    '缓存': { keywords: ['Redis','Memcached','缓存','Tendis'], complexity:'medium', phaseWork:{planning:0.05,infra:0.02,provision:0.10,migration:0.40,deploy:0.20,testing:0.15}, totalPerInstance:0.92 },
    '搜索服务': { keywords: ['Elasticsearch','OpenSearch','ES集群','搜索','Solr'], complexity:'high', phaseWork:{planning:0.15,infra:0.05,provision:0.20,migration:0.60,deploy:0.30,testing:0.20}, totalPerInstance:1.5 },
    '文档数据库': { keywords: ['MongoDB','Mongo','文档数据库','DocumentDB','DynamoDB'], complexity:'medium', phaseWork:{planning:0.10,infra:0.02,provision:0.15,migration:0.50,deploy:0.20,testing:0.15}, totalPerInstance:1.12 },
    '消息队列': { keywords: ['Kafka','RocketMQ','RabbitMQ','消息队列','MQ','Pulsar','ActiveMQ','TDMQ','CMQ'], complexity:'medium', phaseWork:{planning:0.10,infra:0.05,provision:0.15,migration:0.30,deploy:0.25,testing:0.20}, totalPerInstance:1.05 },
    '容器产品': { keywords: ['TKE','K8s','Kubernetes','容器','TCR','镜像','Docker','ACK','CCE','EKS'], complexity:'high', phaseWork:{planning:0.30,infra:0.50,provision:0.30,migration:0.40,deploy:0.80,testing:0.40}, totalPerInstance:2.7 },
    '网络产品': { keywords: ['ELB','CLB','ALB','NAT','VPC','DNS','负载均衡','公网IP','EIP','专线','VPN','带宽','SLB','CDN'], complexity:'low', phaseWork:{planning:0.05,infra:0.10,provision:0.05,migration:0.02,deploy:0.03,testing:0.03}, totalPerInstance:0.28 },
    '安全产品': { keywords: ['WAF','防火墙','堡垒机','DDoS','高防','安全组','密钥','SSL','证书','HSM','主机安全'], complexity:'medium', phaseWork:{planning:0.10,infra:0.20,provision:0.15,migration:0.15,deploy:0.20,testing:0.15}, totalPerInstance:0.95 },
    '安全服务': { keywords: ['等保','安全运维','安全托管','渗透测试','漏洞扫描','安全评估'], complexity:'high', phaseWork:{planning:0.30,infra:0.20,provision:0.20,migration:0.30,deploy:0.50,testing:0.50}, totalPerInstance:2.0 },
    'CDN/存储': { keywords: ['COS','OSS','S3','对象存储','文件存储','NAS','CFS','CBS','云硬盘','块存储'], complexity:'low', phaseWork:{planning:0.05,infra:0.02,provision:0.05,migration:0.25,deploy:0.10,testing:0.05}, totalPerInstance:0.52 },
    '大数据': { keywords: ['EMR','Hadoop','Spark','Flink','Hive','HBase','数据湖','ClickHouse','Presto','Doris'], complexity:'high', phaseWork:{planning:0.30,infra:0.30,provision:0.30,migration:0.80,deploy:0.50,testing:0.30}, totalPerInstance:2.5 },
    '中间件': { keywords: ['Nacos','Apollo','Consul','注册中心','配置中心','Zookeeper','etcd','API网关','微服务引擎'], complexity:'medium', phaseWork:{planning:0.10,infra:0.10,provision:0.15,migration:0.30,deploy:0.25,testing:0.15}, totalPerInstance:1.05 },
    '其他': { keywords: [], complexity:'medium', phaseWork:{planning:0.10,infra:0.05,provision:0.15,migration:0.25,deploy:0.20,testing:0.15}, totalPerInstance:0.9 },
};

const COMPLEXITY_WEIGHTS = { low: 0.8, medium: 1.0, high: 1.3 };
const COMPLEXITY_LABELS = { low: '低', medium: '中', high: '高' };

// 固定开销基准值（满额，未缩放）—— 权威来源：references/calculation-guide.md
const PROJECT_OVERHEAD = {
    planning: [{ name:'项目启动会',days:1,aiR:0.1 },{ name:'网络方案设计',days:1.5,aiR:0.3 },{ name:'排期规划',days:1,aiR:0.4 },{ name:'方案文档编写评审',days:2,aiR:0.35 }],
    infra: [{ name:'VPC/子网搭建',days:1.5,aiR:0.45 },{ name:'监控体系搭建',days:1,aiR:0.4 }],
    provision: [{ name:'迁移工具部署',days:0.5,aiR:0.4 }],
    migration: [{ name:'数据一致性校验',days:1.5,aiR:0.3 }],
    deploy: [{ name:'第三方系统联调',days:1.5,aiR:0.15 }],
    testing: [{ name:'割接演练',days:2,aiR:0.2 },{ name:'正式割接',days:1,aiR:0.1 },{ name:'上线观察',days:3,aiR:0.15 }],
};

// 规格权重：从规格字符串解析 vCPU 数量（references/resource-models.md）
function getSpecWeight(spec) {
    if (!spec) return 1.0;
    const m = String(spec).match(/(\d+)\s*[cCC核]/);
    const cpu = m ? parseInt(m[1]) : 0;
    if (cpu >= 64) return 1.4;
    if (cpu >= 32) return 1.25;
    if (cpu >= 16) return 1.1;
    return 1.0;
}

// 项目固定开销规模缩放系数（references/calculation-guide.md 第二层）
function getOverheadScaleFactor(totalInstances, typeCount) {
    if (totalInstances <= 3 && typeCount <= 2) return 0.15;   // 极小项目
    if (totalInstances <= 10 && typeCount <= 5) return 0.35;  // 小项目
    if (totalInstances <= 30 && typeCount <= 10) return 0.60; // 中等项目
    if (totalInstances <= 80) return 0.80;                    // 中大项目
    return 1.00;                                              // 大项目
}

// ============== 计算引擎 ==============
function detectCategory(resource) {
    const text = ((resource.name||'')+ ' '+(resource.spec||'')+' '+(resource.usage||'')).toLowerCase();
    for (const [cat, model] of Object.entries(RESOURCE_TYPE_MODELS)) {
        if (cat === '其他') continue;
        for (const kw of model.keywords) {
            if (text.includes(kw.toLowerCase())) return cat;
        }
    }
    return '其他';
}

function getPhaseAiReduction(phaseId, category) {
    const phaseAiBase = { planning:0.35, infra:0.40, provision:0.50, migration:0.25, deploy:0.30, testing:0.35 };
    const catMod = { '云数据库':0.8, '搜索服务':0.85, '容器产品':0.9, '大数据':0.8 };
    return (phaseAiBase[phaseId]||0.3) * (catMod[category]||1.0);
}

function calculate(data) {
    const config = data.config || { teamSize:5, hoursPerDay:8, aiBoost:50, parallel:0.7, riskBuffer:15, costPerDay:1500 };
    if (config.aiBoost == null) config.aiBoost = 50;
    const resources = (data.resources || []).map(r => ({
        ...r,
        category: r.category || detectCategory(r),
        complexity: r.complexity || (RESOURCE_TYPE_MODELS[r.category||detectCategory(r)]||RESOURCE_TYPE_MODELS['其他']).complexity,
    }));

    // 资源级工时
    const resourceBreakdown = resources.map(r => {
        const model = RESOURCE_TYPE_MODELS[r.category] || RESOURCE_TYPE_MODELS['其他'];
        const cw = COMPLEXITY_WEIGHTS[r.complexity] || 1.0;
        const specW = getSpecWeight(r.spec);
        const qty = parseInt(r.qty) || 1;
        const qtyF = qty <= 1 ? 1 : (1 + (qty-1)*0.6);
        const pb = {};
        let totalRaw = 0, totalAi = 0;
        for (const phase of MIGRATION_PHASES) {
            const base = model.phaseWork[phase.id] || 0;
            const raw = base * qtyF * cw * specW;
            const aiR = getPhaseAiReduction(phase.id, r.category);
            const aiDays = raw * (1 - aiR * (config.aiBoost/100));
            const final = Math.max(aiDays, raw * 0.2);
            pb[phase.id] = { rawDays: Math.round(raw*100)/100, aiDays: Math.round(final*100)/100 };
            totalRaw += raw; totalAi += final;
        }
        return { ...r, qty, qtyEffectiveFactor: Math.round(qtyF*100)/100, complexityFactor: cw, specWeight: specW, complexityLabel: COMPLEXITY_LABELS[r.complexity]||'中', phaseBreakdown: pb, totalRawDays: Math.round(totalRaw*10)/10, totalAiDays: Math.round(totalAi*10)/10 };
    });

    // 项目固定开销（按项目规模动态缩放）
    const totalInstances = resources.reduce((s,r)=>s+(parseInt(r.qty)||1),0);
    const typeCount = new Set(resources.map(r=>r.category)).size;
    const overheadScale = getOverheadScaleFactor(totalInstances, typeCount);
    const aiBoostN = config.aiBoost / 100;
    const overhead = {};
    for (const phase of MIGRATION_PHASES) {
        const tasks = (PROJECT_OVERHEAD[phase.id]||[]).map(t => {
            const scaledDays = t.days * overheadScale;
            const aiDays = scaledDays * (1 - t.aiR * aiBoostN);
            return { name: t.name, rawDays: Math.round(scaledDays*100)/100, aiDays: Math.round(Math.max(aiDays, scaledDays*0.3)*100)/100 };
        });
        overhead[phase.id] = { tasks, rawTotal: tasks.reduce((s,t)=>s+t.rawDays,0), aiTotal: tasks.reduce((s,t)=>s+t.aiDays,0) };
    }

    // 汇总
    const phaseWorkload = MIGRATION_PHASES.map(phase => {
        let resRaw=0, resAi=0;
        resourceBreakdown.forEach(r => { resRaw += r.phaseBreakdown[phase.id].rawDays; resAi += r.phaseBreakdown[phase.id].aiDays; });
        const oh = overhead[phase.id];
        return { ...phase, resourceRaw:Math.round(resRaw*10)/10, resourceAi:Math.round(resAi*10)/10, overheadRaw:Math.round(oh.rawTotal*10)/10, overheadAi:Math.round(oh.aiTotal*10)/10, rawTotal:Math.round((resRaw+oh.rawTotal)*10)/10, aiTotal:Math.round((resAi+oh.aiTotal)*10)/10 };
    });

    const rawTotal = phaseWorkload.reduce((s,p)=>s+p.rawTotal,0);
    const aiTotal = phaseWorkload.reduce((s,p)=>s+p.aiTotal,0);
    const buffered = aiTotal * (1 + config.riskBuffer/100);
    const calendarDays = Math.floor(buffered / (config.teamSize * config.parallel));
    const totalResources = resources.reduce((s,r)=>s+(parseInt(r.qty)||1),0);

    return { resourceBreakdown, phaseWorkload, overhead, overheadScale, rawTotal:Math.round(rawTotal*10)/10, aiTotal:Math.round(aiTotal*10)/10, buffered:Math.round(buffered*10)/10, calendarDays, aiSaveDays:Math.round((rawTotal-aiTotal)*10)/10, aiSavePct:rawTotal>0?Math.round((rawTotal-aiTotal)/rawTotal*100):0, aiCostSave:Math.round((rawTotal-aiTotal)*config.costPerDay), totalResources, config };
}

// ============== Word 报告生成 ==============
async function generateDocx(data, results, outputPath) {
    const { Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun, AlignmentType, BorderStyle, WidthType, HeadingLevel, ShadingType } = requireOrGuide('docx');
    const pi = data.projectInfo || {};
    const r = results;
    const today = new Date().toLocaleDateString('zh-CN');
    const blue = '006EFF';

    const targetCloudName = { tencent:'腾讯云', aliyun:'阿里云', huawei:'华为云', aws:'AWS', azure:'Azure', gcp:'GCP', other:'其他' }[pi.targetCloud] || pi.targetCloud || '目标云';
    const sourceTypeName = { 'private-cloud':'私有云', idc:'自建IDC', 'other-cloud':'其他公有云', hybrid:'混合环境' }[pi.sourceType] || pi.sourceType || '源端';

    function heading(text, level) { return new Paragraph({ text, heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 } }); }
    function para(text, opts = {}) { return new Paragraph({ children: [new TextRun({ text, size: opts.size || 21, bold: opts.bold, color: opts.color })], spacing: { after: 80 }, alignment: opts.align }); }
    function cell(text, opts = {}) { return new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: String(text), size: 18, bold: opts.bold, color: opts.color })], alignment: AlignmentType.CENTER })], shading: opts.bg ? { type: ShadingType.SOLID, color: opts.bg } : undefined, width: opts.width ? { size: opts.width, type: WidthType.PERCENTAGE } : undefined }); }

    const sections = [];

    // 封面
    sections.push(para(' '));
    sections.push(para(' '));
    sections.push(para(pi.name || '公有云迁移项目', { size: 44, bold: true, color: blue, align: AlignmentType.CENTER }));
    sections.push(para('工作量评估报告', { size: 36, bold: true, color: blue, align: AlignmentType.CENTER }));
    sections.push(para(' '));
    sections.push(para(`评估日期：${today}`, { size: 24, align: AlignmentType.CENTER }));
    sections.push(para(`评估人：${pi.assessor || ''}`, { size: 24, align: AlignmentType.CENTER }));
    sections.push(para(' '));
    sections.push(para(' '));

    // 一、项目概要
    sections.push(heading('一、项目迁移概要', 1));
    sections.push(para(`项目名称：${pi.name || '（未填写）'}`));
    sections.push(para(`客户/单位：${pi.client || '（未填写）'}`));
    if (pi.code) sections.push(para(`项目编号：${pi.code}`));
    sections.push(para(`迁移方向：${sourceTypeName}${pi.sourceLocation?'（'+pi.sourceLocation+'）':''} → ${targetCloudName}${pi.targetRegion?'（'+pi.targetRegion+'）':''}`));
    sections.push(para(`评估日期：${today}`));
    sections.push(para(`资源规模：${r.resourceBreakdown.length} 类资源，共 ${r.totalResources} 个实例`));
    sections.push(para(`预估周期：${r.calendarDays} 日历天（含 ${r.config.riskBuffer}% 风险缓冲）`));

    // 二、资源清单汇总
    sections.push(heading('二、迁移资源清单', 1));
    const catMap = {};
    r.resourceBreakdown.forEach(res => {
        const cat = res.category || '其他';
        if (!catMap[cat]) catMap[cat] = { count: 0, qty: 0, aiDays: 0 };
        catMap[cat].count++;
        catMap[cat].qty += res.qty;
        catMap[cat].aiDays += res.totalAiDays;
    });
    const resTableRows = [new TableRow({ children: [cell('资源类别',{bold:true,bg:'D6E4F0'}), cell('类型数',{bold:true,bg:'D6E4F0'}), cell('实例数',{bold:true,bg:'D6E4F0'}), cell('工时(人天)',{bold:true,bg:'D6E4F0'})] })];
    for (const [cat, info] of Object.entries(catMap)) {
        resTableRows.push(new TableRow({ children: [cell(cat), cell(info.count), cell(info.qty), cell(Math.round(info.aiDays*10)/10, {bold:true})] }));
    }
    resTableRows.push(new TableRow({ children: [cell('合计',{bold:true,bg:'E8F4FF'}), cell(r.resourceBreakdown.length,{bold:true,bg:'E8F4FF'}), cell(r.totalResources,{bold:true,bg:'E8F4FF'}), cell(r.aiTotal,{bold:true,bg:'E8F4FF'})] }));
    sections.push(new Table({ rows: resTableRows, width: { size: 100, type: WidthType.PERCENTAGE } }));

    // 三、工作量评估
    sections.push(heading('三、迁移工作量评估', 1));
    const wlRows = [new TableRow({ children: [cell('迁移阶段',{bold:true,bg:'D6E4F0'}), cell('资源驱动',{bold:true,bg:'D6E4F0'}), cell('固定开销',{bold:true,bg:'D6E4F0'}), cell('阶段合计',{bold:true,bg:'D6E4F0'}), cell('AI优化前',{bold:true,bg:'D6E4F0'}), cell('节省',{bold:true,bg:'D6E4F0'})] })];
    r.phaseWorkload.forEach(p => {
        const save = Math.round((p.rawTotal - p.aiTotal)*10)/10;
        wlRows.push(new TableRow({ children: [cell(p.name), cell(p.resourceAi), cell(p.overheadAi), cell(p.aiTotal,{bold:true}), cell(p.rawTotal,{color:'999999'}), cell(`-${save}`,{color:'10B981'})] }));
    });
    wlRows.push(new TableRow({ children: [cell('合计',{bold:true,bg:'E8F4FF'}), cell(Math.round(r.phaseWorkload.reduce((s,p)=>s+p.resourceAi,0)*10)/10,{bold:true,bg:'E8F4FF'}), cell(Math.round(r.phaseWorkload.reduce((s,p)=>s+p.overheadAi,0)*10)/10,{bold:true,bg:'E8F4FF'}), cell(r.aiTotal,{bold:true,bg:'E8F4FF'}), cell(r.rawTotal,{bg:'E8F4FF',color:'999999'}), cell(`-${r.aiSaveDays}(${r.aiSavePct}%)`,{bg:'E8F4FF',color:'10B981'})] }));
    sections.push(new Table({ rows: wlRows, width: { size: 100, type: WidthType.PERCENTAGE } }));

    sections.push(para(`含 ${r.config.riskBuffer}% 风险缓冲后总工时：${r.buffered} 人天`));
    sections.push(para(`团队 ${r.config.teamSize} 人，并行度 ${r.config.parallel}，预估日历天数：${r.calendarDays} 天`));
    sections.push(para(`AI效率提升 ${r.config.aiBoost}%，节省人力成本约 ¥${r.aiCostSave.toLocaleString()}`));

    // 四、详细资源工时分解
    sections.push(heading('四、详细资源工时分解', 1));
    const detailHeaders = [cell('类别',{bold:true,bg:'D6E4F0'}), cell('资源名称',{bold:true,bg:'D6E4F0'}), cell('数量',{bold:true,bg:'D6E4F0'}), cell('复杂度',{bold:true,bg:'D6E4F0'})];
    MIGRATION_PHASES.forEach(p => detailHeaders.push(cell(p.name.substring(0,4),{bold:true,bg:'D6E4F0'})));
    detailHeaders.push(cell('合计',{bold:true,bg:'D6E4F0'}));
    const detailRows = [new TableRow({ children: detailHeaders })];
    r.resourceBreakdown.forEach(res => {
        const cells = [cell(res.category||'其他'), cell(res.name), cell(res.qty), cell(res.complexityLabel)];
        MIGRATION_PHASES.forEach(p => cells.push(cell(res.phaseBreakdown[p.id].aiDays)));
        cells.push(cell(res.totalAiDays, {bold:true}));
        detailRows.push(new TableRow({ children: cells }));
    });
    sections.push(new Table({ rows: detailRows, width: { size: 100, type: WidthType.PERCENTAGE } }));

    // 五、实施建议
    sections.push(heading('五、实施建议', 1));
    sections.push(para('1. 分批迁移策略：建议按业务优先级分3~4批次迁移。先迁移非核心系统验证流程，再迁移核心系统。'));
    sections.push(para('2. 灰度切流方案：利用DNS/负载均衡进行灰度切流，10%→50%→100%逐步提升。'));
    sections.push(para('3. AI工具辅助：使用AI辅助工具进行资源评估、数据校验、配置适配，提升迁移效率。'));
    sections.push(para('4. 回滚保障：每个迁移批次准备完整的回滚方案，确保可快速恢复。'));
    sections.push(para('5. 后续优化：迁移上线后进行性能调优、成本优化、安全加固。'));

    const doc = new Document({
        styles: { default: { document: { run: { font: '微软雅黑', size: 21 } } } },
        sections: [{ children: sections }],
    });

    const buffer = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buffer);
    console.log(`✅ Word报告已生成: ${outputPath} (${(buffer.length/1024).toFixed(1)} KB)`);
}

// ============== Excel 报告生成 ==============
async function generateXlsx(data, results, outputPath) {
    const ExcelJS = requireOrGuide('exceljs');
    const pi = data.projectInfo || {};
    const r = results;
    const wb = new ExcelJS.Workbook();
    wb.creator = 'Cloud Migration Assessor';

    const headerFill = { type:'pattern', pattern:'solid', fgColor:{argb:'FFD6E4F0'} };
    const headerFont = { bold: true, size: 10 };
    const totalFill = { type:'pattern', pattern:'solid', fgColor:{argb:'FFE8F4FF'} };

    // Sheet 1: 项目概要
    const ws1 = wb.addWorksheet('项目概要');
    ws1.columns = [{ width: 20 }, { width: 40 }];
    ws1.addRow(['项目迁移工作量评估']).font = { bold: true, size: 16, color: { argb: 'FF006EFF' } };
    ws1.addRow([]);
    [['项目名称', pi.name||''], ['客户/单位', pi.client||''], ['项目编号', pi.code||''], ['评估人', pi.assessor||''],
     ['源端类型', pi.sourceType||''], ['源端位置', pi.sourceLocation||''], ['目标云平台', pi.targetCloud||''], ['目标区域', pi.targetRegion||''],
     ['', ''], ['评估结果汇总', ''],
     ['资源类型数', r.resourceBreakdown.length], ['总实例数', r.totalResources],
     ['AI优化后总工时', `${r.aiTotal} 人天`], ['含风险缓冲工时', `${r.buffered} 人天`],
     ['预估日历天数', `${r.calendarDays} 天`], ['AI节省工时', `${r.aiSaveDays} 人天 (${r.aiSavePct}%)`],
     ['节省人力成本', `¥${r.aiCostSave.toLocaleString()}`],
    ].forEach(row => ws1.addRow(row));

    // Sheet 2: 资源清单
    const ws2 = wb.addWorksheet('资源清单');
    const resHeaders = ['序号','类别','资源名称','规格','数量','复杂度','用途','工时(人天)'];
    const resHeaderRow = ws2.addRow(resHeaders);
    resHeaderRow.eachCell(c => { c.fill = headerFill; c.font = headerFont; });
    ws2.columns = [{ width:6 },{ width:12 },{ width:20 },{ width:25 },{ width:8 },{ width:8 },{ width:25 },{ width:12 }];
    r.resourceBreakdown.forEach((res, i) => {
        ws2.addRow([i+1, res.category||'其他', res.name, res.spec||'', res.qty, res.complexityLabel, res.usage||'', res.totalAiDays]);
    });
    const resTotalRow = ws2.addRow(['','合计','','',r.totalResources,'','',r.aiTotal]);
    resTotalRow.eachCell(c => { c.fill = totalFill; c.font = { bold: true }; });

    // Sheet 3: 工时分解矩阵
    const ws3 = wb.addWorksheet('工时分解矩阵');
    const matHeaders = ['类别','资源名称','数量','复杂度', ...MIGRATION_PHASES.map(p=>p.name.substring(0,6)), '合计'];
    const matHeaderRow = ws3.addRow(matHeaders);
    matHeaderRow.eachCell(c => { c.fill = headerFill; c.font = headerFont; });
    ws3.columns = [{ width:12 },{ width:18 },{ width:8 },{ width:8 },{ width:10 },{ width:10 },{ width:10 },{ width:10 },{ width:10 },{ width:10 },{ width:10 }];
    r.resourceBreakdown.forEach(res => {
        const row = [res.category||'其他', res.name, res.qty, res.complexityLabel];
        MIGRATION_PHASES.forEach(p => row.push(res.phaseBreakdown[p.id].aiDays));
        row.push(res.totalAiDays);
        ws3.addRow(row);
    });
    const matTotalRow = ws3.addRow(['阶段小计','','','', ...MIGRATION_PHASES.map(p => r.phaseWorkload.find(pw=>pw.id===p.id).resourceAi), Math.round(r.phaseWorkload.reduce((s,p)=>s+p.resourceAi,0)*10)/10]);
    matTotalRow.eachCell(c => { c.fill = totalFill; c.font = { bold: true }; });

    // Sheet 4: 阶段汇总
    const ws4 = wb.addWorksheet('阶段汇总');
    const phHeaders = ['迁移阶段','资源驱动(人天)','固定开销(人天)','阶段合计(人天)','AI优化前(人天)','节省(人天)'];
    const phHeaderRow = ws4.addRow(phHeaders);
    phHeaderRow.eachCell(c => { c.fill = headerFill; c.font = headerFont; });
    ws4.columns = [{ width:22 },{ width:16 },{ width:16 },{ width:16 },{ width:16 },{ width:12 }];
    r.phaseWorkload.forEach(p => {
        ws4.addRow([p.name, p.resourceAi, p.overheadAi, p.aiTotal, p.rawTotal, Math.round((p.rawTotal-p.aiTotal)*10)/10]);
    });
    const phTotalRow = ws4.addRow(['合计', Math.round(r.phaseWorkload.reduce((s,p)=>s+p.resourceAi,0)*10)/10, Math.round(r.phaseWorkload.reduce((s,p)=>s+p.overheadAi,0)*10)/10, r.aiTotal, r.rawTotal, r.aiSaveDays]);
    phTotalRow.eachCell(c => { c.fill = totalFill; c.font = { bold: true }; });

    // Sheet 5: 风险矩阵
    const ws5 = wb.addWorksheet('风险矩阵');
    const riskHeaders = ['风险描述','风险等级','发生概率','影响程度','缓解措施'];
    const riskHeaderRow = ws5.addRow(riskHeaders);
    riskHeaderRow.eachCell(c => { c.fill = headerFill; c.font = headerFont; });
    ws5.columns = [{ width:30 },{ width:10 },{ width:10 },{ width:10 },{ width:50 }];
    const RISKS = [
        { risk:'数据迁移过程中数据丢失或不一致', level:'高', prob:'中', impact:'高', mit:'采用DTS/数据同步工具；全量数据校验；制定数据回滚方案' },
        { risk:'业务中断时间超出预期窗口', level:'高', prob:'中', impact:'高', mit:'详细割接方案与回滚方案；分批次迁移、灰度切流；至少2次割接演练' },
        { risk:'应用兼容性问题导致功能异常', level:'中', prob:'中', impact:'中', mit:'提前兼容性测试；建立测试环境；准备适配方案' },
        { risk:'网络延迟或带宽不足', level:'中', prob:'低', impact:'高', mit:'网络压力测试；专线/VPN双通道冗余；优化网络架构' },
        { risk:'安全合规差异', level:'中', prob:'中', impact:'中', mit:'梳理安全合规要求；配置安全基线；安全扫描评估' },
        { risk:'第三方系统对接调整', level:'低', prob:'中', impact:'中', mit:'盘点接口清单；预留联调时间；准备降级方案' },
        { risk:'团队技能不足延长工期', level:'低', prob:'低', impact:'中', mit:'提前培训；引入外部顾问；使用AI辅助工具' },
    ];
    RISKS.forEach(risk => ws5.addRow([risk.risk, risk.level, risk.prob, risk.impact, risk.mit]));

    await wb.xlsx.writeFile(outputPath);
    const stats = fs.statSync(outputPath);
    console.log(`✅ Excel报告已生成: ${outputPath} (${(stats.size/1024).toFixed(1)} KB)`);
}

// ============== 主流程 ==============
async function main() {
    const results = calculate(inputData);
    const defaultName = (inputData.projectInfo && inputData.projectInfo.name) || '迁移评估';
    const outputPath = args.output || (format === 'docx' ? `${defaultName}-评估报告.docx` : `${defaultName}-工时明细.xlsx`);

    if (format === 'docx') {
        await generateDocx(inputData, results, outputPath);
    } else if (format === 'xlsx') {
        await generateXlsx(inputData, results, outputPath);
    } else {
        console.error('不支持的格式，请使用 docx 或 xlsx');
        process.exit(1);
    }
}

main().catch(err => { console.error('生成失败:', err.message); process.exit(1); });
