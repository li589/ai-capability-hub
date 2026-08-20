# 技术操作类常见问题 FAQ

## Word排版问题

**Q：页眉页脚怎么设置？**
A：
1. **分节设置**：不同章节需要不同页眉时，插入"分节符"（布局→分隔符→下一页）
2. **取消链接**：双击页眉→取消"链接到前一节"，可独立设置
3. **奇偶页不同**：页眉页脚工具→勾选"奇偶页不同"
4. **首页不同**：封面页不显示页眉→勾选"首页不同"
5. **页码格式**：插入→页码→设置页码格式（起始页、编号样式）
6. **页眉横线**：选中页眉文字→开始→边框→无边框（或Ctrl+Shift+N清除格式）

**Q：目录怎么自动生成和更新？**
A：
1. **设置标题样式**：选中标题→开始→标题1/2/3（必须先用样式，不能手动调字号）
2. **插入目录**：引用→目录→自动目录1/2
3. **更新目录**：右键目录→更新域→更新整个目录（或F9）
4. **目录格式**：引用→目录→自定义目录→修改（调整字体、缩进）
5. **目录报错"未找到目录项"**：检查标题是否应用了样式，而非手动格式

**Q：交叉引用怎么用？**
A：
1. **引用图表**：引用→交叉引用→引用类型（图/表）→选择编号→插入
2. **引用章节**：引用→交叉引用→引用类型（标题）→选择章节→插入
3. **引用页码**：引用→交叉引用→引用内容（页码）
4. **更新引用**：Ctrl+A全选→F9更新域（或右键→更新域）
5. **切换代码/显示**：Alt+F9（查看域代码）

**Q：参考文献格式怎么调整？**
A：
1. **使用尾注**：引用→插入尾注（编号格式：[1]）
2. **使用交叉引用**：引用→交叉引用→引用类型（尾注）
3. **批量调整**：查找替换（^e替换为[^&]）
4. **悬挂缩进**：选中参考文献→段落→悬挂缩进2字符
5. **间距调整**：段落→段前0段后0，行距固定值18磅

**Q：三线表怎么做？**
A：
1. 插入表格→选中表格→表设计→边框→无框线
2. 选中第一行→边框→上框线+下框线（1.5磅）
3. 选中最后一行→边框→下框线（1.5磅）
4. 标题行下加细线（0.75磅）
5. 表格属性→文字环绕→无（防止位置乱跑）

## 参考文献管理

**Q：Zotero怎么和Word联动？**
A：
1. **安装插件**：Zotero→工具→插件→安装Word插件
2. **插入引用**：Word→Zotero→Add/Edit Citation→搜索文献→回车
3. **生成参考文献**：Zotero→Add/Edit Bibliography
4. **切换格式**：Zotero→Document Preferences→选择格式（GB/T 7714）
5. **刷新**：修改后点击Refresh
6. ** unlink**：定稿后点击Unlink Citations（解除域链接，转为纯文本）

**Q：EndNote导入中文文献乱码？**
A：
1. **导出格式**：知网导出→EndNote格式（.enw）
2. **编码设置**：Edit→Preferences→Display Fonts→宋体/UTF-8
3. **过滤器**：导入时选择正确的Import Option（Reference Manager(RIS)）
4. **手动修正**：双击文献→手动修改Author/Title字段
5. **批量替换**：Edit→Change/Move/Copy Fields

**Q：合并多个文献库？**
A：
1. **Zotero**：文件→导入→选择另一个Zotero库（自动去重）
2. **EndNote**：File→Import→File→选择.enl文件
3. **去重**：Zotero→工具→合并重复项目；EndNote→Library→Find Duplicates
4. **标签整理**：导入后统一打标签分类
5. **备份**：合并前备份原库（导出→Zotero RDF）

## 图表制作问题

**Q：Excel图表怎么符合学术规范？**
A：
1. **删除多余元素**：网格线、图例（如只有一组数据）、背景色
2. **坐标轴**：加粗、标签、单位（如"时间(s)"）
3. **字体**：Arial或Times New Roman，字号≥8
4. **颜色**：黑白优先，如需彩色用色盲友好配色（ColorBrewer）
5. **分辨率**：复制→粘贴为增强型图元文件（EMF）到Word
6. **误差线**：图表设计→添加图表元素→误差线→标准差/标准误

**Q：Python matplotlib怎么做出发表级图表？**
A：
```python
import matplotlib.pyplot as plt

# 设置全局参数
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['xtick.major.width'] = 1.2
plt.rcParams['ytick.major.width'] = 1.2

# 绘制
fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
ax.plot(x, y, 'k-', linewidth=1.5, label='Group 1')
ax.set_xlabel('Time (s)', fontsize=12)
ax.set_ylabel('Response (ms)', fontsize=12)
ax.legend(frameon=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('figure.png', dpi=300, bbox_inches='tight')
```

