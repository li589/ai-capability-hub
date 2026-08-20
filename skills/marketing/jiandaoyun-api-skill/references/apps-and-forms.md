# 应用、表单和字段

## 操作

- `jdy_list_apps`：列出API Key授权范围内的应用。
- `jdy_list_forms`：列出指定应用下的表单。
- `jdy_get_form_widgets`：读取业务字段、子表字段和系统字段。

## 路由顺序

始终按应用 → 表单 → 字段顺序解析目标。名称匹配不唯一时停止并要求用户选择，不要猜测写入目标。

字段定义中的 `name` 是API提交键，`label`用于向用户解释，`widgetName`是稳定控件标识。构造读取或写入请求前重新获取字段结构。

## 示例输入

```json
{"app_id":"APP_ID","entry_id":"ENTRY_ID"}
```

完整参数运行 `python3 scripts/jdy tool-help jdy_get_form_widgets`。
