// 营销海报 / 图片 → 文字（腾讯云 OCR）
// 用法：node ocr_extract.js <image_path> [output.txt]
//   image_path : 本地图片（JPG / JPEG / PNG，最大 10 MiB）
//   output.txt : 输出路径（缺省打印到 stdout）
//
// 依赖：tencentcloud-sdk-nodejs-ocr  npm install tencentcloud-sdk-nodejs-ocr
// 授权：明确确认图片可上传后设置 OCR_UPLOAD_CONFIRMED=1
// 凭证：环境变量 TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY
//       可选 OCR_REGION（默认 ap-guangzhou）
//
// 行为：
//   1. 读取图片为 base64；
//   2. 调用腾讯云 GeneralAccurateOCR（高精度通用印刷体识别）；
//   3. 按 上→下、左→右 重组文字输出；
//   4. 未确认上传、未配置密钥或未安装 SDK 时打印兜底指引并以退出码 2 结束，
//      由上层（AI 视觉识别）转录，保证「图片素材」能力不中断。
//
// 退出码：0 成功 / 1 用法或文件错误 / 2 跳过（无密钥或 SDK 缺失）/ 3 OCR 调用失败

const fs = require("fs");
const path = require("path");

const IMG = process.argv[2];
const OUT = process.argv[3];

if (!IMG) {
  console.error("用法：node ocr_extract.js <image_path> [output.txt]");
  process.exit(1);
}
if (!fs.existsSync(IMG)) {
  console.error("图片不存在：" + IMG);
  process.exit(1);
}
const extension = path.extname(IMG).toLowerCase();
if (![".jpg", ".jpeg", ".png"].includes(extension)) {
  console.error("不支持的文件类型：仅支持 JPG / JPEG / PNG；PDF 请由文档读取能力处理。");
  process.exit(1);
}
if (fs.statSync(IMG).size > 10 * 1024 * 1024) {
  console.error("图片超过 10 MiB，请压缩或拆分后重试。");
  process.exit(1);
}

const SECRET_ID = process.env.TENCENTCLOUD_SECRET_ID;
const SECRET_KEY = process.env.TENCENTCLOUD_SECRET_KEY;
const REGION = process.env.OCR_REGION || "ap-guangzhou";

function fallback(reason) {
  console.error("[OCR 跳过] " + reason);
  console.error("[兜底] 请改由平台的图片视觉能力在当前会话内转录，或完成授权与配置后重试。");
  process.exit(2);
}

if (process.env.OCR_UPLOAD_CONFIRMED !== "1") {
  fallback("尚未获得将图片上传至腾讯云 OCR 的明确授权；确认后设置 OCR_UPLOAD_CONFIRMED=1。");
}

if (!SECRET_ID || !SECRET_KEY) {
  fallback("未检测到腾讯云密钥（TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY）。");
}

let OcrClient;
try {
  OcrClient = require("tencentcloud-sdk-nodejs-ocr").ocr.v20181119.Client;
} catch (e) {
  fallback("未安装 tencentcloud-sdk-nodejs-ocr，请先 npm install tencentcloud-sdk-nodejs-ocr。");
}

const imageBase64 = fs.readFileSync(IMG).toString("base64");

const client = new OcrClient({
  credential: { secretId: SECRET_ID, secretKey: SECRET_KEY },
  region: REGION,
  profile: { httpProfile: { endpoint: "ocr.tencentcloudapi.com" } },
});

client.GeneralAccurateOCR({ ImageBase64: imageBase64 }).then((r) => {
  const items = (r && r.TextDetections) || [];
  // 按 上→下、左→右 排序重组行（Polygon 为左上角坐标）
  const sorted = items.slice().sort((a, b) => {
    const ay = (a.Polygon && a.Polygon.Y) || 0;
    const by = (b.Polygon && b.Polygon.Y) || 0;
    if (Math.abs(ay - by) > 8) return ay - by;
    const ax = (a.Polygon && a.Polygon.X) || 0;
    const bx = (b.Polygon && b.Polygon.X) || 0;
    return ax - bx;
  });
  const text = sorted.map((it) => it.DetectedText || "").join("\n");
  const out =
    "【OCR 来源】" + path.basename(IMG) +
    "（腾讯云 GeneralAccurateOCR，region=" + REGION + "，文本块=" + items.length + "）\n" +
    "【识别文字】\n" + text + "\n";
  if (OUT) {
    fs.writeFileSync(OUT, out);
    console.log("OK -> " + OUT + " （" + items.length + " 个文本块）");
  } else {
    process.stdout.write(out);
  }
}).catch((e) => {
  console.error("[OCR 失败] " + (e && e.message ? e.message : e));
  process.exit(3);
});
