# Skill: EVM Log 关联模式识别（从已知地址出发）

## 目标

给定一个已知 EVM 地址 A，在日志表（log table）中通过 `topic1` 和 `topic2` 两个 indexed 地址位进行检索，识别与该地址高度相关的 `contract_address + topic0` 组合，并进一步抽取对应交易哈希，分析该地址所处的交易模式，最终输出：

1. 与地址 A 高关联的 `contract_address`
2. 与地址 A 高关联的 `topic0`
3. `topic1=A*` 和 `topic2=A*` 两侧最常见的对手地址（标签化）
4. 候选交易模式及代表性交易哈希
5. 是否存在"明显集中于某类事件/某类合约"的模式判断

---

## 适用范围

适用于 EVM 链日志分析（Polygon / ETH / BSC / TRON 等）。  
前提是目标地址 A 可能出现在 event log 的 `topic1` 或 `topic2` 中。  
典型场景：ERC20 Transfer、Approval、NFT Transfer、DeFi 自定义事件、跨链桥事件。

---

## 输入参数

### 必需

| 参数 | 说明 | 示例 |
|------|------|------|
| `address` | 目标地址 A（20 字节 hex） | `0xabc...` |
| `logs_table` | Dune 日志表名 | `polygon.logs` |
| `chain` | 链名标识 | `polygon` |

### 可选

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `block_time_start` | `'2024-01-01'` | 时间过滤起点 |
| `top_n_initial` | `10` | 初始统计前 N 名 |
| `top_n_expand` | `50` | 扩展统计前 N 名 |
| `dominance_threshold` | `0.40` | 第一名对手地址占比阈值 |
| `gap_threshold` | `0.15` | 第1名与第2名频率差阈值 |
| `min_sample_size` | `20` | 最小样本量 |
| `max_hash_examples` | `20` | 每模式抽取代表哈希数量 |
| `known_labels` | `{}` | 已知地址标签字典 `{addr: label}` |

---

## Step 0：地址标准化（Padding）

将 20 字节地址 A 转换为 topic 匹配用的 32 字节形式 A*：

```
去除前缀 0x
保留 40 位 hex
左补 24 个 0（共 64 位）
加回 0x 前缀
```

示例：
- 输入：`0x1111222233334444555566667777888899990000`
- 输出：`0x0000000000000000000000001111222233334444555566667777888899990000`

---

## Step 1：双向 Log 检索（Dune API 调用）

分别在 `topic1=A*` 和 `topic2=A*` 两个方向执行查询。

### SQL 模板

**方向一：A 作为 topic1**

```sql
SELECT
  contract_address,
  topic0,
  topic1,
  topic2,
  COUNT(*) AS hit_count,
  MIN(tx_hash) AS sample_tx
FROM {logs_table}
WHERE block_time > TIMESTAMP '{block_time_start}'
  AND topic1 = '{A_padded}'
GROUP BY contract_address, topic0, topic1, topic2
ORDER BY hit_count DESC
LIMIT {top_n_expand}
```

**方向二：A 作为 topic2**

```sql
SELECT
  contract_address,
  topic0,
  topic1,
  topic2,
  COUNT(*) AS hit_count,
  MIN(tx_hash) AS sample_tx
FROM {logs_table}
WHERE block_time > TIMESTAMP '{block_time_start}'
  AND topic2 = '{A_padded}'
GROUP BY contract_address, topic0, topic1, topic2
ORDER BY hit_count DESC
LIMIT {top_n_expand}
```

### Dune API 调用实现

