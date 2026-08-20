// 一站式生成"鹅厂辟谣助手"分享卡片（1080×1080 方图）
// 跨平台支持 Windows / macOS / Linux
// 用法:
//   node gen-share-card.js --title "标题" --verdict "fake|true|partial|unverified" --summary "结论摘要" --out card.png
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { execSync } = require('child_process');

// 跨平台 Chrome / Edge / Chromium 路径自动探测
function detectBrowser() {
  const platform = process.platform;
  const candidates = [];

  if (platform === 'win32') {
    candidates.push(
      'C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      path.join(os.homedir(), 'AppData/Local/Google/Chrome/Application/chrome.exe'),
      path.join(os.homedir(), 'AppData/Local/Microsoft/Edge/Application/msedge.exe'),
    );
  } else if (platform === 'darwin') {
    candidates.push(
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
      path.join(os.homedir(), 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
    );
    // 还可以用 mdfind / which 兜底
    try {
      const which = execSync('which google-chrome chromium chrome 2>/dev/null || true', { encoding: 'utf8' }).trim();
      if (which) which.split(/\r?\n/).forEach(p => p && candidates.push(p));
    } catch (_) {}
  } else {
    // linux
    candidates.push(
      '/usr/bin/google-chrome',
      '/usr/bin/google-chrome-stable',
      '/usr/bin/chromium',
      '/usr/bin/chromium-browser',
      '/usr/bin/microsoft-edge',
      '/snap/bin/chromium',
    );
  }

  for (const p of candidates) {
    try { if (p && fs.existsSync(p)) return p; } catch (_) {}
  }
  return null;
}

// Logo 路径：用 __dirname 解析，跨平台
const LOGO_PATH = path.join(__dirname, 'assets', 'xiaop-logo-200.png');

function parseArgs() {
  const args = {};
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      args[key] = argv[i + 1];
      i++;
    }
  }
  return args;
}

const VERDICT_MAP = {
  fake:       { color: '#e74c3c', icon: '✗', text: '谣言' },
  true:       { color: '#27ae60', icon: '✓', text: '属实' },
  partial:    { color: '#f39c12', icon: '⚠', text: '部分失实' },
  unverified: { color: '#7f8c8d', icon: '?', text: '待核实' },
};

