# 同程程心 Skills 配置说明

> 💡 **提示**:本技能支持免费试用,无需配置 API Key 即可使用。
> 如需完整服务或试用资格失效后,请按以下方式配置 API Key。

## 配置方式(二选一)

### 方式一:环境变量(推荐,适用于 OpenClaw 平台)

在 OpenClaw 控制台的 Skills 配置页面填写 `CHENGXIN_API_KEY`,或编辑 `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "tc-chengxin": {
        "env": {
          "CHENGXIN_API_KEY": "你的 API Key"
        }
      }
    }
  }
}
```

或在 Shell 中设置环境变量:

```bash
export CHENGXIN_API_KEY="你的 API Key"
```

### 方式二:本地 config.json

在技能目录下创建 `config.json` 文件:

```json
{
  "apiKey": "你的 API Key"
}
```

---

## 接口地址

各 `scripts/*-query.js` 通过 `scripts/lib/api-client.js` 调用程心网关,**基础 URL** 为:

`https://wx.17u.cn/skills/gateway/api/v1/gateway`

具体资源在基础路径后拼接,例如 `/trainResource`、`/flightResource`、`/hotelResource` 等(与脚本内常量一致)。

## 网络要求

- 支持公网访问
- 无网络环境限制

## 获取鉴权信息

### 方式一:通过同程旅行 APP/小程序申领(推荐)

1. 打开 **同程旅行 APP** 或 **同程旅行小程序**(微信 - 我 - 服务 → 火车票机票/酒店民宿)
2. 在顶部搜索栏中搜索「**程心激活码**」
3. 按页面提示完成申领即可获取 API Key
4. 将申领页面上的 **程心激活码(API Key)** 复制到环境变量、配置文件或工具指定的位置即可使用

> 💡 **快捷方式**:也可以直接回复「**帮我把 xxxxx(激活码)配置到 tc-chengxin 这个 skill 上**」,助手会自动帮你完成配置。

### 方式二:联系同程程心大模型团队

如需企业级接入或批量使用,请联系同程程心大模型团队申请 API Key。

---

## 📞 客服支持

使用过程中遇到问题?同程旅行提供 7×24 小时服务:

- **📞 旅行者热线**:**95711**
- **💬 在线客服**:[https://www.ly.com/public/newhelp/CustomerService.html](https://www.ly.com/public/newhelp/CustomerService.html)

---

## 📝 输出格式规范

### 表格结构

所有查询结果使用 **Markdown 表格** 格式,包含以下列:

| 类型 | 列名 |
|------|------|
| 🏨 酒店 | 酒店名称、价格、类型、评分、评论数、特点、PC 预订、手机预订 |
| 🚄 火车票 | 车次、出发站、到达站、出发时间、到达时间、运行时长、最低价、PC 预订、手机预订 |
| ✈️ 机票 | 航班号、航空公司、出发机场、到达机场、出发时间、到达时间、运行时长、价格、PC 预订、手机预订 |
| 🏞️ 景区 | 景区名称、城市、星级、评分、价格、开放时间、PC 预订、手机预订 |

### 链接格式

- **PC 预订**:`[立即预订](pc_link)` - 桌面浏览器链接(`www.ly.com`)
- **手机预订**:`[立即预订](mobile_link)` - 移动端 H5 链接(`m.ly.com`)

### 底部引导语

表格下方统一添加:
> 💡 **更多选择**：也可以打开 **同程旅行 APP** 或在 **微信 - 我 - 服务** 中，点击 **火车票机票** 或 **酒店民宿** 查看更丰富的资源。

---

## 📦 响应结构

详见 `../SKILL.md` 中的响应结构说明。
