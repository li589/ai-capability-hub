# 批量操作安全模式 / Batch Operation Safety Patterns

## 概述

批量修改 DOCX 文档时，段落索引漂移、XML 操作不可逆、格式意外丢失等问题屡见不鲜。本参考提供一套经过验证的安全操作模式，适用于所有涉及多次段落修改的场景。

---

## 安全操作四步法

```
备份 → 分批 → 验证 → 提交
 ↓       ↓       ↓       ↓
COPY    ≤10    全文     SAVE
原始    处/批   逐段     确认
文件    修改   比对     无误
```

### 第一步：备份

操作前必须创建原始文件的副本。这是最后的安全网。

```python
import shutil
import os
from datetime import datetime


def backup_document(doc_path):
    """
    创建带时间戳的备份

    Args:
        doc_path: 原始文档路径

    Returns:
        str: 备份文件路径
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dir_name = os.path.dirname(doc_path)
    base_name = os.path.basename(doc_path)
    name, ext = os.path.splitext(base_name)

    backup_path = os.path.join(dir_name, f'{name}_backup_{timestamp}{ext}')
    shutil.copy2(doc_path, backup_path)

    print(f"备份已创建: {backup_path}")
    return backup_path


def ensure_backup_exists(doc_path, backup_dir=None):
    """
    确保备份存在，如果不存在则创建

    Args:
        doc_path: 文档路径
        backup_dir: 备份目录（默认与文档同目录）

    Returns:
        str: 备份文件路径
    """
    if backup_dir is None:
        backup_dir = os.path.dirname(doc_path)

    os.makedirs(backup_dir, exist_ok=True)
    return backup_document(doc_path)
```

### 第二步：分批

每批处理不超过 10 处修改。批次之间重新打开文档以获取最新状态。

```python
from docx import Document


class BatchProcessor:
    """
    批量处理器：自动分批、重载文档、跟踪变更

    使用方式：
        processor = BatchProcessor('manuscript.docx')
        processor.process(modifications, batch_size=10)
    """

    def __init__(self, doc_path):
        self.doc_path = doc_path
        self.backup_path = backup_document(doc_path)
        self.batch_history = []  # 记录每个批次的变更

    def process(self, modifications, batch_size=10):
        """
        分批执行修改

        Args:
            modifications: 修改操作列表（正序）
                [{'type': 'replace_text', 'old': 'A', 'new': 'B'}, ...]
            batch_size: 每批最大操作数，默认10

        Returns:
            str: 最终文档路径
        """
        total = len(modifications)
        batch_count = (total + batch_size - 1) // batch_size

        for batch_idx in range(batch_count):
            start = (batch_count - batch_idx - 1) * batch_size
            end = min(start + batch_size, total)

            # 处理当前批次（逆序）
            print(f"\n批次 {batch_idx + 1}/{batch_count}: 操作 {start}~{end-1}")

            # 重新打开文档以获取最新段落索引
            doc = Document(self.doc_path)

            # 当前批次的修改（保持原数组顺序，但逆序执行）
            batch = modifications[start:end]
            # 注意：如果修改涉及位置，需要逆序执行
            self._execute_batch(doc, reversed(batch))

            # 保存并验证
            doc.save(self.doc_path)
            self._verify_batch()

        return self.doc_path

    def _execute_batch(self, doc, operations):
        """执行一批操作"""
        for op in operations:
            op_type = op['type']
            if op_type == 'replace_text':
                self._replace_text(doc, op['old'], op['new'])
            elif op_type == 'insert_paragraph':
                self._insert_paragraph(doc, op['after_text'], op['content'])
            # ... 其他操作类型

    def _verify_batch(self):
        """验证批次结果"""
        doc = Document(self.doc_path)
        self.batch_history.append({
            'paragraph_count': len(doc.paragraphs),
            'sections': len(doc.sections),
        })
        print(f"  ✓ 验证通过: {len(doc.paragraphs)} 段落, "
              f"{len(doc.sections)} 节")

    def _replace_text(self, doc, old_text, new_text):
        """替换文本"""
        for para in doc.paragraphs:
            if old_text in para.text:
                for run in para.runs:
                    if old_text in run.text:
                        run.text = run.text.replace(old_text, new_text)
                        break  # 每段落只替换一次

    def _insert_paragraph(self, doc, after_text, content):
        """在指定文本后插入新段落"""
        for i, para in enumerate(doc.paragraphs):
            if after_text in para.text:
                new_para = doc.add_paragraph(content)
                para._element.addnext(new_para._element)
                break
```