function buildHTML({ title, verdict, verdictText, summary, logoDataURL }) {
  const v = VERDICT_MAP[verdict] || VERDICT_MAP.unverified;
  const label = verdictText || v.text;
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  *{margin:0;padding:0;box-sizing:border-box;-webkit-font-smoothing:antialiased;}
  html,body{width:1080px;height:1080px;}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI Emoji","Apple Color Emoji",sans-serif;
    background:#f0f2f5;
  }
  .card{
    position:relative;
    width:1080px;height:1080px;background:#fff;
    display:flex;flex-direction:column;
  }
  .title-band{
    height:270px;
    background:rgba(178,220,252,0.35);
    padding:0 88px;
    display:flex;align-items:center;
    position:relative;
  }
  .title-band::before{
    content:"";
    position:absolute;
    left:44px;top:50%;transform:translateY(-50%);
    width:8px;height:96px;
    background:#0A2540;
    border-radius:4px;
  }
  .title{
    font-weight:900;color:#0A2540;
    letter-spacing:2px;
    overflow:hidden;
    text-align:left;
    width:100%;
    padding-left:24px;
    line-height:1.25;
  }
  .answer{
    flex:1;display:flex;flex-direction:column;justify-content:center;
    padding:56px 88px 0 88px;
  }
  .body{
    font-size:48px;line-height:1.85;color:#2c2c2c;
    letter-spacing:1.5px;
    text-align:justify;
  }
  .verdict{
    font-size:58px;font-weight:900;margin-right:8px;
    color:${v.color};
    letter-spacing:1px;
    white-space:nowrap;
  }
  .footer-wrap{ padding:0 88px 56px 88px; }
  .divider{height:1px;background:#ececec;margin:0 0 28px 0;}
  .footer{display:flex;align-items:center;gap:24px;}
  .logo{width:80px;height:80px;border-radius:50%;object-fit:cover;flex-shrink:0;}
  .footer-title{font-size:30px;font-weight:700;color:#1a1a1a;margin-bottom:6px;letter-spacing:0.5px;}
  .footer-sub{font-size:22px;color:#999;letter-spacing:0.5px;}
</style>
</head>
<body>
  <div class="card">
    <div class="title-band">
      <div class="title" id="title">${escapeHTML(title)}</div>
    </div>
    <div class="answer">
      <div class="body">
        <span class="verdict">【${v.icon} ${escapeHTML(label)}】</span>${escapeHTML(summary)}
      </div>
    </div>
    <div class="footer-wrap">
      <div class="divider"></div>
      <div class="footer">
        <img class="logo" src="${logoDataURL}" alt="logo">
        <div>
          <div class="footer-title">鹅厂辟谣助手 Skill</div>
          <div class="footer-sub">腾讯相关信息，来这里查真假</div>
        </div>
      </div>
    </div>
  </div>
  <script>
    (function(){
      const el = document.getElementById('title');
      const maxWidth = 880;
      const maxHeight = 240;
      const MAX_FONT = 128;
      const MIN_FONT = 64;

      el.style.whiteSpace = 'nowrap';
      let size = MAX_FONT;
      el.style.fontSize = size + 'px';
      while (el.scrollWidth > maxWidth && size > 72) {
        size -= 2;
        el.style.fontSize = size + 'px';
      }
      if (el.scrollWidth <= maxWidth) {
        document.body.dataset.ready = '1';
        return;
      }
      el.style.whiteSpace = 'normal';
      el.style.wordBreak = 'break-word';
      size = MAX_FONT;
      el.style.fontSize = size + 'px';
      while ((el.scrollHeight > maxHeight || el.scrollWidth > maxWidth) && size > MIN_FONT) {
        size -= 2;
        el.style.fontSize = size + 'px';
      }
      document.body.dataset.ready = '1';
    })();
  </script>
</body>
</html>`;
}

function escapeHTML(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

async function main() {
  const args = parseArgs();
  const out = path.resolve(args.out || 'share-card.png');

  // 检查logo
  if (!fs.existsSync(LOGO_PATH)) {
    console.error('Logo not found:', LOGO_PATH);
    process.exit(2);
  }
  const logoDataURL = 'data:image/png;base64,' + fs.readFileSync(LOGO_PATH).toString('base64');

  const html = buildHTML({
    title: args.title || '请提供 --title',
    verdict: args.verdict || 'fake',
    verdictText: args['verdict-text'],
    summary: args.summary || '请提供 --summary',
    logoDataURL,
  });

  // 临时HTML放在 OS 临时目录（跨平台）
  const tmpHTML = path.join(os.tmpdir(), `xiaop-card-${process.pid}-${Date.now()}.html`);
  fs.writeFileSync(tmpHTML, html, 'utf8');

  const exe = detectBrowser();
  if (!exe) {
    console.error('未找到 Chrome/Edge/Chromium。');
    console.error('Windows: 请确认安装了 Chrome 或 Edge');
    console.error('macOS:   请确认 /Applications/Google Chrome.app 存在');
    console.error('Linux:   请确认 /usr/bin/google-chrome 或 chromium 已安装');
    try { fs.unlinkSync(tmpHTML); } catch(_) {}
    process.exit(3);
  }

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: exe,
      headless: 'new',
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });
    // file:// URL 跨平台拼接
    const fileUrl = 'file://' + (process.platform === 'win32'
      ? '/' + tmpHTML.replace(/\\/g, '/')
      : tmpHTML);
    await page.goto(fileUrl, { waitUntil: 'networkidle0' });
    await page.waitForFunction('document.body.dataset.ready === "1"', { timeout: 5000 });
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
    console.log('Saved:', out);
  } catch (e) {
    console.error('Render failed:', e.message);
    process.exit(4);
  } finally {
    if (browser) try { await browser.close(); } catch(_) {}
    try { fs.unlinkSync(tmpHTML); } catch(_) {}
  }
}
main().catch(e => { console.error(e); process.exit(1); });