```python
import requests
import time
import json

DUNE_API_KEY = "YOUR_DUNE_API_KEY"
HEADERS = {
    "X-Dune-API-Key": DUNE_API_KEY,
    "Content-Type": "application/json"
}

def pad_address(addr: str) -> str:
    """将 20 字节地址转为 32 字节 topic 匹配格式"""
    clean = addr.lower().replace("0x", "")
    return "0x" + clean.zfill(64)

def run_dune_query(name: str, sql: str) -> list[dict]:
    """提交 Dune SQL 查询并轮询结果"""
    # 创建查询
    r = requests.post(
        "https://api.dune.com/api/v1/query",
        headers=HEADERS,
        json={"name": name, "query_sql": sql, "is_private": True}
    )
    r.raise_for_status()
    query_id = r.json()["query_id"]

    # 执行查询
    r = requests.post(
        f"https://api.dune.com/api/v1/query/{query_id}/execute",
        headers=HEADERS,
        json={"performance": "medium"}
    )
    r.raise_for_status()
    execution_id = r.json()["execution_id"]

    # 轮询结果
    while True:
        r = requests.get(
            f"https://api.dune.com/api/v1/execution/{execution_id}/results",
            headers=HEADERS
        )
        data = r.json()
        state = data.get("state", "")
        if state == "QUERY_STATE_COMPLETED":
            return data["result"]["rows"]
        elif state in ["QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"]:
            raise RuntimeError(f"查询失败: {data}")
        else:
            time.sleep(3)

def fetch_log_patterns(
    address: str,
    logs_table: str,
    block_time_start: str = "2024-01-01",
    top_n: int = 50
) -> tuple[list, list]:
    """执行双向 log 检索，返回 (rows_as_topic1, rows_as_topic2)"""
    A_padded = pad_address(address)

    sql1 = f"""
    SELECT contract_address, topic0, topic1, topic2,
           COUNT(*) AS hit_count, MIN(tx_hash) AS sample_tx
    FROM {logs_table}
    WHERE block_time > TIMESTAMP '{block_time_start}'
      AND topic1 = '{A_padded}'
    GROUP BY contract_address, topic0, topic1, topic2
    ORDER BY hit_count DESC
    LIMIT {top_n}
    """

    sql2 = f"""
    SELECT contract_address, topic0, topic1, topic2,
           COUNT(*) AS hit_count, MIN(tx_hash) AS sample_tx
    FROM {logs_table}
    WHERE block_time > TIMESTAMP '{block_time_start}'
      AND topic2 = '{A_padded}'
    GROUP BY contract_address, topic0, topic1, topic2
    ORDER BY hit_count DESC
    LIMIT {top_n}
    """

    print(f"[Step 1] 检索 topic1={A_padded[:20]}... 方向")
    rows1 = run_dune_query(f"log_topic1_{address[:8]}", sql1)

    print(f"[Step 1] 检索 topic2={A_padded[:20]}... 方向")
    rows2 = run_dune_query(f"log_topic2_{address[:8]}", sql2)

    return rows1, rows2
```

---

## Step 2：频次统计与聚合

将两侧结果聚合到 `(contract_address, topic0)` 级别，统计对手地址分布。

```python
from collections import defaultdict

def aggregate_patterns(rows: list[dict], side: str) -> dict:
    """
    side: 'topic1' 表示 A 在 topic1（对手在 topic2），反之亦然
    返回: {(contract, topic0): {"total": int, "counterparts": {addr: count}}}
    """
    patterns = defaultdict(lambda: {"total": 0, "counterparts": defaultdict(int), "samples": []})
    
    counterpart_field = "topic2" if side == "topic1" else "topic1"
    
    for row in rows:
        key = (row["contract_address"], row["topic0"])
        count = row["hit_count"]
        counterpart_raw = row.get(counterpart_field, "")
        
        patterns[key]["total"] += count
        
        # 提取对手地址（32字节 → 20字节）
        if counterpart_raw and len(counterpart_raw) == 66:
            counterpart_addr = "0x" + counterpart_raw[-40:].lower()
            patterns[key]["counterparts"][counterpart_addr] += count
        
        if row.get("sample_tx"):
            patterns[key]["samples"].append(row["sample_tx"])
    
    return dict(patterns)

def merge_patterns(pat1: dict, pat2: dict) -> dict:
    """合并两侧模式统计"""
    merged = defaultdict(lambda: {
        "total": 0,
        "counterparts": defaultdict(int),
        "samples": [],
        "sides": []
    })
    
    for key, data in pat1.items():
        merged[key]["total"] += data["total"]
        for addr, cnt in data["counterparts"].items():
            merged[key]["counterparts"][addr] += cnt
        merged[key]["samples"].extend(data["samples"])
        merged[key]["sides"].append("topic1")
    
    for key, data in pat2.items():
        merged[key]["total"] += data["total"]
        for addr, cnt in data["counterparts"].items():
            merged[key]["counterparts"][addr] += cnt
        merged[key]["samples"].extend(data["samples"])
        if "topic2" not in merged[key]["sides"]:
            merged[key]["sides"].append("topic2")
    
    return dict(merged)
```

