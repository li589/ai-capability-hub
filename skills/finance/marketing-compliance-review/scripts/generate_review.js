// 消保审查意见书生成器
// 用法：node generate_review.js <input.json> [output.docx]
//   input.json  : 结构化的审查数据（见 SKILL.md 或 references/input-schema.md）
//   output.docx : 输出路径（缺省按材料名生成）
//
// 依赖：docx  npm install docx
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, LevelFormat
} = require("docx");

const RED = "CC0000";
const YELLOW = "E6A817";
const GREEN = "2E7D32";
const BLUE = "0052D9";
const LIGHT_BLUE = "E8F0FE";
const GRAY_BG = "F5F5F5";
const BLACK = "333333";
const GRAY = "999999";
const SZ = 20;
// 分别声明西文与东亚字体，提升 Word 在 Windows / macOS 间的中文回退兼容性。
const FONT = { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" };

const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const cm = { top: 80, bottom: 80, left: 120, right: 120 };

function hCell(t, w, f) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: { fill: f || LIGHT_BLUE, type: ShadingType.CLEAR }, margins: cm,
    children: [new Paragraph({ children: [new TextRun({ text: t, bold: true, font: FONT, size: SZ, color: BLACK })] })]
  });
}
function tCell(t, w, o) {
  o = o || {};
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR } : undefined, margins: cm,
    children: [new Paragraph({ children: [new TextRun({ text: t, font: FONT, size: SZ, color: o.color || BLACK, bold: !!o.bold })] })]
  });
}
function mCell(lines, w, o) {
  o = o || {};
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR } : undefined, margins: cm,
    children: lines.map(l => new Paragraph({ children: [new TextRun({ text: l, font: FONT, size: SZ, color: o.color || BLACK, bold: !!o.bold })] }))
  });
}
function rBadge(lv) {
  const m = { "🔴 高风险": RED, "🟡 中风险": YELLOW, "🟢 低风险": GREEN };
  return new TextRun({ text: lv, bold: true, color: m[lv] || BLACK, font: FONT, size: SZ });
}
function sTitle(t) {
  return new Paragraph({ spacing: { before: 360, after: 160 },
    children: [new TextRun({ text: t, bold: true, font: FONT, size: 24, color: BLUE })]
  });
}
function p(t, o) {
  o = o || {};
  if (typeof t === "string") t = [new TextRun({ text: t, font: FONT, size: o.sz || SZ, color: o.color || BLACK, bold: !!o.bold, italics: !!o.italics })];
  return new Paragraph(o.sp ? Object.assign({}, o.sp, { children: t }) : { children: t });
}
function pRuns(runs, o) {
  o = o || {};
  return new Paragraph(o.sp ? Object.assign({}, o.sp, { children: runs }) : { children: runs });
}
function riskColor(risk) {
  if ((risk || "").indexOf("高") >= 0) return RED;
  if ((risk || "").indexOf("中") >= 0) return YELLOW;
  return GREEN;
}

function problemSection(no, title, risk, dimension, excerpt, rule, bases, suggestion) {
  const tc = riskColor(risk);
  return [
    p([new TextRun({ text: `问题 ${no}：${title}`, bold: true, font: FONT, size: 22, color: tc })], { sp: { spacing: { before: 280, after: 80 } } }),
    new Table({ width: { size: 9506, type: WidthType.DXA }, columnWidths: [2200, 7306], rows: [
      new TableRow({ children: [hCell("风险等级", 2200), tCell(risk, 7306, { color: tc, bold: true })] }),
      new TableRow({ children: [hCell("审查维度", 2200), tCell(dimension, 7306)] }),
      new TableRow({ children: [hCell("原文摘录", 2200), tCell(excerpt, 7306)] }),
      new TableRow({ children: [hCell("命中规则", 2200), tCell(rule, 7306)] }),
      new TableRow({ children: [hCell("审查依据", 2200), mCell(bases, 7306)] }),
      new TableRow({ children: [hCell("修改建议", 2200), tCell(suggestion, 7306, { color: BLUE })] }),
    ]}),
  ];
}

