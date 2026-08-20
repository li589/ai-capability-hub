---
name: 浏览器自动化助手
slug: browser-auto
displayName: 浏览器自动化助手
description: 全面的浏览器自动化操作指南。覆盖网页自动化操作(点击/填写表单/截图)、多标签页管理、登录流程、文件上传下载、网页数据抓取等。适用于 OpenClaw/Playwright/Selenium 等自动化框架。
trigger:
  - 浏览器自动化
  - 网页自动化
  - 自动操作网页
  - 爬虫
  - 表单填写
  - 网页截图
  - 浏览器
  - 自动化测试
  - web自动化
  - selenium
category: 开发工具
tags: [浏览器自动化, 网页爬虫, 自动化测试, Playwright, Selenium, 网页操作, 数据采集]
version: 1.0.0
source: openclaw/openclaw (browser-automation)
source_url: https://github.com/openclaw/openclaw/tree/main/extensions/browser/skills/browser-automation
original_stars: 378675
---

# 浏览器自动化助手

## 概述

全面的浏览器自动化操作指南。基于 SkillsMP 上 ⭐378K 的超热门浏览器自动化技能汉化增强，适配国内网页生态和常用自动化工具。

本技能在以下场景自动触发：
- 用户需要进行网页自动化操作
- 需要填写表单或模拟用户交互
- 需要多标签页管理
- 需要网页截图和信息采集
- 需要自动化登录流程
- 需要文件上传/下载自动化

## 使用说明

浏览器自动化的核心操作模式：

### 1. 导航与等待
```javascript
// 导航到页面
await page.goto('https://example.com', { waitUntil: 'networkidle' });

// 等待元素出现
await page.waitForSelector('.content-loaded', { timeout: 10000 });

// 等待网络请求完成
await page.waitForResponse(response => response.url().includes('/api/data'));

// 自定义等待条件
await page.waitForFunction(() => document.querySelectorAll('.item').length > 10);
```

### 2. 元素交互
```javascript
// 点击（优先使用语义化选择器）
await page.click('text=提交');
await page.click('[data-testid="submit-btn"]');
await page.click('button:has-text("确认订单")');

// 输入文本
await page.fill('#username', 'test_user');
await page.type('#search', '关键词', { delay: 50 });  // 模拟真人输入

// 选择选项
await page.selectOption('#city', '北京');

// 悬停
await page.hover('.dropdown-trigger');

// 拖拽
await page.dragAndDrop('#source', '#target');
```

### 3. 多标签管理
```javascript
// 打开新标签
const newPage = await context.newPage();
await newPage.goto('https://example.com/2');

// 切换标签
await page.bringToFront();

// 获取所有标签
const pages = context.pages();

// 关闭标签
await page.close();

// 等待新标签打开
const [newPage] = await Promise.all([
  context.waitForEvent('page'),
  page.click('a[target="_blank"]'),
]);
```

### 4. 数据采集
```javascript
// 提取单个元素
const title = await page.textContent('h1');

// 提取多个元素
const items = await page.$$eval('.product-item', elements =>
  elements.map(el => ({
    name: el.querySelector('.name')?.textContent?.trim(),
    price: el.querySelector('.price')?.textContent?.trim(),
    link: el.querySelector('a')?.href,
  }))
);

// 提取表格数据
const tableData = await page.$$eval('table tr', rows =>
  rows.map(row =>
    Array.from(row.querySelectorAll('td, th')).map(cell => cell.textContent?.trim())
  )
);

// 获取页面全部文本
const text = await page.evaluate(() => document.body.innerText);

// 截图
await page.screenshot({ path: 'screenshot.png', fullPage: true });
```

### 5. 登录与认证
```javascript
// Cookie 管理
const cookies = await page.cookies();
await page.setCookie(...cookies);

// 本地存储
await page.evaluate(() => {
  localStorage.setItem('token', 'xxx');
});

// 表单登录
await page.fill('#username', 'user');
await page.fill('#password', 'pass');
await page.click('button[type="submit"]');
await page.waitForNavigation();
```

### 6. 文件操作
```javascript
// 文件上传
const fileInput = await page.$('input[type="file"]');
await fileInput.setInputFiles('/path/to/file.pdf');

// 文件下载
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.click('a#download-btn'),
]);
await download.saveAs('/path/to/save/file.pdf');
```

### 7. 错误处理
```javascript
// 超时处理
try {
  await page.waitForSelector('.dynamic-content', { timeout: 5000 });
} catch (error) {
  console.log('元素未找到，尝试备选方案...');
  // 备选方案
}

// 页面异常捕获
page.on('pageerror', error => {
  console.error('页面JS错误:', error.message);
});

// 请求失败重试
page.on('requestfailed', request => {
  console.error('请求失败:', request.url(), request.failure()?.errorText);
});
```

## 触发关键词
- "自动登录这个网站"
- "帮我把这个表单填了"
- "抓取这个页面的数据"
- "页面截个图"
- "自动化操作这个流程"
- "批量处理网页"
- "帮我在网页上点一下"
- "爬取这个网站"
- "网页数据采集"

## 最佳实践

1. **优先语义化选择器**：text=、data-testid、role 优于 CSS/XPath
2. **避免脆弱的定位**：不用索引依赖的选择器（`:nth-child(3)`）
3. **操作前等待就绪**：每个交互前等待目标元素出现
4. **验证操作结果**：操作后验证预期结果，而非假设成功
5. **错误恢复**：设计超时和异常处理机制
6. **反检测策略**：合理延迟（100-300ms 随机）、调整 User-Agent
7. **资源管理**：用完关闭浏览器实例，避免内存泄漏

## 注意事项
- 遵守网站的 robots.txt 和使用条款
- 合理设置请求频率，避免对服务器造成压力
- 注意登录凭证安全，不硬编码密码/Token
- 处理验证码/滑块时需人类介入
- 不用于破解、撞库、批量注册等非法行为
- 微信/淘宝等网站的自动化需特别注意风控机制
- 国内网站可能有更严格的反爬措施（字体反爬、CSS 偏移等）
- 建议配合浏览器自动化工具（Playwright/Selenium/Puppeteer）使用