---

## Step 3：阈值判断与强/弱模式分类

依据流程图中的判断节点：**"若和第10位该超过 X，数量大于 Y"**

```python
def classify_patterns(
    merged: dict,
    top_n_initial: int = 10,
    dominance_threshold: float = 0.40,
    gap_threshold: float = 0.15,
    min_sample_size: int = 20
) -> tuple[list, list]:
    """
    对每个 (contract, topic0) 模式进行强/弱分类
    返回: (strong_patterns, weak_patterns)
    """
    strong, weak = [], []
    
    # 按总频次排序，取前 top_n_initial
    sorted_patterns = sorted(merged.items(), key=lambda x: -x[1]["total"])
    
    if not sorted_patterns:
        return [], []
    
    # 取第10位（或最后一位）的频次作为基准
    baseline_count = sorted_patterns[min(top_n_initial - 1, len(sorted_patterns) - 1)][1]["total"]
    
    for (contract, topic0), data in sorted_patterns:
        total = data["total"]
        counterparts = data["counterparts"]
        
        if not counterparts or total < min_sample_size:
            weak.append({"contract": contract, "topic0": topic0, **data, "reason": "样本不足"})
            continue
        
        sorted_cp = sorted(counterparts.items(), key=lambda x: -x[1])
        top1_count = sorted_cp[0][1]
        top2_count = sorted_cp[1][1] if len(sorted_cp) > 1 else 0
        
        top1_ratio = top1_count / total
        gap_ratio = (top1_count - top2_count) / total
        
        # 判断是否超过第10位基准（来自流程图的阈值节点）
        exceeds_baseline = total > baseline_count
        
        is_strong = (
            exceeds_baseline and
            top1_ratio >= dominance_threshold and
            gap_ratio >= gap_threshold
        )
        
        entry = {
            "contract": contract,
            "topic0": topic0,
            "total": total,
            "top1_addr": sorted_cp[0][0],
            "top1_ratio": round(top1_ratio, 4),
            "gap_ratio": round(gap_ratio, 4),
            "counterpart_count": len(counterparts),
            "sides": data["sides"],
            "samples": list(set(data["samples"]))[:5],
        }
        
        if is_strong:
            strong.append(entry)
        else:
            weak.append({**entry, "reason": "主导性不足"})
    
    return strong, weak
```

---

## Step 4：扩展遍历（弱模式处理）

对弱模式，将 `top_n` 扩展到 `top_n_expand`（10→50），并引入 `from/to` 字段辅助判断。

```python
def expand_weak_patterns(
    address: str,
    logs_table: str,
    weak_patterns: list,
    block_time_start: str = "2024-01-01",
    top_n_expand: int = 50,
    known_labels: dict = None
) -> list:
    """对弱模式重新扩展查询，加入 from/to 方向分析"""
    if known_labels is None:
        known_labels = {}
    
    A_padded = pad_address(address)
    expanded_results = []
    
    for pat in weak_patterns:
        contract = pat["contract"]
        topic0 = pat["topic0"]
        
        sql = f"""
        SELECT
          l.tx_hash,
          l.block_time,
          l.topic1,
          l.topic2,
          t.from AS tx_from,
          t.to AS tx_to
        FROM {logs_table} l
        LEFT JOIN {logs_table.split('.')[0]}.transactions t
          ON l.tx_hash = t.hash
        WHERE l.block_time > TIMESTAMP '{block_time_start}'
          AND l.contract_address = '{contract}'
          AND l.topic0 = '{topic0}'
          AND (l.topic1 = '{A_padded}' OR l.topic2 = '{A_padded}')
        ORDER BY l.block_time DESC
        LIMIT {top_n_expand}
        """
        
        rows = run_dune_query(f"expand_{contract[:8]}_{topic0[:8]}", sql)
        
        # 统计 from/to 分布
        from_counts = defaultdict(int)
        to_counts = defaultdict(int)
        for row in rows:
            if row.get("tx_from"):
                from_counts[row["tx_from"].lower()] += 1
            if row.get("tx_to"):
                to_counts[row["tx_to"].lower()] += 1
        
        expanded_results.append({
            **pat,
            "expanded_rows": rows,
            "from_distribution": dict(sorted(from_counts.items(), key=lambda x: -x[1])[:10]),
            "to_distribution": dict(sorted(to_counts.items(), key=lambda x: -x[1])[:10]),
        })
    
    return expanded_results
```

