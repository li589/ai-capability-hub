#!/usr/bin/env node
/**
 * PPT Craft Master v2 — conservative PPTX QA
 *
 * Usage:
 *   npm install
 *   node scripts/check-overflow.js deck.pptx
 *
 * Checks:
 * 1. text box bounds
 * 2. text geometry overflow (conservative width estimate)
 * 3. normAutofit dependency
 * 4. suspiciously small text
 * 5. placeholder / TODO text
 *
 * This is a QA estimator, not a PowerPoint rendering engine.
 * Visual rendering remains mandatory before delivery.
 */

const fs = require('fs');
const JSZip = require('jszip');

const file = process.argv[2];
if (!file) {
  console.error('Usage: node scripts/check-overflow.js deck.pptx');
  process.exit(2);
}

const EMU = 914400;
const PT_PER_IN = 72;
const W = 13.333;
const H = 7.5;
const SAFE = { left: 0.5, right: 0.5, top: 0.4, bottom: 0.4 };

function attr(tag, name, fallback = null) {
  const m = tag.match(new RegExp(`${name}="([^"]+)"`));
  return m ? m[1] : fallback;
}

function stripXml(s) {
  return s.replace(/<a:tab\/>/g, ' ')
    .replace(/<a:br\/>/g, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'");
}

function estimateCharUnits(text) {
  let units = 0;
  for (const ch of text) {
    if (ch === '\n' || ch === '\r') continue;
    const cp = ch.codePointAt(0);
    if (/\s/.test(ch)) units += 0.30;
    else if (/[0-9A-Za-z]/.test(ch)) units += 0.55;
    else if (
      (cp >= 0x2E80 && cp <= 0x9FFF) ||
      (cp >= 0xAC00 && cp <= 0xD7AF) ||
      (cp >= 0xF900 && cp <= 0xFAFF) ||
      (cp >= 0xFF01 && cp <= 0xFF60)
    ) units += 1.0;
    else units += 0.70;
  }
  return units;
}

function parseTextFrames(xml) {
  const frames = [];
  const blocks = xml.match(/<p:sp>[\s\S]*?<\/p:sp>/g) || [];

  for (const block of blocks) {
    const xfrm = block.match(/<a:xfrm>[\s\S]*?<\/a:xfrm>/);
    if (!xfrm) continue;
    const off = xfrm[0].match(/<a:off x="(\d+)" y="(\d+)"\/>/);
    const ext = xfrm[0].match(/<a:ext cx="(\d+)" cy="(\d+)"\/>/);
    if (!off || !ext) continue;

    const x = +off[1] / EMU, y = +off[2] / EMU;
    const w = +ext[1] / EMU, h = +ext[2] / EMU;

    const bodyPr = block.match(/<a:bodyPr[^>]*>/)?.[0] || '';
    const lIns = +(attr(bodyPr, 'lIns', '91440')) / EMU;
    const rIns = +(attr(bodyPr, 'rIns', '91440')) / EMU;
    const tIns = +(attr(bodyPr, 'tIns', '91440')) / EMU;
    const bIns = +(attr(bodyPr, 'bIns', '91440')) / EMU;

    const normAutofit = /<a:bodyPr[^>]*normAutofit/.test(block);
    const text = stripXml((block.match(/<p:txBody>[\s\S]*?<\/p:txBody>/)?.[0] || '')).trim();
    if (!text) continue;

    const paras = block.match(/<a:p>[\s\S]*?<\/a:p>/g) || [];
    let requiredPt = 0;
    let maxFont = 0;

    for (let i = 0; i < paras.length; i++) {
      const p = paras[i];
      const texts = [...p.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)].map(m => m[1]);
      const t = texts.join('');
      if (!t) continue;

      // Use the largest explicit run size; otherwise default to 18pt.
      const sizes = [...p.matchAll(/(?:<a:rPr|<a:defRPr)[^>]*sz="(\d+)"/g)].map(m => +m[1] / 100);
      const fs = sizes.length ? Math.max(...sizes) : 18;
      maxFont = Math.max(maxFont, fs);

      const usableWIn = Math.max(0.05, w - lIns - rIns);
      const charsPerLine = Math.max(1, Math.floor((usableWIn * PT_PER_IN) / (fs * 0.92)));
      const units = estimateCharUnits(t);
      const lines = Math.max(1, Math.ceil(units / charsPerLine));

      let mult = 1.0;
      const pct = p.match(/<a:spcPct val="(\d+)"/);
      const pts = p.match(/<a:spcPts val="(\d+)"/);
      if (pct) mult = +pct[1] / 100000;
      else if (pts) mult = Math.max(1, (+pts[1] / 100) / fs);

      let after = 0;
      const aft = p.match(/<a:spcAft>[\s\S]*?<\/a:spcAft>/)?.[0];
      if (aft) {
        const ap = aft.match(/<a:spcPts val="(\d+)"/);
        const ac = aft.match(/<a:spcPct val="(\d+)"/);
        if (ap) after = +ap[1] / 100;
        else if (ac) after = (+ac[1] / 100000) * fs;
      }

      requiredPt += lines * fs * mult;
      if (i < paras.length - 1) requiredPt += after;
    }

    frames.push({ x, y, w, h, lIns, rIns, tIns, bIns, normAutofit, text, maxFont, requiredPt });
  }
  return frames;
}