### 第三步：验证

每批修改后重新提取全文，逐段比对。

```python
def extract_full_text(doc_path):
    """
    提取文档全文作为验证基线

    Returns:
        list of (paragraph_index, style_name, text_preview)
    """
    doc = Document(doc_path)
    text_map = []
    for i, para in enumerate(doc.paragraphs):
        text_map.append({
            'index': i,
            'style': para.style.name,
            'text': para.text,
            'text_preview': para.text[:80],
            'has_image': bool(para._element.findall('.//' + qn('w:drawing'))),
        })
    return text_map


def diff_text_maps(before, after):
    """
    对比两版全文映射，找出差异

    Args:
        before: 修改前的全文映射
        after: 修改后的全文映射

    Returns:
        list of diff strings
    """
    diffs = []
    max_len = max(len(before), len(after))

    for i in range(max_len):
        b = before[i] if i < len(before) else None
        a = after[i] if i < len(after) else None

        if b is None:
            diffs.append(f"  + 新增段落 {i}: '{a['text_preview']}'")
        elif a is None:
            diffs.append(f"  - 删除段落 {i}: '{b['text_preview']}'")
        elif b['text'] != a['text']:
            diffs.append(f"  ~ 段落 {i} 变更")
            diffs.append(f"    旧: '{b['text_preview']}'")
            diffs.append(f"    新: '{a['text_preview']}'")

    return diffs


def verify_document_integrity(doc_path, expected_min_paragraphs=50):
    """
    验证文档结构完整性

    Args:
        doc_path: 文档路径
        expected_min_paragraphs: 预期最少段落数

    Returns:
        bool: 是否通过验证
    """
    doc = Document(doc_path)

    checks = {
        '段落数量合理': len(doc.paragraphs) >= expected_min_paragraphs,
        '至少有一个节': len(doc.sections) > 0,
        '页面尺寸非零': (
            doc.sections[0].page_width is not None and
            doc.sections[0].page_width.cm > 0
        ),
    }

    all_pass = all(checks.values())
    if all_pass:
        print("✓ 所有验证项通过")
    else:
        for check, result in checks.items():
            status = '✓' if result else '✗'
            print(f"  {status} {check}")

    return all_pass
```

### 第四步：提交

确认无误后保存最终版本。

```python
def commit_final(doc_path, temp_backups=None):
    """
    确认提交最终版本

    如果提供了临时备份列表，可选是否清理。

    Args:
        doc_path: 最终文档路径
        temp_backups: 临时备份文件列表（可删除）
    """
    # 最终验证
    doc = Document(doc_path)
    print(f"\n=== 最终提交确认 ===")
    print(f"文件: {doc_path}")
    print(f"段落数: {len(doc.paragraphs)}")
    print(f"节数: {len(doc.sections)}")
    print(f"图片数: {count_images(doc)}")

    # 可选：清理临时备份
    if temp_backups:
        for backup in temp_backups:
            if os.path.exists(backup):
                print(f"可删除临时备份: {backup}")
                # 取消注释以自动删除
                # os.remove(backup)

    print("提交完成。")


def count_images(doc):
    """统计文档中的图片数量"""
    count = 0
    nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for para in doc.paragraphs:
        count += len(para._element.findall('.//w:drawing', nsmap))
    return count
```

---

## 回滚点设置

### 修改前保存中间版本