**Q：R ggplot2怎么做出发表级图表？**
A：
```r
library(ggplot2)

p <- ggplot(data, aes(x=group, y=score, fill=group)) +
  geom_bar(stat="summary", fun="mean", width=0.6, color="black") +
  geom_point(position=position_dodge(width=0.6), size=2) +
  scale_fill_manual(values=c("white", "gray")) +
  labs(x="Group", y="Score (points)") +
  theme_classic() +
  theme(
    text = element_text(size=12, family="Arial"),
    axis.line = element_line(size=0.8),
    legend.position = "none"
  )
ggsave("figure.png", p, dpi=300, width=6, height=4)
```

## 公式编辑问题

**Q：MathType怎么批量调整公式格式？**
A：
1. **定义样式**：大小→定义→设置完整/上标/下标/符号的大小
2. **批量应用**：格式化公式→MathType预设→保存为默认
3. **编号对齐**：插入编号→右对齐→制表位（居中20字符，右对齐40字符）
4. **转换LaTeX**：预置→剪切和复制预置→选择LaTeX 2.09
5. **批量修改**：选中多个公式→大小→其他（统一调整）

**Q：Word自带公式编辑器怎么用？**
A：
1. **插入**：插入→公式→插入新公式（Alt+=）
2. **手写识别**：公式→墨迹公式（触摸屏可用）
3. **LaTeX输入**：公式→转换→LaTeX（支持部分语法）
4. **编号**：公式后插入(1)→右对齐→制表位
5. **交叉引用**：引用→交叉引用→公式编号

**Q：LaTeX公式怎么对齐编号？**
A：
```latex
\begin{equation}
E = mc^2
\label{eq:emc2}
\end{equation}

% 多行对齐
\begin{align}
a &= b + c \\
  &= d + e + f \\
  &= g + h
\label{eq:align}
\end{align}

% 引用：如公式\ref{eq:emc2}所示
```

## 文件转换问题

**Q：PDF怎么转Word可编辑？**
A：
1. **Adobe Acrobat**：文件→导出到→Microsoft Word（保留格式较好）
2. **WPS**：PDF→右键→PDF转Word（免费版有水印）
3. **在线工具**：iLovePDF、Smallpdf（注意隐私）
4. **识别问题**：扫描版PDF需先OCR（Adobe/ABBYY）
5. **格式修复**：转换后检查：分页、页眉、公式、图表

**Q：LaTeX怎么转Word？**
A：
1. **Pandoc**：`pandoc input.tex -o output.docx --bibliography=refs.bib`
2. **TeX4ht**：`make4ht file.tex "docx"`
3. **手动复制**：PDF→复制文字→粘贴到Word（公式需重新编辑）
4. **图表**：LaTeX生成PDF图表→插入Word
5. **参考文献**：导出BibTeX→导入EndNote/Zotero→Word

**Q：Word转PDF后格式变了？**
A：
1. **字体嵌入**：文件→选项→保存→将字体嵌入文件
2. **打印转PDF**：文件→打印→Microsoft Print to PDF（比另存为稳定）
3. **页边距检查**：页面布局→页边距→自定义（确保与Word一致）
4. **图表检查**：Word中图表→组合→再转PDF（防止错位）
5. **目录检查**：更新目录后再转PDF（防止页码错误）

## 其他技术问题

**Q：论文图片分辨率不够？**
A：
1. **矢量图**：优先用PDF/EPS/EMF/SVG（无限放大）
2. **位图**：≥300 dpi（印刷标准），≥150 dpi（电子版）
3. **截图**：放大200%再截图（提高分辨率）
4. **软件导出**：Origin/Visio→导出→PDF/EMF（矢量）
5. **Photoshop**：图像→图像大小→分辨率300→重新采样

**Q：怎么批量调整图片大小？**
A：
1. **Word**：选中图片→格式→大小→统一高度/宽度
2. **Photoshop**：文件→自动→PDF演示文稿→统一尺寸
3. **Python**：
```python
from PIL import Image
img = Image.open('input.jpg')
img = img.resize((width, height), Image.Resampling.LANCZOS)
img.save('output.jpg', dpi=(300, 300))
```
4. **在线工具**：iLoveIMG批量调整（注意隐私）

**Q：论文文件太大怎么压缩？**
A：
1. **图片压缩**：选中图片→格式→压缩图片→150ppi（打印）/96ppi（屏幕）
2. **PDF压缩**：Adobe Acrobat→文件→另存为其他→缩小大小的PDF
3. **在线压缩**：Smallpdf、iLovePDF（注意隐私）
4. **分卷压缩**：论文正文+附录分开
5. **删除隐藏内容**：文件→信息→检查问题→检查文档→删除隐藏内容