---

## Step 5：Hash 回查与交易模式分析

对强模式候选，按 `(contract_address, topic0)` 序列回查代表性哈希，分析交易行为。

```python
def fetch_pattern_hashes(
    address: str,
    logs_table: str,
    strong_patterns: list,
    block_time_start: str = "2024-01-01",
    max_hash_examples: int = 20
) -> list:
    """
    对每个强模式，抽取代表性交易哈希，
    提取 Contract_topic0 序列（同一 tx 内的所有 log 事件顺序）
    """
    A_padded = pad_address(address)
    results = []
    
    for pat in strong_patterns:
        contract = pat["contract"]
        topic0 = pat["topic0"]
        
        # 回查该模式下的代表哈希
        sql_hashes = f"""
        SELECT DISTINCT tx_hash
        FROM {logs_table}
        WHERE block_time > TIMESTAMP '{block_time_start}'
          AND contract_address = '{contract}'
          AND topic0 = '{topic0}'
          AND (topic1 = '{A_padded}' OR topic2 = '{A_padded}')
        LIMIT {max_hash_examples}
        """
        hash_rows = run_dune_query(f"hashes_{contract[:8]}_{topic0[:8]}", sql_hashes)
        tx_hashes = [r["tx_hash"] for r in hash_rows]
        
        if not tx_hashes:
            results.append({**pat, "tx_sequences": []})
            continue
        
        hashes_str = ", ".join(f"'{h}'" for h in tx_hashes)
        
        # 对每个 hash，抽取同一 tx 中的完整 log 序列（contract_address + topic0）
        sql_seq = f"""
        SELECT
          tx_hash,
          block_time,
          contract_address,
          topic0,
          topic1,
          topic2,
          data
        FROM {logs_table}
        WHERE tx_hash IN ({hashes_str})
        ORDER BY tx_hash, index
        """
        seq_rows = run_dune_query(f"seq_{contract[:8]}_{topic0[:8]}", sql_seq)
        
        # 按 tx_hash 分组为事件序列
        from itertools import groupby
        tx_sequences = {}
        for tx_hash, group in groupby(seq_rows, key=lambda x: x["tx_hash"]):
            events = list(group)
            tx_sequences[tx_hash] = [
                f"{e['contract_address']}:{e['topic0'][:10]}"
                for e in events
            ]
        
        results.append({
            **pat,
            "tx_hashes": tx_hashes,
            "tx_sequences": tx_sequences,
        })
    
    return results
```

---

## Step 6：对手地址标签化

对 topic1 / topic2 中高频出现的对手地址进行标签匹配，输出标签 List。

```python
def label_counterparts(
    rows1: list,
    rows2: list,
    known_labels: dict,
    top_n: int = 20
) -> list:
    """
    对 topic1=A* 侧的 topic2 字段，和 topic2=A* 侧的 topic1 字段，
    统计最高频对手地址，匹配已知标签，输出标签列表
    """
    addr_counts = defaultdict(int)
    
    for row in rows1:
        raw = row.get("topic2", "")
        if raw and len(raw) == 66:
            addr = "0x" + raw[-40:].lower()
            addr_counts[addr] += row.get("hit_count", 1)
    
    for row in rows2:
        raw = row.get("topic1", "")
        if raw and len(raw) == 66:
            addr = "0x" + raw[-40:].lower()
            addr_counts[addr] += row.get("hit_count", 1)
    
    top_addrs = sorted(addr_counts.items(), key=lambda x: -x[1])[:top_n]
    
    labeled = []
    for addr, count in top_addrs:
        label = known_labels.get(addr, known_labels.get(addr.lower(), "Unknown"))
        labeled.append({
            "address": addr,
            "hit_count": count,
            "label": label
        })
    
    return labeled
```