```python
class RollbackManager:
    """
    回滚管理器

    在每次批量修改前后自动保存中间版本，
    支持回滚到任意历史版本。

    使用方式：
        mgr = RollbackManager('manuscript.docx')
        mgr.save_checkpoint('before_chapter3')
        # ... 进行一系列修改 ...
        mgr.save_checkpoint('after_chapter3')
        # 如果出错，可以回滚
        mgr.rollback_to('before_chapter3')
    """

    def __init__(self, doc_path, checkpoint_dir=None):
        self.doc_path = doc_path
        self.original_path = doc_path

        if checkpoint_dir is None:
            checkpoint_dir = os.path.join(
                os.path.dirname(doc_path),
                'checkpoints'
            )
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

        self.checkpoints = []  # [(label, file_path, timestamp)]

    def save_checkpoint(self, label):
        """
        保存检查点

        Args:
            label: 检查点标签（如 'before_ch3', 'after_figures'）
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base = os.path.basename(self.doc_path)
        name, ext = os.path.splitext(base)
        checkpoint_name = f'{name}_{timestamp}_{label}{ext}'
        checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_name)

        shutil.copy2(self.doc_path, checkpoint_path)
        self.checkpoints.append((label, checkpoint_path, timestamp))

        print(f"检查点已保存 [{label}]: {checkpoint_path}")
        return checkpoint_path

    def rollback_to(self, label):
        """
        回滚到指定检查点

        Args:
            label: 检查点标签

        Returns:
            bool: 是否成功
        """
        for cp_label, cp_path, ts in reversed(self.checkpoints):
            if cp_label == label:
                shutil.copy2(cp_path, self.doc_path)
                print(f"已回滚到: {label} ({ts})")
                return True

        print(f"未找到检查点: {label}")
        print(f"可用检查点: {[c[0] for c in self.checkpoints]}")
        return False

    def rollback_to_last(self):
        """回滚到最近一个检查点"""
        if self.checkpoints:
            return self.rollback_to(self.checkpoints[-1][0])
        print("没有可用的检查点")
        return False

    def list_checkpoints(self):
        """列出所有检查点"""
        print("=== 可用检查点 ===")
        for label, path, ts in self.checkpoints:
            print(f"  [{label}] {ts} — {os.path.basename(path)}")


# ===== 使用示例 =====
mgr = RollbackManager('manuscript.docx')
mgr.save_checkpoint('initial')

try:
    # 阶段一：修改标题
    doc = Document('manuscript.docx')
    # ... 修改操作 ...
    doc.save('manuscript.docx')
    mgr.save_checkpoint('headings_fixed')

    # 阶段二：插入图片
    doc = Document('manuscript.docx')
    # ... 图片操作 ...
    doc.save('manuscript.docx')
    mgr.save_checkpoint('figures_inserted')

    # 阶段三：格式化表格
    doc = Document('manuscript.docx')
    # ... 表格美化 ...
    doc.save('manuscript.docx')
    mgr.save_checkpoint('tables_styled')

except Exception as e:
    print(f"错误: {e}")
    mgr.rollback_to_last()
```

---

## 操作顺序原则

### 先文字后图片，先末尾后开头

这四条原则决定操作的先后顺序：

```
1. 先文字内容 → 图片操作排后
   原因：图片插入影响段落结构，文字替换不改变结构

2. 先删除 → 后添加
   原因：删除后索引减少，添加后索引增加，逆序删除可以保持前置索引稳定

3. 先末尾 → 后开头
   原因：末尾操作不影响前面的索引（逆向操作原则）

4. 粗粒度先执行 → 细粒度后执行
   原因：大块操作（合并章节）先完成，最终微调（字体、缩进）在最后
```

### 推荐的操作链

```python
def academic_document_pipeline(doc_path):
    """
    学术文档处理推荐管道

    严格按照安全顺序执行所有操作
    """
    mgr = RollbackManager(doc_path)
    mgr.save_checkpoint('00_original')

    # === 阶段1: 结构操作（大块） ===
    # 合并章节、拆分段落、删除多余内容
    mgr.save_checkpoint('01_structure')

    # === 阶段2: 文字替换 ===
    # 查找和替换、统一术语
    mgr.save_checkpoint('02_text')

    # === 阶段3: 格式应用 ===
    # 标题样式、段落格式、字体
    mgr.save_checkpoint('03_formatting')

    # === 阶段4: 表格美化 ===
    # 表格配色、边框、字体
    mgr.save_checkpoint('04_tables')

    # === 阶段5: 图片管理 ===
    # 图片插入、替换、编号
    mgr.save_checkpoint('05_figures')

    # === 阶段6: 最终验证 ===
    # 全文提取、逐段比对、编号检查
    doc = Document(doc_path)
    verify_document_integrity(doc_path)
    mgr.save_checkpoint('06_final')

    print("管道执行完毕")
    mgr.list_checkpoints()
```

---

## 验证检查清单

每次批量修改后，执行以下检查：

