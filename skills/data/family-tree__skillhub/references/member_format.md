# 家庭成员数据格式

## 概览
定义家庭成员信息的标准JSON格式，用于生成家庭结构图。

## 数据结构

### 根对象
```json
{
  "family_members": [/* 成员数组 */]
}
```

### 成员对象
每个成员对象包含以下字段：

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| relation | string | 是 | 家庭关系称谓 | "父亲"、"妻子"、"大儿子" |
| age | string | 是 | 年龄（带"岁"）或描述 | "59岁"、"未提及" |
| gender | string | 是 | 性别 | "男"、"女" |
| job | string | 是 | 职业或状态（"身故"表示已故） | "小企业主"、"身故"、"学生" |
| marital_status | string | 是 | 婚姻状态 | "已婚"、"未婚"、"离婚" |
| parent | string | 否 | 父节点关系（用于孙辈定位） | "大儿子" |

## 完整示例

### 示例1：基础家庭
```json
{
  "family_members": [
    {
      "relation": "自己",
      "age": "37岁",
      "gender": "男",
      "job": "企业高管",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "妻子",
      "age": "34岁",
      "gender": "女",
      "job": "企业白领",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "父亲",
      "age": "59岁",
      "gender": "男",
      "job": "小企业主",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "母亲",
      "age": "57岁",
      "gender": "女",
      "job": "家庭主妇",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "女儿",
      "age": "4岁",
      "gender": "女",
      "job": "幼儿园",
      "marital_status": "未婚",
      "parent": ""
    }
  ]
}
```

### 示例2：多代家庭
```json
{
  "family_members": [
    {
      "relation": "自己",
      "age": "40岁",
      "gender": "男",
      "job": "企业高管",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "妻子",
      "age": "38岁",
      "gender": "女",
      "job": "教师",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "父亲",
      "age": "65岁",
      "gender": "男",
      "job": "身故",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "母亲",
      "age": "62岁",
      "gender": "女",
      "job": "退休",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "岳父",
      "age": "68岁",
      "gender": "男",
      "job": "退休",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "岳母",
      "age": "65岁",
      "gender": "女",
      "job": "退休",
      "marital_status": "已婚",
      "parent": ""
    },
    {
      "relation": "大儿子",
      "age": "15岁",
      "gender": "男",
      "job": "学生",
      "marital_status": "未婚",
      "parent": ""
    },
    {
      "relation": "二儿子",
      "age": "10岁",
      "gender": "男",
      "job": "学生",
      "marital_status": "未婚",
      "parent": ""
    },
    {
      "relation": "孙子",
      "age": "2岁",
      "gender": "男",
      "job": "幼儿",
      "marital_status": "未婚",
      "parent": "大儿子"
    }
  ]
}
```

## 验证规则

1. **必填字段检查**：relation、age、gender、job、marital_status 均不能为空
2. **性别一致性**：
   - "父亲"、"岳父"、"公公"、"儿子"、"孙子" → gender 必须为 "男"
   - "母亲"、"岳母"、"婆婆"、"女儿"、"孙女" → gender 必须为 "女"
3. **关系称谓规范**：
   - 支持的称谓：自己、妻子、丈夫、父亲、母亲、岳父、岳母、公公、婆婆、姐姐、哥哥、弟弟、妹妹、大儿子、二儿子、小儿子、大女儿、二女儿、小女儿、孙子、孙女、外孙、外孙女、儿媳、女婿
4. **age 格式**：建议使用 "XX岁" 格式，也可使用 "未提及"
5. **job 字段特殊值**：当 job 为 "身故" 时，成员卡片会显示为灰色样式

## 常见使用场景

### 场景1：单核家庭
- 客户自己 + 配偶 + 子女
- 无需补充信息

### 场景2：三代同堂
- 客户自己 + 配偶 + 子女 + 父母
- 自动补充配偶父母（如果有子女）

### 场景3：复杂家庭
- 包含兄弟姐妹、子女配偶、孙辈
- parent 字段用于定位孙辈到对应子女

## 注意事项
- relation 字段中 "自己" 会在处理时自动转换为 "客户自己"
- 当缺少必要成员时，脚本会自动补充（如自己父母、配偶父母）
- parent 字段仅对孙辈有效，值应是对应子女的 relation 值