// ===================== 读取输入 =====================
const inputPath = process.argv[2] || "review_input.json";
let D;
try {
  D = JSON.parse(fs.readFileSync(inputPath, "utf8"));
} catch (e) {
  console.error("[输入错误] 无法读取或解析 JSON：" + (e && e.message ? e.message : e));
  process.exit(1);
}
const M = D.meta || {};
const SUM = D.summary || {};
const mode = M.mode || "draft";
const RISK_LEVELS = ["🔴 高风险", "🟡 中风险", "🟢 低风险"];
const DIMENSIONS = ["合法合规", "真实准确", "风险提示", "信息完整", "公平诚信", "个人信息保护"];

function nonEmptyString(v) {
  return typeof v === "string" && v.trim().length > 0;
}

function validateInput() {
  const errors = [];
  if (!D || typeof D !== "object" || Array.isArray(D)) errors.push("顶层必须是 JSON 对象");
  if (!D.meta || typeof D.meta !== "object" || Array.isArray(D.meta)) errors.push("meta 必须是对象");
  if (!nonEmptyString(M.material)) errors.push("meta.material 为必填字符串");
  if (!["draft", "archive"].includes(mode)) errors.push("meta.mode 只能是 draft 或 archive");
  if (!Array.isArray(D.problems) || D.problems.length === 0) {
    errors.push("problems 必须是非空数组");
  } else {
    D.problems.forEach((pr, index) => {
      const at = `problems[${index}]`;
      if (!pr || typeof pr !== "object" || Array.isArray(pr)) {
        errors.push(`${at} 必须是对象`);
        return;
      }
      ["no", "title", "risk", "dimension", "excerpt", "rule", "suggestion"].forEach((key) => {
        if (pr[key] === undefined || pr[key] === null || String(pr[key]).trim() === "") {
          errors.push(`${at}.${key} 为必填字段`);
        }
      });
      if (pr.risk && !RISK_LEVELS.includes(pr.risk)) errors.push(`${at}.risk 取值不合法`);
      if (pr.dimension && !DIMENSIONS.includes(pr.dimension)) errors.push(`${at}.dimension 取值不合法`);
      if (!Array.isArray(pr.basis) || pr.basis.length === 0 || pr.basis.some((v) => !nonEmptyString(v))) {
        errors.push(`${at}.basis 必须是非空字符串数组`);
      }
    });
  }
  if (M.riskLevel && !RISK_LEVELS.includes(M.riskLevel)) errors.push("meta.riskLevel 取值不合法");
  if (D.remediation !== undefined && !Array.isArray(D.remediation)) {
    errors.push("remediation 必须是数组");
  } else {
    (D.remediation || []).forEach((r, index) => {
      if (!r || typeof r !== "object" || !RISK_LEVELS.includes(r.level)) {
        errors.push(`remediation[${index}].level 必须使用完整风险等级枚举`);
      }
    });
  }
  if (mode === "archive") {
    ["docNo", "date", "department", "submitter", "conclusion", "riskLevel"].forEach((key) => {
      if (!nonEmptyString(M[key])) errors.push(`归档模式下 meta.${key} 为必填字符串`);
    });
  }
  if (errors.length) {
    console.error("[输入校验失败]\n- " + errors.join("\n- "));
    process.exit(1);
  }
}

validateInput();
const docNo = M.docNo || "（待编号）";

