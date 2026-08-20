/**
 * MarkText 汉化核心脚本
 * 版本: v1.3 (基于 MarkText v0.17.1)
 * 汉化总数: v1.2补充 + v1.3补充
 *
 * 用法:
 *   先解包 asar，再运行本脚本，再重新打包。
 *   通常由 hanhua-apply.js 调用，不需要手动执行。
 */

const fs = require('fs');
const path = require('path');

// 解包目录：由调用方通过环境变量传入，默认为 temp-unpacked
const unpackedDir = process.env.HANHUA_UNPACKED_DIR || path.join(process.cwd(), 'temp-unpacked');
const rendererPath = path.join(unpackedDir, 'dist', 'electron', 'renderer.js');
const mainPath    = path.join(unpackedDir, 'dist', 'electron', 'main.js');

if (!fs.existsSync(rendererPath)) {
  console.error('[错误] 未找到解包文件: ' + rendererPath);
  console.error('请先执行: asar extract app.asar <解包目录>');
  process.exit(1);
}

let rendererContent = fs.readFileSync(rendererPath, 'utf8');
let mainContent = fs.existsSync(mainPath) ? fs.readFileSync(mainPath, 'utf8') : '';

// ============================================================
// 翻译字典（387处）
// ============================================================
const TRANSLATIONS = {
  // --- 顶层菜单 ---
  '"&File"': '"文件(&F)"',
  '"&Edit"': '"编辑(&E)"',
  '"&Paragraph"': '"段落(&P)"',
  '"F&ormat"': '"格式(&O)"',
  '"&View"': '"视图(&V)"',
  '"&Window"': '"窗口(&W)"',
  '"&Help"': '"帮助(&H)"',
  '"&Theme"': '"主题(&T)"',

  // --- 文件菜单 ---
  '"New File"': '"新建文件"',
  '"Open File"': '"打开文件"',
  '"New Tab"': '"新建标签页"',
  '"New Window"': '"新建窗口"',
  '"Open Folder"': '"打开文件夹"',
  '"Save"': '"保存"',
  '"Save As..."': '"另存为..."',
  '"Rename..."': '"重命名..."',
  '"Move..."': '"移动..."',
  '"Close current Tab"': '"关闭当前标签页"',
  '"Close Window"': '"关闭窗口"',
  '"Print current Tab"': '"打印当前标签页"',
  '"Import..."': '"导入..."',
  '"Export"': '"导出"',
  '"Preferences"': '"偏好设置"',
  '"Quit"': '"退出"',

  // --- 编辑菜单 ---
  '"Undo"': '"撤销"',
  '"Redo"': '"重做"',
  '"Cut"': '"剪切"',
  '"Copy"': '"复制"',
  '"Paste"': '"粘贴"',
  '"Duplicate"': '"复制行"',
  '"Create Paragraph"': '"创建段落"',
  '"Delete Paragraph"': '"删除段落"',
  '"Find"': '"查找"',
  '"Find Next"': '"查找下一个"',
  '"Find Previous"': '"查找上一个"',
  '"Find in Folder"': '"在文件夹中查找"',
  '"Replace"': '"替换"',
  '"Select All"': '"全选"',
  '"Make Screenshot"': '"截图"',

  // --- 格式菜单 ---
  '"Strong"': '"加粗"',
  '"Emphasis"': '"斜体"',
  '"Underline"': '"下划线"',
  '"Strike"': '"删除线"',
  '"Highlight"': '"高亮"',
  '"Inline Code"': '"行内代码"',
  '"Inline Math"': '"行内数学"',
  '"Hyperlink"': '"超链接"',
  '"Insert Image"': '"插入图片"',
  '"Superscript"': '"上标"',
  '"Subscript"': '"下标"',
  '"Clear Format"': '"清除格式"',

  // --- 段落菜单 ---
  '"Transform into Heading 1"': '"转换为标题1"',
  '"Transform into Heading 2"': '"转换为标题2"',
  '"Transform into Heading 3"': '"转换为标题3"',
  '"Transform into Heading 4"': '"转换为标题4"',
  '"Transform into Heading 5"': '"转换为标题5"',
  '"Transform into Heading 6"': '"转换为标题6"',
  '"Upgrade Heading"': '"提升标题级别"',
  '"Degrade Heading"': '"降低标题级别"',
  '"Transform into Bullet List"': '"转换为无序列表"',
  '"Transform into Order List"': '"转换为有序列表"',
  '"Transform into Task List"': '"转换为任务列表"',
  '"Convert to Loose List Item"': '"转换为松散列表项"',
  '"Transform into Code Fence"': '"转换为代码块"',
  '"Transform into Quote Block"': '"转换为引用块"',
  '"Transform into Math Formula"': '"转换为数学公式"',
  '"Transform into HTML Block"': '"转换为 HTML 块"',
  '"Create Table"': '"创建表格"',
  '"Insert Horizontal Line"': '"插入水平线"',
  '"Insert Front Matter"': '"插入前言"',
  '"Create new Paragraph"': '"创建新段落"',

  // --- 视图菜单 ---
  '"Show Command Palette"': '"显示命令面板"',
  '"Toggle Sidebar"': '"切换侧边栏"',
  '"Toggle Tabs"': '"切换标签栏"',
  '"Toggle Table of Content"': '"切换目录"',
  '"Toggle Typewriter Mode"': '"切换打字机模式"',
  '"Focus Mode"': '"专注模式"',
  '"Toggle Source Code Mode"': '"切换源码模式"',
  '"Clear cache and reload images"': '"清除缓存并重新加载图片"',
  '"Show Developer Tools (Debug)"': '"显示开发者工具（调试）"',
  '"Reload Window (Debug)"': '"重新加载窗口（调试）"',

  // --- 窗口菜单 ---
  '"Minimize"': '"最小化"',
  '"Toggle Full Screen"': '"切换全屏"',
  '"Always on Top"': '"总在最前"',
  '"Zoom In"': '"放大"',
  '"Zoom Out"': '"缩小"',

  // --- 右键菜单 ---
  '"Copy As Markdown"': '"复制为 Markdown"',
  '"Copy As Html"': '"复制为 HTML"',
  '"Paste as Plain Text"': '"粘贴为纯文本"',
  '"Bold"': '"粗体"',
  '"Italic"': '"斜体"',
  '"Strikethrough"': '"删除线"',
  '"Image"': '"图片"',

  // --- 设置面板左侧导航 ---
  '"General"': '"通用"',
  '"Editor"': '"编辑器"',
  '"Theme"': '"主题"',
  '"Key Bindings"': '"快捷键"',
  '"About"': '"关于"',

  // --- 通用设置 ---
  '"Search preferences"': '"搜索偏好设置"',
  '"Sidebar"': '"侧边栏"',
  '"Wrap text in table of contents"': '"目录中自动换行"',
  '"Sort field for files in open folders"': '"打开文件夹的文件排序字段"',
  '"Creation time"': '"创建时间"',
  '"Modified time"': '"修改时间"',
  '"File name"': '"文件名"',
  '"Action on startup"': '"启动时操作"',
  '"Select Folder"': '"选择文件夹"',
  '"User interface language"': '"用户界面语言"',
  '"Requires restart."': '"需要重启。"',
  '"Auto Save"': '"自动保存"',
  '"Automatically save document changes"': '"自动保存文档更改"',
  '"Delay following document edit before automatically saving"': '"自动保存延迟"',
  '"Title bar style"': '"标题栏样式"',
  '"Custom"': '"自定义"',
  '"Hide scrollbars"': '"隐藏滚动条"',
  '"Zoom"': '"缩放"',

  // --- 编辑器设置 ---
  '"Maximum width of text editor"': '"文本编辑器最大宽度"',
  '"Remove leading and trailing empty lines"': '"删除首尾空行"',
  '"Automatically close brackets when writing"': '"输入时自动闭合括号"',
  '"Automatically complete markdown syntax"': '"自动补全 Markdown 语法"',
  '"Automatically close quotation marks"': '"自动闭合引号"',
  '"Preferred tab width"': '"首选 Tab 宽度"',
  '"Line separator type"': '"行分隔符类型"',
  '"Default"': '"默认"',
  '"Default encoding"': '"默认编码"',
  '"Automatically detect file encoding"': '"自动检测文件编码"',
  '"Handling of trailing newline characters"': '"尾部换行符处理"',
  '"Preserve style of original document"': '"保留原文档样式"',
  '"Ensure single trailing newline"': '"确保单个尾部换行"',
  '"Text direction"': '"文本方向"',
  '"Left to Right"': '"从左到右"',
  '"Right to Left"': '"从右到左"',
  '"Hide hint for selecting type of new paragraph"': '"隐藏新段落类型选择提示"',
  '"Hide popup when cursor is over link"': '"光标悬停链接时隐藏弹窗"',
  '"Whether to automatically check any related tasks"': '"是否自动检查关联任务"',
  '"Font family"': '"字体族"',
  '"Font size"': '"字体大小"',
  '"Line height"': '"行高"',

  // --- Markdown 设置 ---
  '"Prefer loose list items"': '"偏好松散列表项"',
  '"Preferred marker for bullet lists"': '"无序列表首选标记"',
  '"Preferred marker for ordered lists"': '"有序列表首选标记"',
  '"Preferred list indentation"': '"首选列表缩进"',
  '"Single space character"': '"单个空格字符"',
  '"Two space characters"': '"两个空格字符"',
  '"Tab character"': '"Tab 字符"',
  '"Front matter format"': '"前言格式"',
  '"Enable Pandoc-style superscript and subscript"': '"启用 Pandoc 风格上下标"',
  '"Enable Pandoc-style footnotes"': '"启用 Pandoc 风格脚注"',
  '"Enable HTML rendering"': '"启用 HTML 渲染"',
  '"Enable GitLab compatibility mode"': '"启用 GitLab 兼容模式"',
  '"Sequence diagram theme"': '"序列图主题"',
  '"Hand drawn"': '"手绘"',
  '"Simple"': '"简约"',
  '"Preferred heading style"': '"首选标题样式"',
  '"ATX heading"': '"ATX 样式标题"',
  '"Setext heading"': '"Setext 样式标题"',

  // --- 拼写检查 ---
  '"Enable spell checker"': '"启用拼写检查"',
  '"Use Hunspell instead of system spell checker on macOS and Windows 10"':
    '"在 macOS 和 Windows 10 上使用 Hunspell 替代系统拼写检查"',
  '"Hide marks for spelling errors"': '"隐藏拼写错误标记"',
  '"Default language for spell checker"': '"拼写检查默认语言"',

  // --- 主题 ---
  '"Automatically adjust application theme according to system settings"':
    '"根据系统设置自动调整应用主题"',
  '"Never"': '"从不"',
  '"Adjust theme at startup"': '"启动时调整主题"',

  // --- 图片 ---
  '"Keep original location"': '"保留原始位置"',
  '"Global or relative image folder"': '"全局或相对图片文件夹"',
  '"Global image folder"': '"全局图片文件夹"',
  '"Open..."': '"打开..."',
  '"Show in Folder"': '"在文件夹中显示"',
  '"Prefer relative assets folder"': '"偏好相对资源文件夹"',

  // --- 快捷键页面 ---
  '"Description"': '"描述"',
  '"Key Combination"': '"按键组合"',
  '"Options"': '"选项"',
  '"Restore default key bindings"': '"恢复默认快捷键"',
  '"Customize MarkText shortcuts and click on the save button below to apply all changes (requires a restart). All available and default key binding can be found"':
    '"自定义 MarkText 快捷键，点击下方保存按钮以应用所有更改（需要重启）。所有可用的默认快捷键可"',

  // --- 快捷键分类前缀 ---
  '"Edit: "': '"编辑："',
  '"File: "': '"文件："',
  '"Format: "': '"格式："',
  '"Paragraph: "': '"段落："',
  '"View: "': '"视图："',
  '"Window: "': '"窗口："',
  '"Misc: "': '"其他："',
  '"MarkText: "': '"MarkText："',

  // --- Vue.js e._v() 文本节点 ---
  'e._v("Action on startup:")': 'e._v("启动时操作：")',
  'e._v("Text editor settings:")': 'e._v("文本编辑器设置：")',
  'e._v("Code block settings:")': 'e._v("代码块设置：")',
  'e._v("Writing behavior:")': 'e._v("写作行为：")',
  'e._v("File representation:")': 'e._v("文件格式：")',
  'e._v("Markdown extensions:")': 'e._v("Markdown 扩展：")',
  'e._v("Diagrams:")': 'e._v("图表：")',
  'e._v("Sidebar:")': 'e._v("侧边栏：")',
  'e._v("Misc:")': 'e._v("其他：")',
  'e._v("Window:")': 'e._v("窗口：")',
  'e._v("Auto Save:")': 'e._v("自动保存：")',
  'e._v("Lists:")': 'e._v("列表：")',
  'e._v("Compatibility:")': 'e._v("兼容性：")',

  // ============================================================
  // v1.1 补充翻译
  // ============================================================

  // --- 表格右键菜单 ---
  '"Resize Table"': '"调整表格大小"',
  '"Delete Table"': '"删除表格"',
  '"Remove Column"': '"删除列"',
  '"Remove Row"': '"删除行"',

  // --- 表格/图片对齐 ---
  '"Align Left"': '"左对齐"',
  '"Align Center"': '"居中对齐"',
  '"Align Right"': '"右对齐"',
  '"Align Middle"': '"垂直居中"',

  // --- 表格创建对话框 ---
  'label:"Rows"': 'label:"行数"',
  'label:"Columns"': 'label:"列数"',

  // --- 标签页右键菜单 ---
  '{label:"Close",id:"closeThisTab"': '{label:"关闭",id:"closeThisTab"',

  // --- 标签页/侧边栏 Rename ---
  '{label:"Rename",id:"renameFile"': '{label:"重命名",id:"renameFile"',
  '{label:"Rename",id:"renameMenuItem"': '{label:"重命名",id:"renameMenuItem"',

  // --- 侧边栏右键菜单 ---
  '{label:"Move To Trash",id:"deleteMenuItem"': '{label:"移到回收站",id:"deleteMenuItem"',
  '{label:"Show In Folder",id:"showInFolderMenuItem"': '{label:"在文件夹中显示",id:"showInFolderMenuItem"',

  // --- 新文档界面：段落选择器标题 ---
  'title:"Paragraph"': 'title:"段落"',
  'title:"Code Block"': 'title:"代码块"',
  'title:"Quote Block"': 'title:"引用块"',
  'title:"HTML Block"': 'title:"HTML 块"',
  'title:"Order List"': 'title:"有序列表"',
  'title:"Bullet List"': 'title:"无序列表"',
  'title:"Horizontal Line"': 'title:"水平线"',

  // --- 新文档界面：段落操作按钮 ---
  'text:"Duplicate"': 'text:"创建副本"',
  'text:"Turn Into"': 'text:"转换为"',
  'text:"New Paragraph"': 'text:"新建段落"',

  // --- 图片工具栏 ---
  'tooltip:"Remove Image"': 'tooltip:"删除图片"',

  // --- 通知消息 ---
  'title:"Error while pasting"': 'title:"粘贴时出错"',
  'title:"Paste Forbidden"': 'title:"禁止粘贴"',
  'title:"Printing/Exporting failed"': 'title:"打印/导出失败"',
  'title:"Shortcut already in use"': 'title:"快捷键已被占用"',
  'title:"Error loading tab"': 'title:"加载标签页失败"',
  'title:"Error in Side Bar"': 'title:"侧边栏错误"',
  'title:"Error while deleting"': 'title:"删除时出错"',
  'title:"Exported successfully"': 'title:"导出成功"',
  'title:"Failed to save"': 'title:"保存失败"',

  // --- 设置面板补充 ---
  '"Add to Dictionary"': '"添加到词典"',
  '"Remove from Dictionary"': '"从词典中删除"',
  '"Change Language..."': '"更改语言..."',
  'title:"Case Sensitive"': 'title:"区分大小写"',
  'title:"Use query as RegEx"': 'title:"使用正则表达式"',
  'title:"Select whole word"': 'title:"全字匹配"',

  // --- 设置面板：标题栏样式 ---
  '{label:"Native",value:"native"': '{label:"原生",value:"native"',

  // --- 设置面板：尾行换行 ---
  '{label:"Do nothing",value:3}': '{label:"不处理",value:3}',

  // --- 导出设置 ---
  'label:"Header & Footer"': 'label:"页眉与页脚"',
  'label:"Style"': 'label:"样式"',

  // --- 新建文件夹 ---
  '"New Directory"': '"新建文件夹"',

  // --- 拼写检查标签 ---
  '"Change Language..."': '"更改语言..."',
  '"Add to Dictionary"': '"添加到词典"',
  '"Remove from Dictionary"': '"从词典中删除"',

  // --- 标签页右键：Copy path / Show in folder（小写版） ---
  '{label:"Copy path"': '{label:"复制路径"',
  '{label:"Show in folder"': '{label:"在文件夹中显示"',

  // ============================================================
  // v1.2 补充翻译
  // ============================================================

  // --- 标签页右键菜单补充 ---
  '{label:"Close others",id:"closeOtherTabs"': '{label:"关闭其他标签页",id:"closeOtherTabs"',
  '{label:"Close saved tabs",id:"closeSavedTabs"': '{label:"关闭已保存的标签页",id:"closeSavedTabs"',
  '{label:"Close all tabs",id:"closeAllTabs"': '{label:"关闭所有标签页",id:"closeAllTabs"',

  // --- 段落右键菜单 ---
  '{label:"Insert Paragraph Before",id:"insertParagraphBeforeMenuItem"': '{label:"在前面插入段落",id:"insertParagraphBeforeMenuItem"',
  '{label:"Insert Paragraph After",id:"insertParagraphAfterMenuItem"': '{label:"在后面插入段落",id:"insertParagraphAfterMenuItem"',

  // --- 表格行列插入 ---
  '{label:"Insert Column Left"': '{label:"在左侧插入列"',
  '{label:"Insert Column Right"': '{label:"在右侧插入列"',
  '{label:"Insert Row Above"': '{label:"在上方插入行"',
  '{label:"Insert Row Below"': '{label:"在下方插入行"',

  // --- 表格单元格合并 ---
  '{label:"Single cell",value:1}': '{label:"单个单元格",value:1}',
  '{label:"Three cells",value:2}': '{label:"三个单元格",value:2}',

  // --- 字数统计 ---
  'e._v("Words:")': 'e._v("字数：")',
  'e._v("Characters:")': 'e._v("字符数：")',
  'e._v("Paragraphs:")': 'e._v("段落数：")',

  // --- 新文档界面段落选择器标题补充 ---
  'title:"Header 1"': 'title:"标题 1"',
  'title:"Header 2"': 'title:"标题 2"',
  'title:"Header 3"': 'title:"标题 3"',
  'title:"Header 4"': 'title:"标题 4"',
  'title:"Header 5"': 'title:"标题 5"',
  'title:"Header 6"': 'title:"标题 6"',
  'title:"Table Block"': 'title:"表格块"',
  'title:"Display Math"': 'title:"数学公式"',
  'title:"To-do List"': 'title:"待办列表"',

  // --- 图表类型 ---
  'title:"Vega Chart"': 'title:"Vega 图表"',
  'title:"Flow Chart"': 'title:"流程图"',
  'title:"Sequence Diagram"': 'title:"时序图"',
  'title:"PlantUML Diagram"': 'title:"PlantUML 图"',
  'title:"Mermaid"': 'title:"Mermaid 图"',

  // --- 图片工具栏补充 ---
  'tooltip:"Edit Image"': 'tooltip:"编辑图片"',
  'tooltip:"Inline Image"': 'tooltip:"行内图片"',
  'tooltip:"Link"': 'tooltip:"链接"',
  'tooltip:"Clear Formatting"': 'tooltip:"清除格式"',

  // --- 通知消息补充 ---
  'title:"Image deletion URL"': 'title:"图片删除链接"',
  'title:"Save failure"': 'title:"保存失败"',

  // --- 更新相关 ---
  'title:"Update Available"': 'title:"有可用更新"',
  'title:"Update Downloaded"': 'title:"更新已下载"',
  'title:"Update not Available"': 'title:"暂无可用更新"',

  // --- e._v() 界面文本 ---
  'e._v("Create File")': 'e._v("创建文件")',
  'e._v("Empty project")': 'e._v("空项目")',
  'e._v("Export Options")': 'e._v("导出选项")',
  'e._v("Import Theme")': 'e._v("导入主题")',
  'e._v("Import or Open")': 'e._v("导入或打开")',
  'e._v("Left/Right:")': 'e._v("左/右：")',
  'e._v("Top/Bottom:")': 'e._v("上/下：")',
  'e._v("No folder open")': 'e._v("未打开文件夹")',
  'e._v("No results found.")': 'e._v("未找到结果。")',
  'e._v("Open a blank page")': 'e._v("打开空白页")',
  'e._v("Opened files")': 'e._v("已打开的文件")',
  'e._v("Table Of Contents")': 'e._v("目录")',
  'e._v("Spelling")': 'e._v("拼写")',
  'e._v("Delete")': 'e._v("删除")',
  'e._v("Update")': 'e._v("更新")',
  'e._v("Uploader")': 'e._v("上传器")',
  'e._v("Page margin in mm:")': 'e._v("页边距（毫米）：")',
  'e._v("Width/Height in mm:")': 'e._v("宽度/高度（毫米）：")',
  'e._v("Branch name (optional):")': 'e._v("分支名称（可选）：")',
  'e._v("Owner name:")': 'e._v("所有者名称：")',
  'e._v("Repo name:")': 'e._v("仓库名称：")',
  'e._v("Debug options:")': 'e._v("调试选项：")',
  'e._v("Shell script location:")': 'e._v("Shell 脚本位置：")',
  'e._v("Hunspell settings:")': 'e._v("Hunspell 设置：")',

  // --- 设置面板补充 label ---
  '{label:"Language"': '{label:"语言"',
  '{label:"Name"': '{label:"名称"',
  '{label:"Page"': '{label:"页面"',
  '{label:"Ignore"': '{label:"忽略"',
  '{label:"Info"': '{label:"信息"',
  '{label:"None"': '{label:"无"',
  '{label:"Operations"': '{label:"操作"',
  '{label:"Title"': '{label:"标题"',
  '{label:"Select"': '{label:"选择"',
  '{label:"Spelling..."': '{label:"拼写..."',
  '{label:"Embed link"': '{label:"嵌入链接"',

  // --- 行分隔符 ---
  '{label:"Line feed (LF)"': '{label:"换行符 (LF)"',
  '{label:"Carriage return and line feed (CRLF)"': '{label:"回车换行 (CRLF)"',
  // 子菜单选项（编辑->行尾格式）
  'label:"Carriage return and line feed (CRLF)"': 'label:"回车换行 (CRLF)"',
  'label:"Line feed (LF)"': 'label:"换行符 (LF)"',

  // --- 列表缩进 ---
  '{label:"True tab character"': '{label:"Tab 字符"',
  '{label:"Single space character"': '{label:"单个空格字符"',
  '{label:"Two space characters"': '{label:"两个空格字符"',
  '{label:"Three space characters"': '{label:"三个空格字符"',
  '{label:"Four space characters"': '{label:"四个空格字符"',

  // --- 尾部换行 ---
  '{label:"Trim all trailing"': '{label:"删除所有尾部"',
  '{label:"Ensure exactly one trailing"': '{label:"确保恰好一个尾部"',
  '{label:"Remove leading and trailing empty lines"': '{label:"删除首尾空行"',

  // --- 文件排序 ---
  '{label:"Modification time"': '{label:"修改时间"',

  // --- 前言格式 ---
  '{label:"TOML"': '{label:"TOML"',
  '{label:"JSON (;;)"': '{label:"JSON (;;)"',
  '{label:"JSON ({})"': '{label:"JSON ({})"',
  '{label:"YAML"': '{label:"YAML"',

  // --- 导出样式 ---
  '{label:"GitHub (Default)"': '{label:"GitHub（默认）"',
  '{label:"DocFX style"': '{label:"DocFX 风格"',
  '{label:"Academic"': '{label:"学术"',
  '{label:"Liber"': '{label:"Liber"',
  '{label:"Styled"': '{label:"样式化"',

  // --- 纸张大小 ---
  '{label:"A3 (297mm x 420mm)"': '{label:"A3 (297mm x 420mm)"',
  '{label:"A4 (210mm x 297mm)"': '{label:"A4 (210mm x 297mm)"',
  '{label:"A5 (148mm x 210mm)"': '{label:"A5 (148mm x 210mm)"',

  // --- 图片上传 ---
  '{label:"Unsplash"': '{label:"Unsplash"',

  // --- 其他 e._v() ---
  'e._v("Download additional Hunspell dictionaries")': 'e._v("下载额外的 Hunspell 词典")',
  'e._v("Dump keyboard information")': 'e._v("导出键盘信息")',
  'e._v("Hunspell settings:")': 'e._v("Hunspell 设置：")',
  'e._v("Import custom themes")': 'e._v("导入自定义主题")',
  'e._v("Installed Hunspell dictionaries")': 'e._v("已安装的 Hunspell 词典")',
  'e._v("Open the default directory")': 'e._v("打开默认目录")',
  'e._v("Open the themes folder")': 'e._v("打开主题文件夹")',
  'e._v("Privacy Statement")': 'e._v("隐私声明")',
  'e._v("Tell us your feedback?")': 'e._v("告诉我们您的反馈？")',
  'e._v("Terms of Service")': 'e._v("服务条款")',
  'e._v("Send us feedback via tweet")': 'e._v("通过推文发送反馈")',
  'e._v("Press Enter to continue or ESC to exit.")': 'e._v("按 Enter 继续或按 ESC 退出。")',
  'e._v("What\'s your experience feelings?")': 'e._v("您的使用体验如何？")',
  'e._v("Markdown")': 'e._v("Markdown")',
  'e._v("MarkText")': 'e._v("MarkText")',

  // ============================================================
  // v1.3 补充翻译
  // ============================================================

  // --- 搜索/替换框 ---
  'placeholder:"Replacement"': 'placeholder:"替换内容"',
  'content:"Replace All"': 'content:"全部替换"',
  'content:"Replace Single"': 'content:"替换单个"',

  // --- 文件菜单补充 ---
  'label:"Open File..."': 'label:"打开文件..."',
  'label:"Open Folder..."': 'label:"打开文件夹..."',
  'label:"Open Recent"': 'label:"最近打开"',
  'label:"Move To..."': 'label:"移动到..."',
  'label:"Print"': 'label:"打印"',

  // --- 编辑菜单补充 ---
  'label:"Copy as Markdown"': 'label:"复制为 Markdown"',
  'label:"Copy as HTML"': 'label:"复制为 HTML"',
  'label:"Line Ending"': 'label:"行尾格式"',

  // --- 段落菜单 ---
  'label:"Heading 1"': 'label:"标题 1"',
  'label:"Heading 2"': 'label:"标题 2"',
  'label:"Heading 3"': 'label:"标题 3"',
  'label:"Heading 4"': 'label:"标题 4"',
  'label:"Heading 5"': 'label:"标题 5"',
  'label:"Heading 6"': 'label:"标题 6"',
  'label:"Promote Heading"': 'label:"提升标题级别"',
  'label:"Demote Heading"': 'label:"降低标题级别"',
  'label:"Code Fences"': 'label:"代码块"',
  'label:"Quote Block"': 'label:"引用块"',
  'label:"Math Block"': 'label:"数学公式"',
  'label:"Html Block"': 'label:"HTML 块"',
  'label:"Ordered List"': 'label:"有序列表"',
  'label:"Bullet List"': 'label:"无序列表"',
  'label:"Task List"': 'label:"任务列表"',
  'label:"Loose List Item"': 'label:"松散列表项"',
  'label:"Horizontal Rule"': 'label:"水平线"',
  'label:"Front Matter"': 'label:"前言"',

  // --- 格式菜单补充 ---
  'tooltip:"Clear Formatting"': 'tooltip:"清除格式"',

  // --- 视图菜单 ---
  'label:"Command Palette..."': 'label:"命令面板..."',
  'label:"Source Code Mode"': 'label:"源码模式"',
  'label:"Typewriter Mode"': 'label:"打字机模式"',
  'label:"Show Sidebar"': 'label:"显示侧边栏"',
  'label:"Show Tab Bar"': 'label:"显示标签栏"',
  'label:"Toggle Table of Contents"': 'label:"切换目录"',
  'label:"Reload Images"': 'label:"重新加载图片"',

  // --- 窗口菜单 ---
  'label:"Show in Full Screen"': 'label:"全屏显示"',

  // --- 帮助菜单 ---
  'label:"Quick Start..."': 'label:"快速入门..."',
  'label:"Markdown Reference..."': 'label:"Markdown 参考..."',
  'label:"Changelog..."': 'label:"更新日志..."',
  'label:"Donate via Open Collective..."': 'label:"通过 Open Collective 捐款..."',
  'label:"Feedback via Twitter..."': 'label:"通过 Twitter 反馈..."',
  'label:"Report Issue or Request Feature..."': 'label:"反馈问题或功能建议..."',
  'label:"Website..."': 'label:"官方网站..."',
  'label:"Watch on GitHub..."': 'label:"在 GitHub 关注..."',
  'label:"Follow us on Github..."': 'label:"在 Github 关注我们..."',
  'label:"Follow us on Twitter..."': 'label:"在 Twitter 关注我们..."',
  'label:"License..."': 'label:"许可证..."',
  'label:"Check for updates..."': 'label:"检查更新..."',
  'label:"About MarkText..."': 'label:"关于 MarkText..."',

  // ============================================================
  // v1.4 补充翻译 - 导出选项对话框
  // ============================================================

  // --- 通用 ---
  'label:"Include top heading:"': 'label:"包含顶级标题："',
  'label:"Title:"': 'label:"标题："',

  // --- 页眉页脚 ---
  'label:"The text appear on all pages if header and/or footer is defined."': 'label:"如果定义了页眉和/或页脚，文本将出现在所有页面上。"',
  'label:"Header type:"': 'label:"页眉类型："',
  'label:"Footer type:"': 'label:"页脚类型："',
  'label:"Customize style:"': 'label:"自定义样式："',

  // --- 主题 ---
  'label:"You can change the document appearance by choosing a theme or create a handcrafted one."': 'label:"您可以通过选择主题或创建自定义主题来更改文档外观。"',
  'label:"Theme:"': 'label:"主题："',

  // --- 样式 ---
  'label:"Overwrite theme font settings:"': 'label:"覆盖主题字体设置："',
  'label:"Auto numbering headings:"': 'label:"自动编号标题："',
  'label:"Show front matter:"': 'label:"显示前言："',

  // --- 页面 ---
  'label:"Page size:"': 'label:"页面大小："',
  'label:"Landscape orientation:"': 'label:"横向方向："',

  // --- 信息 ---
  'label:"Please customize the page appearance and click on \\"export\\" to continue."': 'label:"请自定义页面外观并点击"导出"继续。"',
};

// ============================================================
// 执行替换
// ============================================================
let total = 0;

function replaceAll(content, dict) {
  for (const [src, dst] of Object.entries(dict)) {
    const count = content.split(src).length - 1;
    if (count > 0) {
      content = content.split(src).join(dst);
      total += count;
    }
  }
  return content;
}

rendererContent = replaceAll(rendererContent, TRANSLATIONS);
if (mainContent) mainContent = replaceAll(mainContent, TRANSLATIONS);

fs.writeFileSync(rendererPath, rendererContent, 'utf8');
if (mainContent) fs.writeFileSync(mainPath, mainContent, 'utf8');

console.log('[hanhua-core] 替换完成，共 ' + total + ' 处');