(async () => {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const slideNames = Object.keys(zip.files)
    .filter(n => /^ppt\/slides\/slide\d+\.xml$/.test(n))
    .sort((a,b) => {
      const na = +(a.match(/slide(\d+)/)||[])[1];
      const nb = +(b.match(/slide(\d+)/)||[])[1];
      return na - nb;
    });

  const issues = [];
  let textFrames = 0;

  for (const name of slideNames) {
    const slideNo = +(name.match(/slide(\d+)/)||[])[1];
    const xml = await zip.file(name).async('string');
    const frames = parseTextFrames(xml);
    textFrames += frames.length;

    for (const f of frames) {
      const label = f.text.replace(/\s+/g, ' ').slice(0, 50);

      if (f.x < SAFE.left - 0.01 || f.y < SAFE.top - 0.01 ||
          f.x + f.w > W - SAFE.right + 0.01 ||
          f.y + f.h > H - SAFE.bottom + 0.01) {
        issues.push({ level: 'ERROR', slide: slideNo, msg: `text box outside safe area: "${label}"` });
      }

      const usableHIn = Math.max(0, f.h - f.tIns - f.bIns);
      const availablePt = usableHIn * PT_PER_IN;
      if (f.requiredPt > availablePt + 0.5) {
        issues.push({
          level: f.normAutofit ? 'ERROR' : 'ERROR',
          slide: slideNo,
          msg: `${f.normAutofit ? 'text depends on normAutofit and is still estimated to overflow' : 'estimated hard overflow'}: "${label}" (${f.requiredPt.toFixed(1)}pt > ${availablePt.toFixed(1)}pt)`
        });
      }

      if (f.maxFont > 0 && f.maxFont < 12) {
        issues.push({ level: 'WARN', slide: slideNo, msg: `very small text (${f.maxFont}pt): "${label}"` });
      }

      if (/\b(TODO|FIXME|PLACEHOLDER|待补充|待完善|占位符)\b/i.test(f.text)) {
        issues.push({ level: 'ERROR', slide: slideNo, msg: `placeholder/debug text detected: "${label}"` });
      }
    }
  }

  console.log(`PPT Craft Master v2 QA`);
  console.log(`Slides: ${slideNames.length} | Text frames: ${textFrames}`);
  console.log(`Errors: ${issues.filter(x => x.level === 'ERROR').length} | Warnings: ${issues.filter(x => x.level === 'WARN').length}`);

  for (const i of issues) console.log(`[${i.level}] Slide ${i.slide}: ${i.msg}`);

  process.exit(issues.some(x => x.level === 'ERROR') ? 2 : 0);
})().catch(err => {
  console.error('QA failed:', err.message);
  process.exit(3);
});
