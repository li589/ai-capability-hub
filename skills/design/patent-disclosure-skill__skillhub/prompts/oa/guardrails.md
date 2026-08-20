# 模式 D · 审查答复辅助 · 总则

## 定位

可选、默认关闭。显式触发后进入：

1. **案例脱敏入库**（历史通知书/答复 → Obs 笔记；向量可选）  
2. **审查文档自动答复草稿**（先标签/字段过滤，向量可用时再相似度检索；须人审）

**不**替代专利代理签字与正式递交；产出为草稿。

## 禁止

- 未脱敏入库含客户名、电话、未公开核心参数的原文  
- 无检索命中（或未说明库为空）就长篇「糊弄」意见陈述  
- 修改超原申请记载范围却不标注风险  
- 无人审确认即将草稿当作已递交文件  
- 将 API Key 写入仓库或在回复中回显完整密钥

## 配置（对话交互 · 向量可选）

**必须 `Read`** `prompts/oa/configure_embedding.md`，按问答收集后写文件：

1. `python tools/oa/config.py recommend`  
2. 问用户：跳过 / 推荐智谱 / 其他预设 / 自定义（URL+模型+维度+Key）  
3. 用户提供后：  
   - `config.py skip-vector`，或  
   - `config.py set --preset … --api-key …`（自定义则带 `--base-url --model --dimensions`）  
4. **设置后必须自检**：`set` 默认含 `selftest`；也可 `config.py selftest`  
5. 自检通过且需重建时，人确认后 `rebuild_vectors.py --confirm`  
6. 向量超时/失败：检索回退标签（`tags_fallback`），流程不中断  

配置：`{Documents}/patent-disclosure-skill/oa/embedding.config.yaml`  
密钥：同目录 `embedding.secrets.yaml`（仅本机）

## 人审闸门

```
以下为审查答复【草稿】，须代理人/发明人复核后再递交。
请回复：确认仅作内部草稿 / 需要修改策略 / 暂停
```
