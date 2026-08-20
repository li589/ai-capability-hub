#!/usr/bin/env node

import { fileURLToPath } from 'node:url';

const ENDPOINT = 'https://proxy.finance.qq.com/cgi/cgi-bin/openai/openclaw/proxy';
const ROUTE = 'doc_list_get';
const SCRIPT = fileURLToPath(import.meta.url);

function printUsage() {
  console.error(`用法: node ${SCRIPT} query "关键词组1" "关键词组2"`);
  console.error('说明: 每个位置参数会成为 params.keywords 数组的一个元素，可传关键词组或文档 ID。');
  console.error(`帮助: node ${SCRIPT} --help`);
}

function parseArgs(argv) {
  if (argv.length === 1 && (argv[0] === '--help' || argv[0] === '-h')) {
    printUsage();
    process.exit(0);
  }

  const [command, ...rawKeywords] = argv;

  if (command === '--help' || command === '-h') {
    printUsage();
    process.exit(0);
  }

  if (command !== 'query') {
    console.error(`[westock-finsearch] 只支持子命令 query，不支持 ${command || '(空命令)'}`);
    printUsage();
    process.exit(1);
  }

  if (rawKeywords.length === 1 && (rawKeywords[0] === '--help' || rawKeywords[0] === '-h')) {
    printUsage();
    process.exit(0);
  }

  const keywords = rawKeywords.map((item) => item.trim());

  if (keywords.length === 0 || keywords.some((item) => item.length === 0)) {
    console.error('[westock-finsearch] query 后至少传入 1 组非空关键词或文档 ID。');
    printUsage();
    process.exit(1);
  }

  if (keywords.length > 5) {
    console.error(`[westock-finsearch] 警告: 当前传入 ${keywords.length} 组，建议一次 1-5 组以控制结果规模。`);
  }

  return keywords;
}

function getToken() {
  const token = process.env.WZQ_APIKEY || '2ca3e9f70160d329540e549ca08d1e463a9991884a79fb20e940f03985406eb7';

  if (!token) {
    console.error('[westock-finsearch] 环境变量 WZQ_APIKEY 未注入，无法发起查询。');
    process.exit(1);
  }

  return token;
}

async function requestFinSearch(keywords) {
  const response = await fetch(ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      route: ROUTE,
      token: getToken(),
      params: {
        keywords,
      },
    }),
  });

  const bodyText = await response.text();

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${bodyText.slice(0, 500)}`);
  }

  try {
    return JSON.parse(bodyText);
  } catch (error) {
    throw new Error(`接口返回非 JSON 内容: ${bodyText.slice(0, 500)}`);
  }
}

async function main() {
  const keywords = parseArgs(process.argv.slice(2));
  const result = await requestFinSearch(keywords);

  if (result.code !== 0) {
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  }

  const content = result?.data?.content;

  if (typeof content === 'string') {
    process.stdout.write(content);
    return;
  }

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(`[westock-finsearch] 查询失败: ${error.message}`);
  printUsage();
  process.exit(1);
});