---

## Step 7：新地址发现

从结果中提取未出现在已知地址集中的新地址，用于后续扩展调查。

```python
def extract_new_addresses(
    rows: list,
    known: dict
) -> dict:
    """
    从 rows 中提取 topic1/topic2 中未知地址
    返回: {addr: {hit_count, sample_tx, contract, topic0}}
    """
    new = {}
    for row in rows:
        for field in ["topic1", "topic2"]:
            val = row.get(field, "")
            if val and len(val) == 66:
                addr = "0x" + val[-40:].lower()
                if addr not in known and addr not in new:
                    new[addr] = {
                        "hit_count": row.get("hit_count", 0),
                        "sample_tx": row.get("sample_tx", ""),
                        "contract": row.get("contract_address", ""),
                        "topic0": row.get("topic0", "")
                    }
    return new
```

---

## Step 8：主流程入口

```python
import csv
import io

def run_skill(
    address: str,
    logs_table: str,
    block_time_start: str = "2024-01-01",
    top_n_initial: int = 10,
    top_n_expand: int = 50,
    dominance_threshold: float = 0.40,
    gap_threshold: float = 0.15,
    min_sample_size: int = 20,
    max_hash_examples: int = 20,
    known_labels: dict = None
) -> str:
    """
    主入口：执行完整的 EVM log 关联模式识别流程
    返回 CSV 格式字符串
    """
    if known_labels is None:
        known_labels = {}

    print(f"\n=== EVM Log 模式识别 ===")
    print(f"目标地址: {address}")
    print(f"数据表: {logs_table}\n")

    # Step 0: Padding
    A_padded = pad_address(address)
    print(f"[Step 0] A* = {A_padded}")

    # Step 1: 双向检索
    rows1, rows2 = fetch_log_patterns(address, logs_table, block_time_start, top_n_expand)
    print(f"[Step 1] topic1 命中: {len(rows1)} 行 | topic2 命中: {len(rows2)} 行")

    # Step 2: 聚合
    pat1 = aggregate_patterns(rows1, side="topic1")
    pat2 = aggregate_patterns(rows2, side="topic2")
    merged = merge_patterns(pat1, pat2)
    print(f"[Step 2] 合并后模式数: {len(merged)}")

    # Step 3: 强/弱分类
    strong, weak = classify_patterns(
        merged, top_n_initial, dominance_threshold, gap_threshold, min_sample_size
    )
    print(f"[Step 3] 强模式: {len(strong)} | 弱模式: {len(weak)}")

    # Step 4: 扩展弱模式（可选，按需开启）
    # expanded_weak = expand_weak_patterns(address, logs_table, weak, block_time_start, top_n_expand)

    # Step 5: Hash 回查
    pattern_with_hashes = fetch_pattern_hashes(
        address, logs_table, strong, block_time_start, max_hash_examples
    )

    # Step 6: 对手地址标签化
    labeled_counterparts = label_counterparts(rows1, rows2, known_labels)
    print(f"\n[Step 6] 高频对手地址（Top {len(labeled_counterparts)}）:")
    for item in labeled_counterparts:
        print(f"  {item['address']}  [{item['label']}]  hit={item['hit_count']}")

    # Step 7: 新地址发现
    known_set = {k.lower(): v for k, v in known_labels.items()}
    known_set[address.lower()] = "TARGET"
    new_addrs = extract_new_addresses(rows1 + rows2, known_set)
    print(f"\n[Step 7] 新发现地址: {len(new_addrs)}")
    for addr, info in sorted(new_addrs.items(), key=lambda x: -x[1]["hit_count"])[:10]:
        print(f"  {addr}  hit={info['hit_count']}  contract={info['contract']}")

    # Step 8: 输出 CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 强模式表
    writer.writerow(["=== 强模式 ==="])
    writer.writerow(["contract_address", "topic0", "total_hits", "top1_addr",
                     "top1_ratio", "gap_ratio", "counterpart_count",
                     "sides", "sample_txs", "tx_sequence_example"])
    for pat in pattern_with_hashes:
        seq_example = ""
        if pat.get("tx_sequences"):
            first_tx = list(pat["tx_sequences"].values())[0]
            seq_example = " → ".join(first_tx)
        writer.writerow([
            pat["contract"], pat["topic0"], pat["total"],
            pat.get("top1_addr", ""), pat.get("top1_ratio", ""),
            pat.get("gap_ratio", ""), pat.get("counterpart_count", ""),
            ";".join(pat.get("sides", [])),
            ";".join(pat.get("samples", [])[:3]),
            seq_example
        ])

    writer.writerow([])

    # 对手地址标签表
    writer.writerow(["=== 高频对手地址 ==="])
    writer.writerow(["address", "label", "hit_count"])
    for item in labeled_counterparts:
        writer.writerow([item["address"], item["label"], item["hit_count"]])

    writer.writerow([])

    # 新发现地址表
    writer.writerow(["=== 新发现地址 ==="])
    writer.writerow(["address", "hit_count", "contract", "topic0", "sample_tx"])
    for addr, info in sorted(new_addrs.items(), key=lambda x: -x[1]["hit_count"]):
        writer.writerow([addr, info["hit_count"], info["contract"],
                         info["topic0"], info["sample_tx"]])

    return output.getvalue()
```

