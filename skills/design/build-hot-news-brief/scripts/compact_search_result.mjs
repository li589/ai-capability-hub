#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const TRACKING = new Set(["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "from", "source", "spm", "ref"]);

function argumentsOf(argv) {
  const result = { topic: "", now: new Date(), files: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--topic") result.topic = argv[++index] ?? "";
    else if (value === "--now") result.now = new Date(argv[++index] ?? "");
    else if (value === "--input") result.files.push(argv[++index] ?? "");
    else result.files.push(value);
  }
  result.files = result.files.filter(Boolean);
  if (!result.files.length) throw new Error("at_least_one_input_file_required");
  if (Number.isNaN(result.now.getTime())) throw new Error("invalid_now");
  return result;
}

function collectPages(value, output, depth = 0) {
  if (depth > 12 || value == null) return;
  if (typeof value === "string") {
    const text = value.trim();
    if ((text.startsWith("{") && text.endsWith("}")) || (text.startsWith("[") && text.endsWith("]"))) {
      try { collectPages(JSON.parse(text), output, depth + 1); } catch { /* ignore non-JSON text */ }
    }
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectPages(item, output, depth + 1);
    return;
  }
  if (typeof value !== "object") return;
  if (Array.isArray(value.webPages?.value)) output.push(...value.webPages.value);
  for (const [key, child] of Object.entries(value)) {
    if (key !== "webPages") collectPages(child, output, depth + 1);
  }
}

function compactText(value, limit = 240) {
  return String(value ?? "").replace(/\s+/gu, " ").trim().slice(0, limit);
}

function normalizedUrl(value) {
  try {
    const parsed = new URL(String(value ?? ""));
    if (!/^https?:$/u.test(parsed.protocol)) return null;
    for (const key of [...parsed.searchParams.keys()]) if (TRACKING.has(key.toLowerCase())) parsed.searchParams.delete(key);
    parsed.hash = "";
    return parsed.toString();
  } catch {
    return null;
  }
}

function comparable(value) {
  return String(value ?? "").toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
}

function features(value) {
  const normalized = comparable(value);
  const result = new Set();
  if (normalized) result.add(normalized);
  for (let index = 0; index < normalized.length - 1; index += 1) result.add(normalized.slice(index, index + 2));
  return result;
}

function relevance(topic, page) {
  const wanted = features(topic.replace(/(?:使用|快速|深度|模式|搜索|最近|热点|新闻|有什么)/gu, ""));
  if (!wanted.size) return 0;
  const content = features(`${page.title}${page.snippet}`);
  let matches = 0;
  for (const token of wanted) if (content.has(token)) matches += token.length > 2 ? 3 : 1;
  return matches;
}

function compactPage(page, topic, now) {
  const title = compactText(page?.name ?? page?.title, 180);
  const url = normalizedUrl(page?.url);
  const published = new Date(page?.datePublished ?? "");
  if (!title || !url || Number.isNaN(published.getTime())) return null;
  const age = now.getTime() - published.getTime();
  if (age < 0 || age > 7 * 24 * 60 * 60 * 1000) return null;
  const parsed = new URL(url);
  const snippet = compactText(page?.snippet ?? page?.summary, 240);
  const result = {
    title,
    url,
    domain: parsed.hostname.toLowerCase().replace(/^www\./u, ""),
    source: compactText(page?.siteName ?? page?.source ?? parsed.hostname, 80),
    datePublished: published.toISOString(),
    snippet,
  };
  return { ...result, relevance: relevance(topic, result) };
}

function main() {
  const args = argumentsOf(process.argv.slice(2));
  const pages = [];
  const errors = [];
  for (const file of args.files) {
    try { collectPages(JSON.parse(fs.readFileSync(file, "utf8")), pages); }
    catch { errors.push(path.basename(file)); }
  }
  const unique = new Map();
  for (const page of pages) {
    const compact = compactPage(page, args.topic, args.now);
    if (!compact) continue;
    const titleKey = comparable(compact.title);
    if (!unique.has(compact.url) && ![...unique.values()].some((item) => comparable(item.title) === titleKey)) unique.set(compact.url, compact);
  }
  const ranked = [...unique.values()].sort((left, right) => right.relevance - left.relevance || right.datePublished.localeCompare(left.datePublished));
  const domainCounts = new Map();
  const items = [];
  for (const item of ranked) {
    const count = domainCounts.get(item.domain) ?? 0;
    if (count >= 2) continue;
    domainCounts.set(item.domain, count + 1);
    items.push(item);
    if (items.length === 40) break;
  }
  console.log(JSON.stringify({ raw_count: pages.length, compact_count: items.length, parse_errors: errors, items }));
}

try { main(); } catch (error) { console.error(`compact_search_result_failed: ${error.message}`); process.exitCode = 1; }
