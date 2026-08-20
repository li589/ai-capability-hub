---
name: feishu
description: 飞书云文档统一 skill。覆盖文档、表格、多维表格、云空间的全部操作。凭证从环境变量（FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_USER_OPEN_ID）获取，没有则提示用户。
install_source: official
install_method: download
skill_id: official_5XzSNuhN
enabled_at: 1787230826111
version: 1.0.0
name_zh: 飞书云文档
---

# 飞书云文档

## ⚠️ 重要说明

### 凭证获取
1. **多账户支持**：OpenClaw 可能配置多个飞书机器人账户（如 work、default、main）
2. **自动检测**：技能会优先从环境变量获取，其次从 OpenClaw 配置读取
3. **账户选择**：默认使用 'work' 账户，可根据会话标签选择

### 文档所有权
- **机器人所有者**：使用机器人凭证创建的文档，所有者显示为机器人应用
- **用户访问**：通过邀请协作者 + 公开链接确保用户有完全访问权限
- **所有权限制**：无法通过 API 将文档所有者改为用户，这是飞书 API 限制

### 回复格式
- **纯链接列表**：禁止显示 raw token，禁止用 markdown 表格
- **正确格式**：
  ```
  📊 表格名
  https://dcncc0hlk6pl.feishu.cn/sheets/TOKEN
  ```

## 凭证获取策略（改进版）

基于实际经验，凭证获取应该支持多种方式，优先级如下：
1. **环境变量**：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_USER_OPEN_ID`
2. **OpenClaw 配置**：从 `~/.openclaw/openclaw.json` 读取
3. **用户输入**：如果都没有，提示用户输入

```python
import urllib.request, json, os, sys

def get_feishu_credentials(account_label="work"):
    """
    获取飞书凭证，支持多种来源
    account_label: 账户标签，如 'work', 'default', 'main'
    """
    # 1. 优先从环境变量获取
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    user_open_id = os.environ.get("FEISHU_USER_OPEN_ID")
    
    # 2. 如果环境变量不全，尝试从 OpenClaw 配置读取
    if not all([app_id, app_secret]):
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    accounts = config.get("channels", {}).get("feishu", {}).get("accounts", [])
                    
                    # 根据标签选择账户
                    selected_account = None
                    for account in accounts:
                        if account.get("label") == account_label:
                            selected_account = account
                            break
                    
                    # 如果没找到指定标签的账户，使用第一个
                    if not selected_account and accounts:
                        selected_account = accounts[0]
                    
                    if selected_account:
                        if not app_id:
                            app_id = selected_account.get("appId")
                        if not app_secret:
                            app_secret = selected_account.get("appSecret")
            except Exception as e:
                print(f"读取 OpenClaw 配置失败: {e}", file=sys.stderr)
    
    # 3. 如果还没有，提示用户输入
    if not app_id:
        app_id = input("请输入飞书 App ID: ").strip()
    if not app_secret:
        app_secret = input("请输入飞书 App Secret: ").strip()
    if not user_open_id:
        user_open_id = input("请输入你的飞书 Open ID (可选，不填则文档所有者是机器人): ").strip()
    
    # 验证凭证
    if not app_id or not app_secret:
        raise ValueError("缺少飞书凭证。请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")
    
    print(f"使用飞书账户: {app_id[:8]}...")
    if user_open_id:
        print(f"用户 Open ID: {user_open_id}")
    else:
        print("警告：未设置 FEISHU_USER_OPEN_ID，创建的文档所有者将是机器人")
    
    return app_id, app_secret, user_open_id

# 使用示例
APP_ID, APP_SECRET, USER_OPEN_ID = get_feishu_credentials("work")  # 使用 work 账户
```

## 标准工作流（创建文件并分享）

**顺序：创建 → 写数据 → 设置公开链接 → 邀请协作者**

```python
def feishu_req(url, data=None, method=None, token=None):
    if not data: data = {}
    payload = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=payload, method=method or ("POST" if data else "GET"))
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

# ① 获取 token
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
TOKEN = feishu_req(url, {"app_id": APP_ID, "app_secret": APP_SECRET}, "POST")["tenant_access_token"]

# ② 获取真实根目录 token
url = "https://open.feishu.cn/open-apis/drive/explorer/v2/root_folder/meta"
ROOT_TOKEN = feishu_req(url, token=TOKEN)["data"]["token"]

