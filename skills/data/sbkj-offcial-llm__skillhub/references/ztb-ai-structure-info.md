## POST 【AI模型训练定制化】LLM招中标项目信息结构化

**请求地址：** `https://gate.gov-bid.com/outer-gateway/bid/ztbAiStructureInfo?key=***`

**说明：** 调用大模型接口对招中标项目信息标题和内容进行结构化抽取，座机号码补全区号，金额转化为人民币元，评标专家角色提取为职业、职务、专业方向等。

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| messages | array | 否 | - | 对话消息数组，兼容OpenAI Chat Completions格式，通常包含system结构化规则和user标讯标题及内容 |
| messages[].role | string | 是 | system | 消息角色：system、user、assistant等 |
| messages[].content | string | 是 | 工程 | 消息内容；system中填写结构化规则，user中填写待结构化的标讯标题和正文内容 |
| max_tokens | integer | 否 | 2048 | 模型最大输出token数量 |
| temperature | number | 否 | 0 | 采样温度，0表示稳定输出 |
| top_p | number | 否 | 1 | 核采样参数，1表示不限制累计概率采样范围 |

### 请求示例

```json
{
  "messages": [
    {
      "role": "system",
      "content": "标讯信息数据结构化，座机号码要补全区号，金额要转化为人民币元，评标专家角色为其职业、职务、专业方向等。"
    },
    {
      "role": "user",
      "content": "中标（成交）结果公告 采购项目名称： 新庙镇沙塘学校信息化设备采购项目 采购项目编号： EZYG-ZFCG-2023-017 项目行政主管地区： 鄂州市 采购项目子包编号： 1 中标（成交）供应商名称： 武汉市腾亚科技有限公司 中标（成交）供应商代码： 91420111751839827U 中标（成交）价格： 121.5 价格单位： 万元 价格币种： 人民币 公告名称： 鄂州市临空经济区新庙镇中心学校新庙镇沙塘学校信息化设备采购项目中标（成交）结果公告 首次公告时间： 2023-09-06 15:13:53 创建人： 公告内容： 一、项目编号 EZYG-ZFCG-2023-017 二、采购计划备案号 420706-2023-00292 三、项目名称 新庙镇沙塘学校信息化设备采购项目 四、中标（成交）信息 包1： 供应商名称：武汉市腾亚科技有限公司 供应商地址：武汉东湖新技术开发区东一产业园光谷大道金融后台服务中心基地建设项目二期2.7期B26幢2层1、2号 中标（成交）金额：¥121.5万元 五、主要标的信息 包1： 货物类 名称：详见响应文件 品牌（如有）：详见响应文件 规格型号：详见响应文件 数量：详见响应文件 单价：121.5 万元 六、 评审专家名单 廖良锋(包1采购人代表)、汪学斌(包1组长)、任红军(包1) 七、评审信息 1. 评审时间：2023-09-05 2. 评审地点：鄂州市文苑壹号34号门面，吴都中学东门对面（阳光造价招标代理部评标室） 八、代理服务收费标准及金额： 1. 代理服务收费标准：参照《招标代理服务收费管理暂行办法》计价格[2002]1980号文规定计取 2. 收费金额（万元）：1.74 九、公告期限 自本公告发布之日起1个工作日。 十、其他补充事宜 根据《鄂州市政府采购合同融资工作实施方案》的要求，有需求的中标的中小微企业可以向意向金融机构提出政府采购合同融资申请。中小微企业凭政府采购中标（成交）通知书、政府采购合同，即可'零担保、零抵押'自主选择金融机构申请融资。合作金融机构承诺为中标供应商提供融资绿色通道，采购人承诺及时做好政府采购合同公开和合同备案。具体融资事宜由中标供应商与合作金融机构进行洽谈、办理。 十一、凡对本次公告内容提出询问，请按以下方式联系 1、采购人信息 名 称：鄂州市临空经济区新庙镇中心学校 地 址：新庙镇文塘村 联系方式：13986403924 2、采购代理机构信息 名 称：鄂州阳光建设工程造价咨询有限责任公司 地 址：湖北省-鄂州市-市辖区 文苑1号9号楼1层34号门面及2层4-9号门面 联系方式：13554455605 3、项目联系方式： 项目联系人： 向哲文 电 话： 13554455605 鄂州阳光建设工程造价咨询有限责任公司 2023-09-06"
    }
  ],
  "temperature": 0,
  "top_p": 1
}
```

### 响应参数

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 本次对话补全请求ID |
| object | string | 响应对象类型，通常为chat.completion |
| created | integer | 响应创建时间戳 |
| model | string | 实际调用的模型名称 |
| choices | array | 模型生成结果列表 |
| choices[].index | integer | 候选结果序号 |
| choices[].message | object | 模型返回的消息对象 |
| choices[].message.role | string | 模型消息角色，通常为assistant |
| choices[].message.content | string | 标讯信息结构化结果文本，通常为JSON字符串或结构化文本 |
| choices[].finish_reason | string | 模型停止原因，例如stop、length等 |
| usage | object | token用量统计对象 |
| usage.prompt_tokens | integer | 输入提示词token数量 |
| usage.completion_tokens | integer | 输出内容token数量 |
| usage.total_tokens | integer | 总token数量 |

### 响应示例

```json
{
  "id": "chatcmpl-d25b458a28244220b8d200442032927e",
  "object": "chat.completion",
  "created": 1780388222,
  "model": "/home/ubuntu/ZTB-Structure/model/qwen2.5-1.5b-ztbstructure-ch17400-20251101",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"项目名称\":\"安徽省低空科技建工水利AI飞巡网络区域建设三期人机机场及配套设施采购\",\"项目编号\":[\"ACEG-202604233001001\"],\"甲方信息\":[{\"甲方名称\":\"安徽省低空科技发展有限公司\",\"甲方联系人姓名\":[\"吴工\"],\"甲方联系电话\":[\"18656351508\"]}],\"报名截止时间\":\"2026-04-09 18:00:00\",\"开标时间\":\"2026-04-13\"}",
        "refusal": null,
        "annotations": null,
        "audio": null,
        "function_call": null,
        "tool_calls": [],
        "reasoning_content": null
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null,
      "token_ids": null
    }
  ],
  "service_tier": null,
  "system_fingerprint": null,
  "usage": {
    "prompt_tokens": 1493,
    "total_tokens": 1617,
    "completion_tokens": 124,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null,
  "prompt_token_ids": null,
  "kv_transfer_params": null
}
```

---
