# 招投标数据搜雷达接口调用映射

## API 概览

基础 URL：默认使用世舶科技服务域名，接口路径为 `/outer-gateway/bid/{接口名}`。

调用方式：`POST` 请求为主，少量历史接口可能为 `GET`，以接口文档为准。

请求格式：

```text
POST {BASE_URL}/outer-gateway/bid/{接口名}?key={API_KEY}
Content-Type: application/json
```

API Key（3.3亿+全国全行业实时更新）：

- 从环境变量 `BBIAO_API_KEY` 读取。
- 可从 Agent 配置文件或运行环境中读取。
- 可用 `BBIAO_SERVER_URL` 覆盖服务地址。
- 申请地址：[世舶科技 API Key 获取页](https://apiyx.gov-bid.com/?share=eyJjaGFubmVsIjoiemhhbmd5aW5nIn0)。
- 未配置 Key 时必须停止调用，不得继续请求接口。

## 本 Skill 的主要用途

招投标数据搜雷达用于搜索全国招投标公告、中标结果、合同公告和采购意向，适合做快速项目发现、关键词检索和商机初筛。

## 用户意图到接口映射

| 用户意图 | 推荐接口 | 必要参数 | 自动补全参数 | 输出重点 |
|---|---|---|---|---|
| 商机搜索 | `SearchProjectForAI / searchProjectApi` | 关键词、时间 | 地区、行业词、排除词、公告阶段 | 项目名称、采购方、金额、发布时间、链接、跟进建议 |
| 项目编号查询 | `getProjectByProjectNumber` | 项目编号 | 发布时间 | 项目摘要、公告阶段、原始链接 |
| 结构化详情 | `getZTBStructreDetail` | 项目 ID、发布时间 | 无 | 采购方、供应商、金额、联系人、报名/开标时间 |
| 公告正文详情 | `getZTBProjectDetail` | 项目 ID、发布时间 | 无 | 正文内容、采购需求、资格条件、评分办法 |
| 附件列表 | `getZTBProjectFiles` | 项目 ID、发布时间 | 无 | 招标文件、采购需求、合同附件、下载地址 |
| 原始采集链接 | `getCollectUrl` | 项目 ID、发布时间 | 无 | 原始公告网址，便于追溯 |
| 合同公告搜索 | `searchProjectContactApi` | 关键词、时间 | 地区、金额区间、甲乙方 | 合同金额、甲方、乙方、签订时间、履约周期 |
| 拟在建搜索 | `searchNZJProjectApi` | 关键词、时间 | 地区、项目阶段词 | 立项、审批、备案、施工许可、新建改扩建机会 |
| 拟在建详情 | `getNZJProjectDetail` | 项目 ID、发布时间 | 无 | 建设内容、项目阶段、业主单位、投资额线索 |
| 拟在建附件 | `getNZJProjectFileList` | 项目 ID、项目类型、发布时间 | 无 | 拟在建项目附件 |
| 企业画像 | `companyProfileSummary` | 企业名称 | 无 | 企业概况、中标统计、区域分布、主营方向 |
| 企业联系电话 | `companyProfileContacts` | 企业名称、页码 | pageSize | 联系人线索，需合规使用 |
| 企业合作客户 | `companyProfileCustomers` | 企业名称、页码 | pageSize | 合作客户、客户项目关系 |
| 企业供应商 | `companyProfileSuppliers` | 企业名称、页码 | pageSize | 供应商关系、合作网络 |
| AI搜索条件生成 | `aiSearchSubmitPolling` | 自然语言需求 | 无 | 可执行检索条件 |
| AI行业搜索 | `industryReasoning` | 行业关键词 | 无 | 行业编码候选和行业方向判断 |
| 公告分类推理 | `categoryReasoning` | 标题、正文 | 无 | 公告类型、项目阶段 |
| 项目信息甄别 | `projectDiscrimination` | 标题、正文 | 无 | 标讯、拟在建、非项目信息或异常信息判断 |
| 公告结构化抽取 | `ztbAiStructureInfo` | 标题、正文 | 结构化规则 | 项目名称、金额、联系人、资质、评分、时间节点 |

## 默认参数规则

- 未指定地区：默认全国。
- 未指定时间：搜索和商机类默认近 30 天；趋势、企业画像、合同分析可扩展到近 90 天、12 个月或 24 个月，并在回答中说明。
- 未指定公告阶段：默认覆盖采购意向、招标公告、中标/成交结果、合同公告，拟在建问题单独使用拟在建接口。
- 结果过少：扩展同义词、放宽地区、放宽时间、增加公告阶段。
- 结果过杂：增加必含词，并加入招聘、考试、培训、会议、新闻、人员公示等排除词。

## 错误处理

| 场景 | 处理方式 |
|---|---|
| 缺少 API Key | 停止调用，提示访问 [世舶科技 API Key 获取页](https://apiyx.gov-bid.com/?share=eyJjaGFubmVsIjoiemhhbmd5aW5nIn0) 获取并配置 `BBIAO_API_KEY` |
| 鉴权失败 | 检查 Key 是否正确、过期、具备接口权限 |
| 额度不足 | 联系世舶科技商务人员充值或扩容 |
| 请求超时 | 缩小时间、地区、关键词范围后重试 |
| 参数错误 | 检查必填参数、日期格式、分页、金额和公告类型 |
| 无结果 | 展示已用条件，并按扩展策略放宽 |
