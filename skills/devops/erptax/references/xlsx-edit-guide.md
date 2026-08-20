# XLSX XML 编辑规范

## 单元格 XML 结构

```xml
<c r="A1" s="1" t="n">
  <f>SUM(B1:B10)</f>
  <v>1234.56</v>
</c>
```

| 属性 | 说明 | 是否可修改 |
|------|------|-----------|
| `r="A1"` | 单元格引用 | ❌ 禁止 |
| `s="1"` | 样式索引（颜色/字体/边框等）| ❌ 禁止 |
| `t="n"` | 类型（n=数字, s=字符串）| ❌ 禁止 |
| `<f>` | 公式内容 | ❌ 禁止修改 |
| `<v>` | 缓存值 | ✅ 只改这里 |

## 替换算法

```python
import re

def set_cell_value(xml_content, cell_ref, new_value):
    pattern = rf'(<c r="{re.escape(cell_ref)}"[^>]*>)(.*?)(</c>)'
    
    def replacer(m):
        inner = m.group(2)
        # 替换 <v>...</v>
        new_inner = re.sub(r'<v>[^<]*</v>', f'<v>{new_value}</v>', inner)
        # 如果没有 <v> 但有 <f>，插在 </f> 后面
        if '<v>' not in new_inner:
            if '<f' in new_inner:
                new_inner = re.sub(r'(</f>)', rf'\1<v>{new_value}</v>', new_inner)
            else:
                new_inner = f'<v>{new_value}</v>'
        return m.group(1) + new_inner + m.group(3)
    
    return re.subn(pattern, replacer, xml_content, flags=re.DOTALL)
```

## 公式缓存值更新

Excel 打开时会忽略 `<v>`，自动重算 `<f>`。但**必须保留正确的缓存值**，否则：
- 打印/导出 PDF 时会显示错误
- 某些版本会显示公式而非值

所以：更新 `<v>` 时，填入**实际计算结果**，让 Excel 无需重算即可显示正确值。

## calcChain.xml

位于 `xl/calcChain.xml`，记录了公式的计算顺序。**编辑 XML 后必须删除**，否则 Excel 可能使用旧的计算链。

删除方法：
```python
import os
calc = '/tmp/work/xl/calcChain.xml'
if os.path.exists(calc):
    os.remove(calc)
```

## 查找单元格

用正则精确匹配：
```python
import re

with open('sheet1.xml', 'r') as f:
    content = f.read()

targets = ['D7', 'E7', 'H11', 'H17']
for t in targets:
    m = re.search(rf'<c r="{re.escape(t)}"[^>]*>.*?</c>', content, re.DOTALL)
    if m:
        print(f'{t}: {m.group()[:200]}')
    else:
        print(f'{t}: NOT FOUND')
```

## 样式（s属性）说明

`xl/styles.xml` 的 `<cellXfs>` 段定义了每个 `s=` 索引对应的样式：
- `s=34`: 蓝色输入格（数值）
- `s=40`: 黑色汇总格（公式）
- `s=44`: 蓝色合计行

**绝对不能改 s= 属性**，否则颜色和字体全部乱套。