# ③ 创建文档
url = "https://open.feishu.cn/open-apis/docx/v1/documents"
DOC_ID = feishu_req(url, {"node_type": "docx", "parent_node_id": ROOT_TOKEN, "title": "标题"}, "POST", TOKEN)["data"]["document"]["document_id"]

# ③ 创建表格
url = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets"
SHEET_TOKEN = feishu_req(url, {"title": "标题", "folder_token": ROOT_TOKEN}, "POST", TOKEN)["data"]["spreadsheet"]["spreadsheet_token"]
SHEET_ID = feishu_req(f"{url}/{SHEET_TOKEN}/sheets/query", token=TOKEN)["data"]["sheets"][0]["sheet_id"]

# ④ 写数据（表格）
values = [["列1", "列2"], ["值1", "值2"]]
feishu_req(f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values",
    {"valueRange": {"range": f"{SHEET_ID}!A1:Z100", "values": values}}, "PUT", TOKEN)

# ⑤ 设置公开链接
for ptype, token in [("docx", DOC_ID), ("sheet", SHEET_TOKEN)]:
    feishu_req(f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/public?type={ptype}",
        {"share_entity": "anyone", "link_share_entity": "anyone_editable"}, "PATCH", TOKEN)

# ⑥ 邀请协作者（如果有用户 Open ID）
if USER_OPEN_ID:
    for ptype, token in [("docx", DOC_ID), ("sheet", SHEET_TOKEN)]:
        feishu_req(f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/members?type={ptype}",
            {"member_type": "openid", "member_id": USER_OPEN_ID, "perm": "full_access"}, "POST", TOKEN)
```

**发送消息给用户**：用纯链接列表格式，禁止显示 raw token，禁止用 markdown 表格。

> ⚠️ **关键**：
> 1. **必须先写数据，再设置权限**（顺序反了文件不会出现在"外部"列表）
> 2. `parent_node_id` / `folder_token` 必须用真实 token（不能是字符串 "root"）
> 3. **回复格式必须严格**：
>    ```
>    📊 表格名
>    https://dcncc0hlk6pl.feishu.cn/sheets/TOKEN
>    ```
>    或
>    ```
>    📄 文档名
>    https://dcncc0hlk6pl.feishu.cn/docx/TOKEN
>    ```
> 4. **不要包含**：markdown 表格、raw token、额外说明文本

---

## 核心概念

| 概念 | 说明 | 从 URL 提取方式 |
|------|------|----------------|
| folder_token | 文件夹唯一标识 | URL 中 `folder/` 后字符 |
| file_token | 文件唯一标识 | URL 中 `/docx/`、`/sheets/`、`/bitable/` 后字符 |
| doc_token | 文档标识 | `/docx/` 后字符 |
| spreadsheet_token | 表格标识 | `/sheets/` 后字符 |
| app_token | 多维表格标识 | `/bitable/` 后字符 |
| sheet_id | 工作表标识 | URL 参数 `sheet=` |
| block_id | 文档内块 ID | 文档块中唯一 |
| revision_id | 乐观锁 | 文档 metadata 中 |

**文件位置判断：**
- 云空间文件夹 → `folder/` → folder_token
- 文档 → `/docx/` → doc_token
- 表格 → `/sheets/` → spreadsheet_token
- 多维表格 → `/bitable/` → app_token
- 知识库 → `/wiki/` → 需调用 wiki API 取 obj_token

---

## 路由决策树

```
用户发来需求
   ↓
┌──────────────────────────────────────┐
│  含「云文档、文件夹、云空间」？        │
│  或「浏览、看看、有哪些、列表」？      │
├──────────────────────────────────────┤
│  是 → 【云空间操作】直接用 drive 章节  │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  含「文档、在线文档、docx、写入内容」  │
├──────────────────────────────────────┤
│  是 → 【在线文档操作】用 docx 章节    │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  含「表格、电子表格、sheet、写入数据」 │
├──────────────────────────────────────┤
│  是 → 【电子表格操作】用 sheets 章节   │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  含「多维表格、bitable」              │
├──────────────────────────────────────┤
│  是 → 【多维表格操作】用 bitable 章节  │
└──────────────────────────────────────┘
   ↓