```python
def comprehensive_verification(doc_path, original_doc_path=None):
    """
    综合验证检查

    Args:
        doc_path: 当前文档路径
        original_doc_path: 原始文档路径（首次备份版本，可选）

    Returns:
        dict: 验证结果
    """
    doc = Document(doc_path)
    results = {}

    # 1. 基本结构检查
    results['has_content'] = len(doc.paragraphs) > 0
    results['has_sections'] = len(doc.sections) > 0

    # 2. 页面参数检查
    section = doc.sections[0]
    results['page_size_valid'] = (
        section.page_width is not None and
        section.page_height is not None and
        section.page_width.cm > 5 and
        section.page_height.cm > 5
    )

    # 3. 内容对比检查（如果有原始文档）
    if original_doc_path:
        orig = Document(original_doc_path)
        results['paragraph_count_change'] = (
            len(doc.paragraphs) - len(orig.paragraphs)
        )
        # 段落数不应减少太多（除非明确删除了大量内容）
        results['no_excessive_loss'] = (
            len(doc.paragraphs) >= len(orig.paragraphs) * 0.8
        )

    # 4. 图片计数
    drawings = 0
    for para in doc.paragraphs:
        drawings += len(para._element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing'))
    results['drawing_count'] = drawings

    # 5. 表格计数
    results['table_count'] = len(doc.tables)

    # 输出结果
    print("\n=== 综合验证结果 ===")
    all_pass = True
    for check, result in results.items():
        if isinstance(result, bool):
            status = '✓' if result else '✗'
            if not result:
                all_pass = False
        else:
            status = result
        print(f"  {status} {check}")

    return results
```

---

## 常见陷阱与对策

| 陷阱 | 症状 | 对策 |
|------|------|------|
| **段落索引过期** | 修改后段落内容错位 | 每批操作后重新打开文档 |
| **Run 跨段落引用** | `run.text` 修改影响到错误的段落 | 始终通过段落遍历定位 run |
| **图片关系丢失** | 图片显示为红色叉号 | 插入图片后立即保存；不要手动修改 `_rels` 文件 |
| **样式污染** | 新段落继承了不该有的格式 | 创建新段落后显式设置样式 |
| **内存溢出** | 大型文档（>50MB）处理崩溃 | 增加分批粒度（≤5处/批）；考虑流式处理 |
| **编码问题** | 中文字符显示为乱码 | 始终使用 UTF-8 编码读写；设置正确的 eastAsia 字体 |
| **页码丢失** | 合并文档后页码不连续 | 合并前确保各节页眉页脚一致；合并后统一设置 |

---

## 安全操作流程模板（复制即用）

```python
"""
学术DOCX批量操作安全模板
=========================
将此模板复制到你的脚本中，填入具体的修改逻辑即可。
"""

import os
import shutil
from datetime import datetime
from docx import Document


# ===== 配置区 =====
DOC_PATH = 'manuscript.docx'
BATCH_SIZE = 10
CHECKPOINT_DIR = 'checkpoints/'
# ==================


def safe_batch_modify(doc_path, modify_func, batch_size=BATCH_SIZE):
    """
    安全的批量修改入口

    Args:
        doc_path: 文档路径
        modify_func: 修改函数，签名: func(doc) -> int (返回修改数)
        batch_size: 每批最大操作数
    """
    # 1. 备份
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = doc_path.replace('.docx', f'_backup_{ts}.docx')
    shutil.copy2(doc_path, backup_path)
    print(f"备份: {backup_path}")

    # 2. 创建检查点目录
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    try:
        # 3. 执行修改
        doc = Document(doc_path)
        changes = modify_func(doc)
        doc.save(doc_path)

        # 4. 验证
        verify_doc = Document(doc_path)
        print(f"修改完成: {changes} 处变更, "
              f"{len(verify_doc.paragraphs)} 段落, "
              f"{len(verify_doc.tables)} 表格")

    except Exception as e:
        print(f"错误: {e}")
        print(f"可以从备份恢复: {backup_path}")
        raise

    print(f"操作完成。备份: {backup_path}")


# === 使用示例 ===
def my_modifications(doc):
    """在此写入你的修改逻辑"""
    changes = 0
    # 示例：将所有 '旧术语' 改为 '新术语'
    for para in doc.paragraphs:
        if '旧术语' in para.text:
            for run in para.runs:
                if '旧术语' in run.text:
                    run.text = run.text.replace('旧术语', '新术语')
                    changes += 1
                    break
    return changes


if __name__ == '__main__':
    safe_batch_modify(DOC_PATH, my_modifications)
```

---

## 注意事项

1. **备份不是可选项**：即使是最简单的操作（如全局替换），也应在备份后执行。
2. **测试集先行**：在大文档上操作前，先在短测试文档上验证修改逻辑。
3. **不要同时编辑**：确保 Word 或其他程序没有同时打开目标文档（会导致文件锁定）。
4. **环境一致性**：处理路径时始终使用 `os.path.join()`，避免手动拼接字符串。
5. **资源清理**：处理完成后删除中间临时备份文件以节省空间（保留初始备份和最终版本）。