---

## 使用示例

```python
KNOWN_LABELS = {
    "0xabcdef...": "Binance Hot Wallet",
    "0x123456...": "USDT Treasury",
    # ...
}

csv_output = run_skill(
    address="0xYourTargetAddress",
    logs_table="polygon.logs",
    block_time_start="2024-01-01",
    top_n_initial=10,
    top_n_expand=50,
    dominance_threshold=0.40,
    gap_threshold=0.15,
    min_sample_size=20,
    max_hash_examples=20,
    known_labels=KNOWN_LABELS
)

with open("output.csv", "w", encoding="utf-8") as f:
    f.write(csv_output)

print("完成，已输出 output.csv")
```

---

## 输出 CSV 结构

### 表一：强模式

| 字段 | 说明 |
|------|------|
| `contract_address` | 合约地址 |
| `topic0` | 事件签名 hash |
| `total_hits` | 总命中次数 |
| `top1_addr` | 最高频对手地址 |
| `top1_ratio` | 第一名占比 |
| `gap_ratio` | 第1/2名频率差 |
| `counterpart_count` | 不同对手地址总数 |
| `sides` | 出现在 topic1 侧/topic2 侧/两侧 |
| `sample_txs` | 样本交易哈希 |
| `tx_sequence_example` | 代表交易的事件序列（contract:topic0→…） |

### 表二：高频对手地址标签

| 字段 | 说明 |
|------|------|
| `address` | 对手地址 |
| `label` | 已知标签（Unknown 表示未标注） |
| `hit_count` | 与目标地址共同出现次数 |

### 表三：新发现地址

| 字段 | 说明 |
|------|------|
| `address` | 新地址 |
| `hit_count` | 命中次数 |
| `contract` | 最常见关联合约 |
| `topic0` | 最常见事件类型 |
| `sample_tx` | 样本哈希 |

---

## 注意事项

- **ABI 解码**：topic0 到事件名称的映射已从流程中移除（划线部分），如需要可单独调用 4bytes.directory API 补充
- **弱模式扩展**：`expand_weak_patterns` 默认注释，在目标地址交互模式稀疏时手动开启
- **数据量控制**：Dune `medium` 性能档适合 < 100 万行的查询；超大范围请切换 `large` 或缩短时间窗口
- **TRON/BSC 适配**：将 `logs_table` 改为对应链的表名，逻辑不变