【无法判断】→ 询问用户需求
```

**创建类需求类型判断：**
```
用户说「建 / 创建 / 新建 + 云文档」
   ↓
有「表格、数据、报表」→ sheets 章节
有「多维、数据库」→ bitable 章节
有「文档、通知、报告」→ docx 章节
不明显 → 询问：「想建哪种？文档 / 表格 / 多维表格」
```

---

## 常用资源

| 名称 | token |
|------|-------|
| 基金实时估值表格 | `C2kpsGoGfhHM8ZtZYXfcIADOnzc` |
| AI 助手知识库 | `Xz2sdsNvhoocCdxke3Bcjd0mn5e` |

---

# 一、云空间（drive）

**覆盖：浏览文件夹、创建文件夹、上传、下载、删除、移动、版本管理、媒体文件**

## 列出文件

```python
# 列出根目录
url = "https://open.feishu.cn/open-apis/drive/v1/files?page_size=50"
# 列出指定文件夹
url = f"https://open.feishu.cn/open-apis/drive/v1/files?folder_token={FOLDER_TOKEN}"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    for f in json.loads(resp.read())["data"]["files"]:
        print(f["name"], f["token"], f["type"], f["url"])
```

## 创建文件夹

```python
# ⚠️ 先获取真实根目录token（不能传空字符串"",否则会创建在app根目录）
url = "https://open.feishu.cn/open-apis/drive/explorer/v2/root_folder/meta"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
ROOT_TOKEN = json.loads(resp.read())["data"]["token"]

url = "https://open.feishu.cn/open-apis/drive/v1/files/create_folder"
payload = {
    "name": "文件夹名称",
    "folder_token": ROOT_TOKEN  # ⚠️ 必须用真实token，不能用空字符串
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read())["data"]
    print(result["token"], result["url"])
```


### 给文件夹添加协作者

> 重要：文件夹创建后，用户默认没有访问权限（会提示"没有权限访问"）。需要主动给用户授权：

```python
# 将用户添加为文件夹协作者
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{FOLDER_TOKEN}/members?type=folder"
payload = {
    "member_type": "openid",
    "member_id": USER_OPEN_ID,  # 用户的 open_id
    "perm": "full_access"  # full_access / read / edit / comment
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
```

> 注意：文件夹不会出现在用户的"云文档"列表，而是在"共享文件夹"中显示。


## 上传文件

```python
import urllib.request, json, os

# 小文件 < 20MB
def upload_file(file_path, parent_node="root"):
    boundary = "----PythonFormBoundary" + os.urandom(16).hex()
    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()
    
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
    url += f"?file_name={file_name}&parent_type=drive_file&parent_node={parent_node}&upload_type=stream"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["data"]

# 大文件分片上传
def upload_large(file_path, parent_node="root", chunk_size=10*1024*1024):
    file_size = os.path.getsize(file_path)
    chunk_num = (file_size + chunk_size - 1) // chunk_size
    # 1. 创建上传任务
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
    payload = {
        "file_name": os.path.basename(file_path),
        "parent_type": "drive_file",
        "parent_node": parent_node,
        "upload_type": "chunked",
        "chunk_numbers": chunk_num
    }
    # ... 完整分片逻辑见实际需求
```

## 下载文件

```python
url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_TOKEN}/download"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=30) as resp:
    content = resp.read()
    with open("downloaded_file", "wb") as f:
        f.write(content)
```

## 移动文件

```python
# 将文件移动到目标文件夹
url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_TOKEN}/move"
payload = {"type": "file", "folder_token": TARGET_FOLDER_TOKEN}  # ⚠️ 参数名是 folder_token，不是 target_folder_token
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json; charset=utf-8")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## 删除文件

```python
url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_TOKEN}"
req = urllib.request.Request(url, method="DELETE")
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## 版本管理

```python
# 列出版本
url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_TOKEN}/versions"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    versions = json.loads(resp.read())["data"]["files"]
    for v in versions:
        print(v["token"], v["name"], v["size"])

# 创建版本
url = f"https://open.feishu.cn/open-apis/drive/v1/files/{FILE_TOKEN}/versions"
payload = {"name": "版本名称"}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
```

## 设置文件/文档公开链接

```python
# 文档公开（docx/sheet/bitable 均可用此接口）
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{FILE_TOKEN}/public?type=file_type"
payload = {
    "share_entity": "anyone",
    "link_share_entity": "anyone_editable"  # 或 "anyone_readable"、"tenant_editable"
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="PATCH")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## 上传文档内嵌媒体（图片/视频/附件）