// 默认输出文件名
function safeName(s) { return (s || "审查材料").replace(/[\\/:*?"<>|]/g, "_"); }
const outPath = process.argv[3] || `消保审查意见书_${safeName(M.material || "材料")}.docx`;

// ===================== 构建文档 =====================
const coverRows = [
  ["文档状态", mode === "archive" ? "正式归档" : "审阅草稿"],
  ["送审材料", M.material || "（待填）"],
  ["送审类型", M.type || "（待填）"],
  ["关联产品", M.product || "（待填）"],
  ["送审部门", M.department || "（待填）"],
  ["送审人", M.submitter || "（待填）"],
  ["审查时间", M.date || "（待填）"],
  ["审查结论", M.conclusion || "（待填）"],
  ["风险等级", M.riskLevel || "（待填）"],
];
// 素材来源：用于审查溯源（图片OCR(腾讯云) / 图片AI视觉 / 文字转录 / 文档读取）
if (M.source) coverRows.push(["素材来源", M.source]);
const coverColor = (label, val) => {
  if (label === "审查结论") return /\u274C|不通过/.test(val) ? { color: RED, bold: true } : { color: BLACK };
  if (label === "风险等级") return { color: riskColor(val), bold: true };
  return {};
};

const children = [];
// 封面
children.push(new Paragraph({ spacing: { before: 1200 } }));
children.push(p([new TextRun({ text: "消保审查意见书", bold: true, font: FONT, size: 48, color: BLUE })], { sp: { alignment: AlignmentType.CENTER } }));
children.push(p([new TextRun({ text: "金融营销宣传合规审查", font: FONT, size: 24, color: "666666" })], { sp: { alignment: AlignmentType.CENTER, spacing: { after: 80 } } }));
children.push(new Paragraph({ spacing: { before: 400 } }));
children.push(new Table({ width: { size: 9506, type: WidthType.DXA }, columnWidths: [3000, 6506], rows: coverRows.map(r =>
  new TableRow({ children: [hCell(r[0], 3000), tCell(r[1], 6506, coverColor(r[0], r[1]))] })
) }));
children.push(new Paragraph({ spacing: { before: 600 } }));

// 一、审查摘要
children.push(sTitle("一、审查摘要"));
if (SUM.intro) children.push(p(SUM.intro, { sp: { spacing: { after: 120 } } }));
if (SUM.high) children.push(pRuns([rBadge("🔴 高风险"), new TextRun({ text: `：${SUM.high}`, font: FONT, size: SZ })], { sp: { spacing: { after: 60 } } }));
if (SUM.mid) children.push(pRuns([rBadge("🟡 中风险"), new TextRun({ text: `：${SUM.mid}`, font: FONT, size: SZ })], { sp: { spacing: { after: 60 } } }));
if (SUM.low) children.push(pRuns([rBadge("🟢 低风险"), new TextRun({ text: `：${SUM.low}`, font: FONT, size: SZ })], { sp: { spacing: { after: 120 } } }));
if (SUM.core) children.push(p([new TextRun({ text: SUM.core, font: FONT, size: SZ, color: RED, bold: true })]));

// 二、审查发现
children.push(sTitle("二、审查发现"));
(D.problems || []).forEach(pr => {
  children.push(...problemSection(
    pr.no, pr.title, pr.risk, pr.dimension, pr.excerpt, pr.rule,
    pr.basis && pr.basis.length ? pr.basis : ["（待补充）"], pr.suggestion || "（待补充）"
  ));
});

// 三、总体评估
children.push(sTitle("三、总体评估"));
const ev = D.evaluation || [];
if (ev.length) {
  children.push(new Table({ width: { size: 9506, type: WidthType.DXA }, columnWidths: [3000, 1506, 5000], rows: [
    new TableRow({ children: [hCell("评估维度", 3000), hCell("评分", 1506), hCell("说明", 5000)] }),
    ...ev.map(e => new TableRow({ children: [
      tCell(e.dim, 3000),
      tCell(e.score, 1506, { color: (parseInt(e.score) <= 2 || /1\/5|2\/5/.test(e.score)) ? RED : BLACK, bold: /1\/5|2\/5/.test(e.score) }),
      tCell(e.note, 5000),
    ] })),
  ] }));
}
if (D.evaluationSummary) {
  children.push(pRuns([
    new TextRun({ text: "综合意见：", bold: true, font: FONT, size: SZ }),
    new TextRun({ text: D.evaluationSummary, font: FONT, size: SZ }),
  ], { sp: { spacing: { before: 200, after: 120 } } }));
}

// 四、整改要求
children.push(sTitle("四、整改要求"));
const rem = D.remediation || [];
if (rem.length) {
  children.push(new Table({ width: { size: 9506, type: WidthType.DXA }, columnWidths: [800, 4200, 1056, 1500, 1950], rows: [
    new TableRow({ children: [hCell("序号", 800, GRAY_BG), hCell("整改事项", 4200, GRAY_BG), hCell("等级", 1056, GRAY_BG), hCell("期限", 1500, GRAY_BG), hCell("责任人", 1950, GRAY_BG)] }),
    ...rem.map(r => new TableRow({ children: [
      tCell(String(r.no), 800),
      tCell(r.item, 4200),
      tCell(r.level, 1056, { color: riskColor(r.level), bold: true }),
      tCell(r.deadline || "（待定）", 1500),
      tCell(r.owner || "（待分配）", 1950, { color: GRAY }),
    ] })),
  ] }));
}
children.push(p([new TextRun({ text: "整改完成后请重新送审。", bold: true, font: FONT, size: SZ, color: RED })], { sp: { spacing: { before: 160 } } }));

// 五、审批记录
children.push(sTitle("五、审批记录"));
const appr = D.approvals || [
  { role: "审查人", name: "AI 消保审查助手", opinion: "见本意见书审查发现", date: M.date || "（待填）" },
  { role: "复核人", name: "（待填）", opinion: "（待填）", date: "（待填）" },
  { role: "审批人", name: "（待填）", opinion: "（待填）", date: "（待填）" },
];
children.push(new Table({ width: { size: 9506, type: WidthType.DXA }, columnWidths: [1200, 1500, 5000, 1806], rows: [
  new TableRow({ children: [hCell("角色", 1200), hCell("姓名", 1500), hCell("意见", 5000), hCell("日期", 1806)] }),
  ...appr.map(a => new TableRow({ children: [
    tCell(a.role, 1200),
    tCell(a.name || "（待填）", 1500, a.name === "（待填）" ? { color: GRAY } : {}),
    tCell(a.opinion || "（待填）", 5000, a.opinion === "（待填）" ? { color: GRAY } : {}),
    tCell(a.date || "（待填）", 1806, a.date === "（待填）" ? { color: GRAY } : {}),
  ] })),
] }));
children.push(new Paragraph({ spacing: { before: 400 } }));

// 脚注（免责声明，四要素，硬性渲染——S02）
children.push(p([new TextRun({ text: "免责声明：本《消保审查意见书》由 AI 消保审查助手基于公开法规与内置规则库（禁用词库、审查要点、精确法条映射、监管处罚判例）辅助生成，不构成法律意见或监管认定，亦不构成任何投资推荐；审查结论须经具备资质的人员或合规部门复核后方可采用。", font: FONT, size: 16, color: GRAY, italics: true })], {
  sp: { spacing: { before: 400 }, border: { top: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC", space: 8 } } }
}));
children.push(p([new TextRun({ text: "审查依据：国家金融监督管理总局等公开法规、营销宣传禁用词库、营销宣传审查要点（规则均随 Skill 内置，无需外部知识库；机构可接入自有知识库以增强覆盖）。", font: FONT, size: 16, color: GRAY, italics: true })], { sp: { spacing: { before: 40 } } }));

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: SZ } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: BLACK },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
    ]
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1200, bottom: 1440, left: 1200 } } },
    headers: {
      default: new Header({ children: [new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 4 } },
        children: [
          new TextRun({ text: "消保审查意见书", bold: true, font: FONT, size: SZ, color: BLUE }),
          new TextRun({ text: "\t\t编号：" + docNo, font: FONT, size: 16, color: GRAY }),
        ],
        tabStops: [{ type: "RIGHT", position: 9026 }]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "第 ", font: FONT, size: 16, color: GRAY }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: GRAY }),
          new TextRun({ text: " 页", font: FONT, size: 16, color: GRAY }),
        ]
      })] })
    },
    children,
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("OK -> " + outPath);
}).catch((e) => {
  console.error("[生成失败] " + (e && e.message ? e.message : e));
  process.exitCode = 1;
});