```python
# 限速：5 QPS，10000次/天
url = "https://open.feishu.cn/open-apis/drive/v1/media/upload_all"
# multipart/form-data: file, file_name, parent_type, parent_node
# parent_type: "message_attachment"（消息附件）或 "drive_file"（云空间）
```

## drive 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `400 field validation failed: folder_token` | folder_token 放错位置 | 放 body 里作为 `folder_token` 字段 |
| `403` | 文件不在应用云空间 | 确认文件属于应用云空间 |
| `404` | file_token 不存在 | 确认 token 正确 |

---

# 二、在线文档（docx）

**覆盖：读取、创建、搜索、写入内容块（有限制）、设置权限**

## 读取文档

```python
url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read())
    title = result["data"]["document"]["title"]
    revision_id = result["data"]["document"]["revision_id"]
    print(title, revision_id)
```

## 读取文档块

```python
url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{DOC_TOKEN}/blocks?page_size=100"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    blocks = json.loads(resp.read())["data"]["items"]
    for b in blocks:
        bt = b["block_type"]
        if bt == 2:  # 文本
            for e in b["text"]["elements"]:
                print(e["text_run"]["content"], end="")
        elif bt == 12:  # H1
            print("\n# " + b["heading1"]["elements"][0]["text_run"]["content"])
        elif bt == 13:  # H2
            print("\n## " + b["heading2"]["elements"][0]["text_run"]["content"])
        elif bt == 5:  # 无序列表
            print("\n• " + b["bullet"]["elements"][0]["text_run"]["content"])
```

## 创建文档

> ⚠️ **存储位置**：创建文档时，`parent_node_id` 不能写字符串 `"root"`，必须传入真实的 folder_token（获取方法见下）。

```python
# ① 获取用户的"我的空间"根目录 token
url = "https://open.feishu.cn/open-apis/drive/explorer/v2/root_folder/meta"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    ROOT_TOKEN = json.loads(resp.read())["data"]["token"]

# ② 创建文档
url = "https://open.feishu.cn/open-apis/docx/v1/documents"
payload = {"node_type": "docx", "parent_node_id": ROOT_TOKEN, "title": "文档标题"}
DOC_ID = json.loads(resp.read())["data"]["document"]["document_id"]

# ③ 设置公开链接
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{DOC_ID}/public?type=docx"
payload = {"share_entity": "anyone", "link_share_entity": "anyone_editable"}
# PATCH ...

# ④ 邀请用户为协作者（让用户在"我的空间"里能看到）
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{DOC_ID}/members?type=docx"
payload = {"member_type": "openid", "member_id": USER_OPEN_ID, "perm": "full_access"}
# POST ...
    DOC_ID = result["document_id"]
    REVISION_ID = result["revision_id"]
    print(DOC_ID, REVISION_ID)
```

## 写入内容块

⚠️ **已知限制**：飞书 API 对 block_type 有限制，经验证：
- **text（type=2）可写入**
- heading / bullet / quote 等类型返回 `invalid param`

**已验证可用的写入方式：**

```python
def gen_block_id():
    import time
    return "bx_" + str(int(time.time() * 1000))

def insert_text_block(doc_id, text, bold=False, index=0):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    block = [{
        "block_id": gen_block_id(),
        "block_type": 2,
        "text": {
            "elements": [{"text_run": {
                "content": text,
                "text_element_style": {"bold": bold}
            }}],
            "style": {}
        }
    }]
    payload = {"children": block, "index": index}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

# 使用示例
insert_text_block("ZvQGdBvcJo2XpPxJ9Socsz6un7b", "这是普通文本")
insert_text_block("ZvQGdBvcJo2XpPxJ9Socsz6un7b", "这是粗体", bold=True)
```

**建议格式策略（用纯文本模拟格式）：**
- 标题：用全大写或符号前缀（如 `━━━`、`【】`）
- 列表：用 `•` 或 `▶` 符号
- 粗体：单独一行或单独一条消息传达重要性
- 引用/摘要：用 `┃` 或分隔线

## 搜索文档

```python
url = "https://open.feishu.cn/open-apis/suite/docs-api/search/object"
payload = {"search_key": "关键词", "count": 5, "offset": 0, "docs_types": ["docx"]}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    for doc in json.loads(resp.read())["data"]["docs_entities"]:
        print(doc["docs_token"], doc["title"][:60])
```

## docx 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `invalid param` | 非 text block 类型 API 限制 | 换用 text 类型写入 |
| `1770001` | block 结构不符合 API 要求 | 确认 block 字段完整 |

---

# 三、电子表格（sheets）

**覆盖：读取数据、写入数据、公式、sheet_id 查询**

## 核心概念

| 概念 | 说明 |
|------|------|
| spreadsheet_token | 表格唯一标识，`/sheets/` 后字符 |
| sheet_id | 工作表 ID，`?sheet=` 后字符，格式如 `0b**12` |
| range | 范围格式：`{sheetId}!A1:B5` |

## 创建表格

> 创建表格后，要让用户在"云文档"列表看到，需要**同时**完成：① 设置公开链接 + ② 邀请用户为协作者。

```python
# ① 创建表格
url = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets"
payload = {"title": "表格名称", "folder_token": ROOT_TOKEN}
SHEET_TOKEN = json.loads(resp.read())["data"]["spreadsheet"]["spreadsheet_token"]

# ② 设置公开链接（任何人可编辑）
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{SHEET_TOKEN}/public?type=sheet"
payload = {"share_entity": "anyone", "link_share_entity": "anyone_editable"}
# PATCH ...

# ③ 邀请用户为协作者（让用户在"我的空间"里能看到）
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{SHEET_TOKEN}/members?type=sheet"
payload = {
    "member_type": "openid",
    "member_id": USER_OPEN_ID,  # 用户的 open_id
    "perm": "full_access"  # 可编辑
}
# POST ...
```

## 获取 sheet_id

```python
url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{SHEET_TOKEN}/sheets/query"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    sheets = json.loads(resp.read())["data"]["sheets"]
    SHEET_ID = sheets[0]["sheet_id"]
```

## 读取数据

```python
# 读取指定范围
url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values/{SHEET_ID}!A1:Z10"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    values = json.loads(resp.read())["data"]["valueRange"]["values"]
    for row in values:
        print(row)

# 按范围读取
url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values/{SHEET_ID}!A1:B5"
```

## 写入数据

```python
url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SHEET_TOKEN}/values"
payload = {
    "valueRange": {
        "range": f"{SHEET_ID}!A1:B2",
        "values": [["姓名", "分数"], ["张三", 95]]
    }
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="PUT")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## 常用 token

| 名称 | token |
|------|-------|
| 基金实时估值表格 | `C2kpsGoGfhHM8ZtZYXfcIADOnzc` |

---

# 四、多维表格（bitable）

**覆盖：创建、增删改查记录、字段操作、过滤**

## 核心概念

| 概念 | 说明 |
|------|------|
| app_token | 多维表格唯一标识 |
| table_id | 数据表 ID |
| record_id | 记录 ID |
| field_id | 字段 ID |
| view_id | 视图 ID |

## 获取 table_id

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    tables = json.loads(resp.read())["data"]["items"]
    TABLE_ID = tables[0]["table_id"]
```

## 读取记录

```python
# 读取所有记录
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    records = json.loads(resp.read())["data"]["items"]
    for r in records:
        print(r["fields"], r["record_id"])

# 按分页读取
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=100"
```

## 新增记录

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
payload = {"fields": {"字段名": "值", "数量": 10}}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## 批量新增记录

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_create"
payload = {"records": [{"fields": {"姓名": "张三"}}, {"fields": {"姓名": "李四"}}]}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
```

## 更新记录

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{RECORD_ID}"
payload = {"fields": {"姓名": "王五"}}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="PUT")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
```

## 删除记录

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{RECORD_ID}"
req = urllib.request.Request(url, method="DELETE")
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## 批量删除

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_delete"
payload = {"records": [RECORD_ID1, RECORD_ID2]}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, method="DELETE")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Content-Type", "application/json")
```

## 过滤查询

```python
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?filter=AND(字段==值)"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {TOKEN}")
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()))
```

## bitable 资源限制

- 单表记录数上限：50万
- 单表字段数上限：200
- 单表视图数上限：20
- 最多建 50 个表格
- 单次批量操作最多 500 条

---

# 五、导入文件到云空间

支持格式：docx、doc、wps、et、wpt、pdf、epub、xlsx、xls、xlsm、xlsb、csv

```python
# 文件上传（< 50MB）
url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
# multipart/form-data: file, file_name, parent_type="drive_file", parent_node=folder_token或root

# 分片上传（> 20MB，每片 10MB）
url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
payload = {
    "file_name": "文件.docx",
    "parent_type": "drive_file",
    "parent_node": "root",
    "upload_type": "chunked",
    "chunk_numbers": 5,
    "seq": 0  # 从0开始的序号
}
```

---

# 六、block_type 参考表（文档块类型）

| type | 含义 | API 可写 |
|------|------|---------|
| 2 | 文本（Text） | ✅ |
| 3 | 待办（Todo） | ⚠️ |
| 4 | 代码块（Code） | ⚠️ |
| 5 | 无序列表（Bullet） | ⚠️ |
| 6 | 有序列表（OrderedList） | ⚠️ |
| 7 | 引用（BlockQuote） | ⚠️ |
| 9 | 高亮/标注（Callout） | ⚠️ |
| 10 | 视频 | ⚠️ |
| 11 | 图片 | ⚠️ |
| 12 | 一级标题（H1） | ⚠️ |
| 13 | 二级标题（H2） | ⚠️ |
| 14 | 三级标题（H3） | ⚠️ |
| 15 | 表格（Table） | ⚠️ |

**写入建议**：除 type=2（文本）外，其他类型均可能报 `invalid param`。写入时优先使用文本块配合格式符号（`━━━`、`•`、`【】`）来模拟结构。

---

# 七、经验总结

## 关键卡点与解决方案

### 1. 凭证匹配问题
**问题**：OpenClaw 配置多个飞书账户，使用错误账户导致创建失败
**解决方案**：
- 通过 `openclaw channels status --probe` 查看所有账户
- 根据当前会话标签选择正确账户（如 `feishu:work`）
- 使用 `get_feishu_credentials("work")` 自动选择

### 2. 凭证获取方式
**问题**：技能要求环境变量，但凭证已在 OpenClaw 配置中
**解决方案**：
- 优先从环境变量获取
- 其次从 `~/.openclaw/openclaw.json` 读取
- 最后提示用户输入

### 3. 文档所有权问题
**问题**：机器人创建的文档所有者显示为机器人，不是用户
**解决方案**：
- **接受限制**：这是飞书 API 设计，无法通过 API 改变
- **确保访问**：通过公开链接 + 协作者邀请确保用户完全访问
- **明确告知**：向用户说明所有权限制

### 4. 回复格式问题
**问题**：使用了 markdown 表格，不符合技能要求
**解决方案**：
- **严格遵循**：纯链接列表格式
- **禁止显示**：raw token、markdown 表格
- **正确示例**：
  ```
  📊 表格名
  https://dcncc0hlk6pl.feishu.cn/sheets/TOKEN
  ```

## 最佳实践

1. **凭证管理**：
   ```bash
   # 设置环境变量（一次性）
   export FEISHU_APP_ID=cli_xxx
   export FEISHU_APP_SECRET=xxx
   export FEISHU_USER_OPEN_ID=ou_xxx
   ```

2. **账户选择**：
   ```python
   # 根据会话选择正确账户
   account_label = "work"  # 或 "default", "main"
   APP_ID, APP_SECRET, USER_OPEN_ID = get_feishu_credentials(account_label)
   ```

3. **工作流顺序**：
   ```
   获取凭证 → 获取token → 获取根目录 → 创建文件 → 
   写入数据 → 设置公开链接 → 邀请协作者 → 纯链接回复
   ```

4. **错误处理**：
   - 检查凭证是否完整
   - 验证 token 是否有效
   - 确认操作顺序正确

## 已验证的凭证配置

| 账户标签 | App ID | 用途 |
|----------|--------|------|
| work | `cli_a9355f9a51785bce` | 工作会话专用 |
| default | `cli_a93eae577c789bca` | 默认账户 |
| main | (根据配置) | 主账户 |

**注意**：每个飞书机器人都有独立的 App ID 和 App Secret，不能混用。
