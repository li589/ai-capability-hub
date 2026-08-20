#!/usr/bin/env python3
"""
Thesis Tutor v4.0 - 本地助手核心引擎
零成本架构:本地规则引擎 + 用户自配 DeepSeek API
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class IntentMatcher:
    """意图匹配器 - 本地规则版(支持多语言和同义词扩展)"""

    def __init__(self, language="zh"):
        """
        初始化意図マッチャー

        Args:
            language: 言語コード (zh/en/ja)
        """
        self.language = language

        # 按语言加载同义词和模式
        self.synonyms = self._load_synonyms()
        self.patterns = self._load_patterns()

    def _load_synonyms(self) -> Dict:
        """按语言加载同义词词典"""
        if self.language == "en":
            return self._english_synonyms()
        elif self.language == "ja":
            return self._japanese_synonyms()
        elif self.language == "ko":
            return self._korean_synonyms()
        elif self.language == "fr":
            return self._french_synonyms()
        elif self.language == "de":
            return self._german_synonyms()
        elif self.language == "es":
            return self._spanish_synonyms()
        return self._chinese_synonyms()

    def _load_patterns(self) -> Dict:
        """按语言加载意图模式"""
        if self.language == "en":
            return self._english_patterns()
        elif self.language == "ja":
            return self._japanese_patterns()
        elif self.language == "ko":
            return self._korean_patterns()
        elif self.language == "fr":
            return self._french_patterns()
        elif self.language == "de":
            return self._german_patterns()
        elif self.language == "es":
            return self._spanish_patterns()
        return self._chinese_patterns()

    def _chinese_synonyms(self) -> Dict:
        """中文同义词词典"""
        return {
            "查重": ["查重", "检测", "重复率", "相似度", "抄袭率", "复制比", "比对"],
            "降重": ["降重", "降相似度", "降重复率", "改写", "重写", "润色", "去重"],
            "选题": ["选题", "选题目", "定题", "题目", "研究方向", "研究主题", "论文题目"],
            "大纲": ["大纲", "框架", "结构", "目录", "提纲", "章节安排", "组织架构"],
            "开题": ["开题", "开题报告", "研究计划", "proposal", "开题答辩", "开题论证"],
            "答辩": ["答辩", "毕业答辩", "论文答辩", "预答辩", "oral defense", "defense"],
            "文献综述": ["文献综述", "综述", "文献回顾", "研究现状", "研究进展", "文献梳理"],
            "方法": ["方法", "方法论", "研究方法", "研究设计", "技术路线", "实验设计"],
            "格式": ["格式", "排版", "样式", "模板", "版式", "版面", "字体字号"],
            "引用": ["引用", "参考文献", "文献引用", "引文", "注脚", "尾注", "夹注"],
            "AI检测": ["AI检测", "AIGC", "AI率", "人工智能检测", "机器生成检测", "GPT检测"],
            "量化": ["量化", "定量", "实证", "统计", "数据分析", "问卷调查", "SPSS"],
            "质性": ["质性", "定性", "访谈", "案例", "扎根", "民族志", "田野调查"],
        }

    def _english_synonyms(self) -> Dict:
        """英文同义词词典"""
        return {
            "plagiarism": ["plagiarism", "similarity", "duplication", "turnitin", "check", "detection"],
            "paraphrase": ["paraphrase", "rewrite", "rephrase", "reword", "revise"],
            "topic": ["topic", "title", "subject", "research question", "research direction"],
            "outline": ["outline", "framework", "structure", "table of contents", "organization"],
            "proposal": ["proposal", "research plan", "research proposal", "dissertation proposal"],
            "defense": ["defense", "oral defense", "viva", "thesis defense", "dissertation defense"],
            "literature_review": ["literature review", "review", "systematic review", "research status"],
            "methodology": ["methodology", "method", "research design", "research method"],
            "format": ["format", "formatting", "style", "template", "layout"],
            "citation": ["citation", "reference", "bibliography", "in-text citation"],
            "ai_detection": ["AI detection", "AIGC", "AI-generated", "GPT detection"],
            "quantitative": ["quantitative", "statistical", "survey", "empirical", "data analysis"],
            "qualitative": ["qualitative", "interview", "case study", "ethnography", "grounded theory"],
        }

    def _japanese_synonyms(self) -> Dict:
        """日本語同義語辞典"""
        return {
            "重複": ["重複", "盗用", "剽窃", "類似度", " plagiarism", "コピペ"],
            "削減": ["削減", "低減", "改訂", "リライト", "書き直し", "パラフレーズ"],
            "テーマ": ["テーマ", "題目", "研究課題", "研究方向", "トピック"],
            "アウトライン": ["アウトライン", "目次", "構成", "框架", "章節構成"],
            "研究計画書": ["研究計画書", "プロポーザル", "研究提案", "開題報告"],
            "答弁": ["答弁", "審査", "口頭試問", "ディフェンス", "卒業審査"],
            "文献綜述": ["文献綜述", "先行研究", "研究サーベイ", "文献レビュー"],
            "研究方法": ["研究方法", "方法論", "リサーチメソッド", "実証研究"],
            "フォーマット": ["フォーマット", "書式", "体裁", "レイアウト", "フォント"],
            "引用": ["引用", "参考文献", "出典", "文献引用", "レファレンス"],
            "AI検出": ["AI検出", "AIGC", "AI生成検出", "GPT検出"],
            "量的": ["量的", "統計", "アンケート", "データ分析", "SPSS"],
            "質的": ["質的", "インタビュー", "ケーススタディ", "フィールドワーク"],
        }

    def _korean_synonyms(self) -> Dict:
        """한국어 동의어 사전"""
        return {
            "중복": ["중복", "표절", "유사도", "도용", "plagiarism", "카피"],
            "감소": ["감소", "경감", "수정", "리라이트", "다시 쓰기", "패러프레이즈"],
            "주제": ["주제", "제목", "연구 과제", "연구 방향", "토픽"],
            "개요": ["개요", "목차", "구성", "구조", "챕터 구성"],
            "연구 계획서": ["연구 계획서", "프로포절", "연구 제안", "개제 보고서"],
            "심사": ["심사", "구두 시험", "디펜스", "졸업 심사", "논문 심사"],
            "문헌 고찰": ["문헌 고찰", "선행 연구", "연구 서베이", "문헌 리뷰"],
            "연구 방법": ["연구 방법", "방법론", "리서치 메서드", "실증 연구"],
            "포맷": ["포맷", "서식", "체裁", "레이아웃", "폰트"],
            "인용": ["인용", "참고 문헌", "출전", "문헌 인용", "레퍼런스"],
            "AI 검출": ["AI 검출", "AIGC", "AI 생성 검출", "GPT 검출"],
            "양적": ["양적", "통계", "설문", "데이터 분석", "SPSS"],
            "질적": ["질적", "인터뷰", "사례 연구", "필드워크"],
        }

    def _french_synonyms(self) -> Dict:
        """Dictionnaire de synonymes francais"""
        return {
            "plagiat": ["plagiat", "plagie", "plagié", "similarite", "duplication", "copie", "contrefacon"],
            "reduction": ["reduction", "reformulation", "paraphrase", "reecriture"],
            "sujet": ["sujet", "theme", "titre", "question de recherche", "orientation"],
            "plan": ["plan", "structure", "sommaire", "cadre", "organisation"],
            "proposition": ["proposition", "protocole", "projet de recherche", "memoire"],
            "soutenance": ["soutenance", "defense", "jury", "examen oral"],
            "revue": ["revue de litterature", "etat de l'art", "bibliographie", "recension"],
            "methode": ["methode", "methodologie", "approche", "technique"],
            "format": ["format", "mise en page", "typographie", "style", "presentation"],
            "citation": ["citation", "reference", "bibliographie", "note de bas de page"],
            "detection_ia": ["detection IA", "AIGC", "IA detection", "GPT detection"],
            "quantitatif": ["quantitatif", "statistique", "enquete", "analyse de donnees", "SPSS"],
            "qualitatif": ["qualitatif", "entretien", "etude de cas", "terrain"],
        }

    def _german_synonyms(self) -> Dict:
        """Deutsches Synonymwoerterbuch"""
        return {
            "plagiat": ["plagiat", "plagiatsvorwurf", "ahnlichkeit", "duplikation", "kopie"],
            "reduktion": ["reduktion", "umformulierung", "paraphrase", "umschreibung"],
            "thema": ["thema", "titel", "forschungsfrage", "ausrichtung"],
            "gliederung": ["gliederung", "struktur", "inhalt", "aufbau", "organisation"],
            "expose": ["expose", "forschungsvorschlag", "projektbeschreibung"],
            "verteidigung": ["verteidigung", "kolloquium", "prufung", "disputation"],
            "literatur": ["literaturubersicht", "literaturrecherche", "bibliographie", "recherche"],
            "methode": ["methode", "methodik", "methodologie", "vorgehensweise"],
            "format": ["format", "layout", "typografie", "gestaltung"],
            "zitation": ["zitation", "zitat", "literaturangabe", "quellenangabe"],
            "ki_erkennung": ["KI-erkennung", "AIGC", "KI-erzeugt", "GPT-erkennung"],
            "quantitativ": ["quantitativ", "statistik", "befragung", "datenanalyse", "SPSS"],
            "qualitativ": ["qualitativ", "interview", "fallstudie", "empirie"],
        }

    def _spanish_synonyms(self) -> Dict:
        """Diccionario de sinonimos en espanol"""
        return {
            "plagio": ["plagio", "similitud", "duplicacion", "copia"],
            "reduccion": ["reduccion", "reformulacion", "parrafaseo", "reescripcion"],
            "tema": ["tema", "titulo", "topico", "orientacion", "pregunta de investigacion"],
            "esquema": ["esquema", "estructura", "indice", "esquema de contenidos", "organizacion"],
            "propuesta": ["propuesta", "anteproyecto", "proyecto de investigacion", "protocolo"],
            "defensa": ["defensa", "sustentacion", "tribunal", "examen oral"],
            "revision": ["revision bibliografica", "estado del arte", "recurso bibliografico"],
            "metodo": ["metodo", "metodologia", "enfoque", "tecnica"],
            "formato": ["formato", "diseno", "maquetacion", "estilo"],
            "citacion": ["citacion", "referencia", "cita", "fuente"],
            "deteccion_ia": ["deteccion IA", "AIGC", "generado por IA", "deteccion GPT"],
            "cuantitativo": ["cuantitativo", "estadistica", "encuesta", "analisis de datos", "SPSS"],
            "cualitativo": ["cualitativo", "entrevista", "estudio de caso", "investigacion de campo"],
        }

    def _chinese_patterns(self) -> Dict:
        """中文意图模式"""
        return {
            "greeting": [
                r"^(你好|在吗|在么|哈喽|嗨|hello|hi|hey|您好|打扰了)",
                r"^(早上好|下午好|晚上好)",
                r"^(有人吗|在不在|在?|在\?)",
                r"^(谢谢|感谢|多谢|谢了)",
                r"^(再见|拜拜|bye|goodbye)",
            ],
            "topic_help": [
                r"(选题|题目|选什么|写什么|不知道写什么|没方向|没想法|选题.*怎么|怎么.*选题)",
                r"(专业.*论文|论文.*选题|毕业论文.*选|本科.*选题|硕士.*选题)",
                r"(导师.*选题|选题.*导师|自己选题|推荐.*题目|题目.*推荐)",
            ],
            "outline_help": [
                r"(大纲|框架|结构|怎么写|从哪开始|目录|提纲|章节.*安排|论文.*结构)",
                r"(大纲.*怎么|怎么.*大纲|搭.*框架|建.*结构)",
            ],
            "chapter_review": [
                r"(帮我看|看看|审查|检查|批注|评价|分析|点评|审阅)",
                r"(这段|这一段|写的|写得|怎么样|如何|行不行|可以吗)",
                r"(导师.*说|导师.*改|导师.*不行|导师.*反馈|导师.*让|根据.*导师)",
                r"(修改.*建议|怎么.*改|如何.*改|哪里.*问题|什么.*问题)",
            ],
            "proposal_help": [
                r"(开题|开题.*报告|研究计划|proposal|开题.*怎么|怎么.*开题)",
                r"(研究背景|研究意义|国内外.*现状|文献综述|技术路线)",
            ],
            "format_question": [
                r"(格式|排版|字体|字号|页眉|页脚|页码|模板|样式|间距|行距)",
                r"(引用.*格式|参考文献|GB/T|7714|APA|MLA|脚注|尾注|引用.*规范)",
                r"(摘要.*字数|关键词|图表|编号|公式|目录|页边距)",
                r"(公式.*编号|图表.*标题|三线表|页眉.*页脚|页边距|行距|段前段后)",
                r"(Word.*排版|LaTeX.*排版|排版.*工具|格式.*调整|格式.*转换)",
                r"(标题.*格式|正文.*格式|注释.*格式|附录.*格式|封面.*格式)",
                r"(学校.*格式|学院.*格式|模板.*下载|格式.*要求|格式.*规范)",
            ],
            "citation_question": [
                r"(引用|参考文献|文献.*格式|怎么引|如何引|引用.*规范|引用.*标准)",
                r"(文献.*管理|zotero|endnote|noteexpress|文献.*工具)",
            ],
            "methodology": [
                r"(方法|方法论|问卷|访谈|SPSS|实证|量化|质性|定性|定量|混合.*研究)",
                r"(信度|效度|Cronbach|KMO|因子|回归|中介|调节|相关.*分析|方差)",
                r"(样本|抽样|数据.*分析|统计|描述性|推断性|假设.*检验)",
                r"(问卷.*设计|访谈.*提纲|案例.*研究|扎根|理论|主题.*分析|编码)",
                r"(实验设计|抽样方法|样本量|功效分析|G\*Power|效应量|统计功效)",
                r"(数据.*收集|数据.*分析|数据.*处理|统计.*方法|统计.*分析|描述.*统计|推断.*统计)",
                r"(研究.*设计|研究.*方案|技术路线|实验.*方案|调查.*方案|田野.*调查)",
                r"(信度.*分析|效度.*分析|因子.*分析|聚类.*分析|判别.*分析|路径.*分析)",
                r"(t检验|方差分析|ANOVA|卡方检验|相关.*分析|回归.*分析|逻辑.*回归)",
                r"(质性.*分析|编码|主题.*分析|内容.*分析|话语.*分析|叙事.*分析)",
                r"(混合.*方法|三角.*验证|多方法|多阶段| sequential|convergent)",
                r"(研究.*范式|实证主义|建构主义|解释主义|批判.*理论|后实证主义)",
                r"(变量.*定义|操作化|概念化|测量.*工具|量表|问卷.*设计|访谈.*提纲)",
                r"(效度.*威胁|内部.*效度|外部.*效度|构念.*效度|统计.*结论.*效度)",
                r"(伦理.*审查|知情.*同意|隐私.*保护|匿名.*处理|数据.*安全)",
            ],
            "defense_prep": [
                r"(答辩|预答辩|PPT|自述|答辩.*准备|紧张|答辩.*技巧|答辩.*问题)",
                r"(评委|委员会|提问|高频问题|怎么答|回答.*策略|答辩.*稿)",
                r"(答辩.*PPT|PPT.*怎么做|幻灯片|汇报|演讲|陈述)",
                r"(答辩.*流程|答辩.*环节|答辩.*顺序|答辩.*时间|答辩.*礼仪|答辩.*着装)",
                r"(答辩.*心态|紧张.*怎么办|答辩.*紧张|克服.*紧张|自信.*表达)",
                r"(答辩.*材料|答辩.*准备|答辩.*清单|答辩.*检查|答辩.*模拟)",
                r"(答辩.*问题|常见问题|高频.*问题|可能.*问题|问题.*预测|问题.*准备)",
                r"(回答.*技巧|回答.*策略|回答.*原则|回答.*方法|回答.*框架|回答.*模板)",
                r"(答辩.*陈述|陈述.*技巧|陈述.*结构|陈述.*时间|陈述.*重点|陈述.*逻辑)",
                r"(答辩.*PPT|PPT.*设计|PPT.*制作|PPT.*模板|PPT.*技巧|PPT.*注意)",
                r"(答辩.*礼仪|着装.*要求|仪态.*举止|眼神.*交流|语言.*表达|时间.*控制)",
                r"(答辩.*结果|通过|不通过|修改|重大.*修改|轻微.*修改|延期.*答辩)",
                r"(答辩.*后|修改.*提交|最终.*提交|论文.*归档|学位.*申请|毕业.*流程)",
                r"(线上.*答辩|视频.*答辩|远程.*答辩|网络.*答辩|答辩.*形式|答辩.*方式)",
                r"(答辩.*委员|评委.*提问|专家.*提问|导师.*提问|同行.*提问|质疑.*回应)",
            ],
            "plagiarism": [
                r"(查重|降重|重复率|相似度|plagiarism|抄袭|AI.*检测|AI率|aigc)",
                r"(知网|维普|格子达|paper.*pass|turnitin|查重.*系统)",
                r"(怎么.*降|如何.*降|降.*方法|改写|重写|同义.*替换)",
            ],
            "literature_review": [
                r"(文献综述|综述.*怎么|怎么.*综述|文献.*整理|文献.*阅读|文献.*笔记)",
                r"(述评|研究.*现状|研究.*进展|研究.*趋势|文献.*梳理)",
                r"(研究.*缺口|研究.*不足|研究.*空白|未来.*方向|研究.*展望)",
                r"(文献.*检索|文献.*搜索|数据库|知网|Web.*of.*Science|Google.*Scholar|Scopus)",
                r"(文献.*管理|Zotero|EndNote|NoteExpress|Mendeley|Citavi|文献.*工具)",
                r"(文献.*筛选|文献.*评价|文献.*质量|文献.*分类|文献.*组织)",
                r"(综述.*结构|综述.*框架|综述.*写法|综述.*模板|综述.*示例)",
                r"(批判性.*综述|系统性.*综述|Meta.*分析|文献.*计量|综述.*方法)",
                r"(引用.*太多|引用.*太少|引用.*格式|引用.*规范|引用.*技巧)",
                r"(文献.*综述.*写作|如何.*写.*综述|综述.*技巧|综述.*要点|综述.*注意事项)",
            ],
            "writing_guide": [
                r"(怎么.*写|如何.*写|写作.*技巧|写作.*方法|学术.*写作|论文.*写作)",
                r"(摘要.*写|结论.*写|引言.*写|讨论.*写|结果.*写|方法.*写)",
                r"(学术.*用语|学术.*表达|规范.*表达|专业.*术语|措辞|用语)",
                r"(段落.*结构|段落.*写作|主题.*句|过渡.*句|结论.*句|PEEL|MEAL)",
                r"(逻辑.*连接|逻辑.*过渡|连接.*词|转折.*词|因果.*词|并列.*词)",
                r"(学术.*风格|写作.*风格|正式.*写作|客观.*写作|第三.*人称|被动.*语态)",
                r"(避免.*口语|避免.*主观|避免.*绝对|避免.*模糊|精确.*表达|清晰.*表达)",
                r"(图表.*制作|图表.*设计|数据.*可视化|三线表|流程图|框架图|示意图)",
                r"(公式.*编辑|公式.*排版|数学.*公式|化学.*公式|LaTeX.*公式|MathType)",
                r"(标题.*拟定|标题.*层次|章节.*标题|小节.*标题|标题.*编号|标题.*格式)",
                r"(摘要.*要素|摘要.*结构|摘要.*字数|关键词.*选择|关键词.*数量)",
                r"(引言.*要素|引言.*结构|研究.*背景|问题.*提出|研究.*目的|研究.*意义)",
                r"(讨论.*要素|讨论.*结构|结果.*解释|结果.*比较|局限.*讨论|未来.*研究)",
                r"(结论.*要素|结论.*结构|主要.*发现|理论.*贡献|实践.*启示|研究.*局限)",
                r"(致谢.*写作|致谢.*要素|致谢.*对象|致谢.*语气|致谢.*长度|致谢.*禁忌)",
            ],
            "toolchain": [
                r"(工具|软件|推荐|用什么|工具.*链|写作.*工具|效率.*工具)",
                r"(word|latex|overleaf|markdown|notion|obsidian|语雀|飞书)",
                r"(时间.*规划|进度.*安排|计划|时间表|甘特图|倒排|时间.*管理)",
                r"(文献.*管理|Zotero|EndNote|Mendeley|NoteExpress|Citavi|文献.*工具)",
                r"(数据分析.*工具|统计.*软件|SPSS|R|Python|Stata|SAS|MATLAB|JMP)",
                r"(质性.*分析|NVivo|Atlas\.ti|MAXQDA|Dedoose|QDA.*Miner|质性.*工具)",
                r"(绘图.*工具|画图.*软件|Visio|ProcessOn|Draw\.io|亿图|思维导图)",
                r"(公式.*编辑|MathType|LaTeX|MathJax|公式.*工具|公式.*编辑器)",
                r"(翻译.*工具|DeepL|Google.*Translate|有道.*翻译|翻译.*软件|机器.*翻译)",
                r"(润色.*工具|Grammarly|QuillBot|Writefull|LanguageTool|写作.*辅助)",
                r"(查重.*工具|知网|维普|万方|Turnitin|PaperPass|查重.*软件)",
                r"(AI.*写作|ChatGPT|Claude|DeepSeek|文心一言|通义千问|AI.*辅助)",
                r"(协作.*工具|腾讯.*文档|石墨.*文档|飞书.*文档|在线.*协作|共享.*编辑)",
                r"(备份.*工具|云.*存储|百度.*网盘|OneDrive|Google.*Drive|坚果.*云|同步.*盘)",
                r"(版本.*控制|Git|GitHub|GitLab|SVN|版本.*管理|代码.*管理)",
                r"(笔记.*工具|Evernote|OneNote|Notion|Obsidian|Roam|Logseq|笔记.*软件)",
                r"(PDF.*工具|PDF.*阅读|PDF.*编辑|PDF.*转换|Adobe|福昕|PDF.*处理)",
                r"(浏览器.*插件|Chrome.*插件|Edge.*插件|学术.*插件|科研.*插件|效率.*插件)",
                r"(时间管理|番茄.*工作|Forest|Focus|ToDo|任务.*管理|日程.*管理|提醒.*工具)",
                r"(思维导图|XMind|MindManager|MindMeister|幕布|思维.*工具|脑图)",
                r"(演示.*工具|PPT|PowerPoint|Keynote|Prezi|Canva|幻灯片|演示.*软件)",
                r"(录音.*转文字|讯飞|搜狗.*录音|语音.*转写|转录.*工具|语音.*识别)",
                r"(屏幕.*录制|录屏.*软件|Camtasia|OBS|Bandicam|屏幕.*录像|视频.*录制)",
                r"(远程.*会议|腾讯.*会议|Zoom|Teams|钉钉|飞书.*会议|在线.*会议|视频.*会议)",
                r"(代码.*编辑|IDE|VSCode|PyCharm|RStudio|Jupyter|Spyder|编程.*环境)",
            ],
            "checklist": [
                r"(检查|核对|清单|自检|自查|提交.*前|最后.*检查|完整.*性|遗漏)",
                r"(格式.*检查|引用.*检查|逻辑.*检查|语法.*检查|错别字|标点)",
                r"(标题.*检查|目录.*检查|页码.*检查|图表.*检查|公式.*检查|参考文献.*检查)",
                r"(内容.*检查|结构.*检查|逻辑.*检查|一致性.*检查|准确性.*检查|完整性.*检查)",
                r"(语言.*检查|表达.*检查|术语.*检查|符号.*检查|单位.*检查|数据.*检查)",
                r"(排版.*检查|字体.*检查|字号.*检查|行距.*检查|页边距.*检查|对齐.*检查)",
                r"(摘要.*检查|关键词.*检查|引言.*检查|结论.*检查|致谢.*检查|附录.*检查)",
                r"(学术.*规范|写作.*规范|引用.*规范|格式.*规范|学校.*要求|学院.*要求)",
                r"(提交.*材料|提交.*清单|材料.*清单|文件.*清单|提交.*要求|提交.*规范)",
                r"(答辩.*准备|答辩.*检查|PPT.*检查|自述.*检查|材料.*准备|着装.*准备)",
                r"(论文.*质量|质量.*检查|质量.*评估|质量.*标准|优秀.*论文|论文.*评分)",
                r"(导师.*意见|导师.*反馈|导师.*修改|导师.*建议|导师.*要求|导师.*检查)",
                r"(盲审.*准备|盲审.*检查|外审.*准备|外审.*检查|评审.*意见|评审.*修改)",
                r"(最终.*检查|最后.*修改|定稿.*检查|定稿.*确认|提交.*确认|打印.*检查)",
                r"(备份.*检查|版本.*管理|文件.*备份|云.*备份|多.*版本|历史.*版本)",
            ],
            "config": [
                r"(配置|设置|api.*key|apikey|deepseek|key|密钥|令牌|token)",
                r"(帮助|help|说明|文档|怎么用|使用.*指南|教程|新手)",
                r"(功能.*介绍|系统.*介绍|能力.*说明|支持.*功能|使用.*说明)",
                r"(价格|费用|收费|免费|付费|订阅|会员|套餐|额度|限制)",
                r"(隐私.*政策|数据.*安全|信息.*保护|数据.*使用|数据.*存储|数据.*删除)",
                r"(反馈|建议|投诉|问题.*反馈|功能.*建议|改进.*建议|bug.*报告)",
                r"(更新|版本|升级|新.*功能|更新.*日志|版本.*说明|版本.*历史)",
                r"(联系|客服|支持|帮助.*中心|技术.*支持|用户.*支持|社区|论坛)",
                r"(账号|注册|登录|注销|密码|重置|找回|绑定|解绑|关联)",
                r"(语言|中文|英文|多语言|翻译|界面.*语言|显示.*语言)",
                r"(主题|界面|外观|深色.*模式|浅色.*模式|夜间.*模式|护眼.*模式)",
                r"(通知|提醒|推送|邮件.*通知|短信.*通知|微信.*通知|声音.*提醒)",
                r"(导出|导入|备份|恢复|迁移|同步|云.*同步|本地.*备份)",
                r"(快捷键|热键|快捷.*操作|效率.*操作|操作.*技巧|使用.*技巧)",
                r"(故障|错误|异常|崩溃|卡顿|加载.*慢|无法.*访问|连接.*失败)",
            ],
        }

    def _english_patterns(self) -> Dict:
        """英文意图模式"""
        return {
            "greeting": [
                r"^(hello|hi|hey|good morning|good afternoon|good evening)",
                r"^(thanks|thank you|bye|goodbye|see you)",
            ],
            "topic_help": [
                r"(topic|title|choose|select|what to write|research direction|research question)",
                r"(thesis topic|dissertation topic|pick a topic|find a topic)",
                r"(suggest.*topic|recommend.*topic|help.*topic)",
            ],
            "outline_help": [
                r"(outline|framework|structure|how to write|where to start|table of contents)",
                r"(outline.*help|help.*outline|create.*outline|build.*structure)",
            ],
            "chapter_review": [
                r"(check|review|examine|analyze|evaluate|critique|assess)",
                r"(this paragraph|this section|how.*write|is it good|look at)",
                r"(advisor.*said|advisor.*feedback|supervisor.*comment|mentor.*suggest)",
                r"(revision.*suggest|how.*improve|what.*wrong|what.*problem)",
            ],
            "proposal_help": [
                r"(proposal|research.*plan|dissertation.*proposal|how.*proposal)",
                r"(background|significance|literature review|methodology|research design)",
            ],
            "format_question": [
                r"(format|formatting|font|size|header|footer|page number|template|style|spacing)",
                r"(citation.*format|reference|APA|MLA|IEEE|Chicago|footnote|endnote)",
                r"(abstract.*length|keyword|figure|table|numbering|equation|margin)",
                r"(Word.*format|LaTeX.*format|formatting.*tool|format.*guide)",
            ],
            "citation_question": [
                r"(citation|reference|bibliography|how.*cite|cite.*format|citation.*style)",
                r"(reference.*manager|zotero|endnote|mendeley|citation.*tool)",
            ],
            "methodology": [
                r"(method|methodology|survey|interview|SPSS|empirical|quantitative|qualitative|mixed.*method)",
                r"(reliability|validity|Cronbach|KMO|factor|regression|mediation|moderation|correlation)",
                r"(sample|sampling|data.*analysis|statistic|descriptive|inferential|hypothesis.*test)",
                r"(survey.*design|interview.*guide|case.*study|grounded.*theory|thematic.*analysis)",
                r"(experimental.*design|sampling.*method|sample.*size|power.*analysis|effect.*size)",
                r"(data.*collection|data.*processing|statistical.*method|statistical.*analysis)",
                r"(research.*design|research.*proposal|technical.*route|experiment.*plan)",
                r"(reliability.*analysis|validity.*analysis|factor.*analysis|cluster.*analysis)",
                r"(t-test|ANOVA|chi-square|correlation.*analysis|regression.*analysis|logistic.*regression)",
                r"(qualitative.*analysis|coding|thematic.*analysis|content.*analysis|discourse.*analysis)",
                r"(mixed.*method|triangulation|multi-method|sequential|convergent)",
                r"(research.*paradigm|positivism|constructivism|interpretivism|critical.*theory)",
                r"(variable.*definition|operationalization|conceptualization|measurement.*tool|scale)",
                r"(validity.*threat|internal.*validity|external.*validity|construct.*validity)",
                r"(ethics.*review|informed.*consent|privacy.*protection|anonymity|data.*security)",
            ],
            "defense_prep": [
                r"(defense|oral defense|viva|presentation|slide|preparation|nervous)",
                r"(committee|question|frequently.*asked|how.*answer|answer.*strategy)",
                r"(defense.*PPT|PPT.*design|slide.*design|presentation.*skill)",
                r"(defense.*process|defense.*procedure|defense.*order|defense.*time)",
                r"(defense.*anxiety|nervous.*how|overcome.*nervous|confidence.*expression)",
                r"(defense.*material|defense.*checklist|defense.*preparation|defense.*simulation)",
                r"(defense.*question|common.*question|frequent.*question|predict.*question)",
                r"(answer.*technique|answer.*strategy|answer.*principle|answer.*framework)",
                r"(defense.*statement|statement.*skill|statement.*structure|statement.*time)",
            ],
            "plagiarism": [
                r"(plagiarism|similarity|duplication|turnitin|check|detection)",
                r"(how.*reduce|how.*lower|paraphrase|rewrite|rephrase)",
            ],
            "literature_review": [
                r"(literature.*review|how.*review|review.*how|literature.*manage|literature.*read)",
                r"(research.*status|research.*progress|research.*trend|literature.*organize)",
                r"(research.*gap|research.*limitation|future.*direction|research.*outlook)",
                r"(literature.*search|literature.*retrieve|database|Web.*of.*Science|Google.*Scholar|Scopus)",
                r"(reference.*manager|Zotero|EndNote|Mendeley|citation.*tool)",
                r"(literature.*screen|literature.*evaluate|literature.*quality|literature.*classify)",
                r"(review.*structure|review.*framework|review.*method|review.*template)",
                r"(critical.*review|systematic.*review|Meta.*analysis|bibliometric)",
                r"(citation.*too.*many|citation.*too.*few|citation.*format|citation.*skill)",
            ],
            "writing_guide": [
                r"(how.*write|writing.*skill|writing.*method|academic.*writing|thesis.*writing)",
                r"(abstract.*write|conclusion.*write|introduction.*write|discussion.*write)",
                r"(academic.*language|academic.*expression|formal.*expression|professional.*term)",
                r"(paragraph.*structure|paragraph.*writing|topic.*sentence|transition.*sentence)",
                r"(logical.*connection|logical.*transition|transition.*word|conjunctive.*adverb)",
                r"(academic.*style|writing.*style|formal.*writing|objective.*writing|third.*person)",
                r"(avoid.*colloquial|avoid.*subjective|avoid.*absolute|precise.*expression)",
                r"(figure.*design|table.*design|data.*visualization|flowchart|diagram)",
                r"(equation.*edit|math.*formula|LaTeX.*formula|MathType)",
                r"(title.*design|heading.*level|section.*title|title.*numbering)",
                r"(abstract.*element|abstract.*structure|abstract.*length|keyword.*selection)",
                r"(introduction.*element|introduction.*structure|background|problem.*statement)",
                r"(discussion.*element|discussion.*structure|result.*interpretation|limitation)",
                r"(conclusion.*element|conclusion.*structure|main.*finding|theoretical.*contribution)",
                r"(acknowledgment.*writing|acknowledgment.*element|acknowledgment.*tone)",
            ],
            "toolchain": [
                r"(tool|software|recommend|what.*use|tool.*chain|writing.*tool|efficiency.*tool)",
                r"(word|latex|overleaf|markdown|notion|obsidian)",
                r"(time.*planning|schedule|timeline|gantt|time.*management)",
                r"(reference.*manager|Zotero|EndNote|Mendeley|citation.*tool)",
                r"(data.*analysis.*tool|statistical.*software|SPSS|R|Python|Stata|SAS|MATLAB)",
                r"(qualitative.*analysis|NVivo|Atlas\.ti|MAXQDA)",
                r"(drawing.*tool|diagram.*software|Visio|ProcessOn|Draw\.io|mind.*map)",
                r"(equation.*editor|MathType|LaTeX|MathJax)",
                r"(translation.*tool|DeepL|Google.*Translate|machine.*translation)",
                r"(proofreading.*tool|Grammarly|QuillBot|Writefull|LanguageTool)",
                r"(plagiarism.*check|Turnitin|PaperPass|iThenticate)",
                r"(AI.*writing|ChatGPT|Claude|DeepSeek|AI.*assistant)",
                r"(collaboration.*tool|Google.*Docs|Office.*365|shared.*document)",
                r"(backup.*tool|cloud.*storage|OneDrive|Google.*Drive|Dropbox)",
                r"(version.*control|Git|GitHub|GitLab)",
                r"(note.*tool|Evernote|OneNote|Notion|Obsidian|Roam|Logseq)",
                r"(PDF.*tool|PDF.*reader|PDF.*editor|PDF.*converter|Adobe)",
                r"(browser.*extension|Chrome.*extension|Edge.*extension)",
                r"(time.*management|Pomodoro|Forest|Focus|ToDo|task.*management)",
                r"(mind.*map|XMind|MindManager|MindMeister)",
                r"(presentation.*tool|PPT|PowerPoint|Keynote|Prezi|Canva)",
                r"(voice.*to.*text|transcription.*tool|speech.*recognition)",
                r"(screen.*record|screen.*capture|Camtasia|OBS)",
                r"(remote.*meeting|Zoom|Teams|Google.*Meet|online.*meeting)",
                r"(code.*editor|IDE|VSCode|PyCharm|RStudio|Jupyter)",
            ],
            "checklist": [
                r"(check|verify|checklist|self.*check|submit.*before|final.*check|completeness)",
                r"(format.*check|citation.*check|logic.*check|grammar.*check|typo|punctuation)",
                r"(title.*check|table.*of.*content.*check|page.*number.*check|figure.*check)",
                r"(content.*check|structure.*check|logic.*check|consistency.*check|accuracy.*check)",
                r"(language.*check|expression.*check|terminology.*check|symbol.*check)",
                r"(formatting.*check|font.*check|size.*check|spacing.*check|alignment.*check)",
                r"(abstract.*check|keyword.*check|introduction.*check|conclusion.*check)",
                r"(academic.*standard|writing.*standard|citation.*standard|format.*standard)",
                r"(submit.*material|submit.*checklist|material.*checklist|file.*checklist)",
                r"(defense.*preparation|defense.*check|PPT.*check|statement.*check)",
                r"(thesis.*quality|quality.*check|quality.*assessment|quality.*standard)",
                r"(advisor.*comment|advisor.*feedback|advisor.*revision|advisor.*requirement)",
                r"(blind.*review|external.*review|review.*comment|review.*revision)",
                r"(final.*check|final.*revision|finalize.*check|submit.*confirm)",
                r"(backup.*check|version.*management|file.*backup|cloud.*backup)",
            ],
            "config": [
                r"(config|setting|api.*key|apikey|deepseek|key|token)",
                r"(help|documentation|guide|tutorial|how.*use|user.*guide)",
                r"(feature.*introduction|system.*introduction|capability|supported.*feature)",
                r"(price|cost|fee|free|paid|subscription|premium|quota|limit)",
                r"(privacy.*policy|data.*security|information.*protection|data.*usage)",
                r"(feedback|suggestion|complaint|bug.*report|feature.*request)",
                r"(update|version|upgrade|new.*feature|changelog|release.*note)",
                r"(contact|support|help.*center|technical.*support|community|forum)",
                r"(account|register|login|logout|password|reset|recover)",
                r"(language|Chinese|English|multilingual|translation|interface.*language)",
                r"(theme|interface|appearance|dark.*mode|light.*mode|night.*mode)",
                r"(notification|reminder|push|email.*notification|sound.*reminder)",
                r"(export|import|backup|restore|migration|sync|cloud.*sync)",
                r"(shortcut|hotkey|quick.*operation|efficiency.*operation|usage.*tip)",
                r"(error|exception|crash|lag|slow.*load|connection.*fail)",
            ],
        }

    def _japanese_patterns(self) -> Dict:
        """日本語意図パターン"""
        return {
            "greeting": [
                r"^(こんにちは|おはよう|こんばんは|やあ|ハロー)",
                r"^(ありがとう|感謝|すみません|さようなら)",
                r"^(hello|hi|hey)",
            ],
            "topic_help": [
                r"(テーマ|題目|選定|何を書く|研究方向|研究課題)",
                r"(テーマ.*選|テーマ.*決|テーマ.*探|テーマ.*推薦)",
                r"(卒論.*テーマ|修士論文.*テーマ|論文.*テーマ)",
            ],
            "outline_help": [
                r"(アウトライン|目次|構成|構造|書き方|どこから)",
                r"(アウトライン.*作|フレームワーク.*構)",
            ],
            "chapter_review": [
                r"(確認|検査|チェック|レビュー|評価|分析|添削)",
                r"(この段落|この部分|どう|良いか|見て)",
                r"(指導教員.*言|指導教員.*修正|指導教員.*フィードバック)",
                r"(修正.*提案|どう.*直|どこ.*問題)",
            ],
            "proposal_help": [
                r"(研究計画書|プロポーザル|開題|研究計画)",
                r"(研究背景|研究意義|先行研究|文献綜述|技術ロードマップ)",
            ],
            "format_question": [
                r"(フォーマット|書式|体裁|フォント|サイズ|ページ番号|テンプレート)",
                r"(引用.*形式|参考文献|APA|MLA|IEEE|Chicago|脚注|章末注)",
                r"(要旨.*文字数|キーワード|図表|番号|余白|行間)",
            ],
            "citation_question": [
                r"(引用|参考文献|文献.*形式|引用.*規範|引用.*標準)",
                r"(文献.*管理|Zotero|EndNote|Mendeley)",
            ],
            "methodology": [
                r"(方法|方法論|アンケート|インタビュー|SPSS|実証|量的|質的)",
                r"(信頼性|妥当性|Cronbach|KMO|因子|回帰|相関)",
                r"(サンプル|標本|データ.*分析|統計|仮説.*検定)",
                r"(研究.*設計|技術.*路線|実験.*計画)",
            ],
            "defense_prep": [
                r"(答弁|審査|口頭試問|プレゼン|スライド|準備)",
                r"(委員|質問|よくある質問|答え方|回答.*戦略)",
                r"(答弁.*PPT|PPT.*作|スライド.*作)",
                r"(緊張|不安|克服|自信)",
            ],
            "plagiarism": [
                r"(重複|盗用|剽窃|類似度| plagiarism|検出)",
                r"(どう.*減|どう.*下|リライト|改訂|書き直し)",
                r"(Turnitin|iThenticate|知网|コピー.*チェック)",
            ],
            "literature_review": [
                r"(文献綜述|先行研究|サーベイ|文献レビュー|文献.*整理)",
                r"(研究.*現状|研究.*動向|文献.*検索)",
                r"(研究.*ギャップ|研究.*不足|今後の.*方向)",
                r"(文献.*管理|Zotero|EndNote|Mendeley)",
            ],
            "writing_guide": [
                r"(書き方|どう.*書|如何.*書|執筆.*技法|学術.*文章)",
                r"(要旨.*書|結論.*書|序論.*書|考察.*書|方法.*書)",
                r"(学術.*表現|学術.*用語|正式.*表現)",
                r"(段落.*構成|トピック.*センテンス|接続.*表現)",
            ],
            "toolchain": [
                r"(ツール|ソフト|推奨|何.*使|効率.*ツール)",
                r"(Word|LaTeX|Overleaf|Markdown|Notion)",
                r"(時間.*計画|スケジュール|ガント|時間.*管理)",
                r"(文献.*管理|Zotero|EndNote|Mendeley)",
                r"(統計.*ソフト|SPSS|R|Python|Stata)",
            ],
            "checklist": [
                r"(チェック|確認|自己.*チェック|提出.*前|最終.*確認)",
                r"(フォーマット.*チェック|引用.*チェック|論理.*チェック)",
                r"(品質.*チェック|基準.*チェック|標準.*チェック)",
            ],
            "config": [
                r"(設定|config|api.*key|apikey|deepseek|key|token)",
                r"(ヘルプ|ドキュメント|ガイド|チュートリアル)",
                r"(言語|Japanese|English|多言語|翻訳)",
            ],
        }

    def _korean_patterns(self) -> Dict:
        """한국어 의도 패턴"""
        return {
            "greeting": [
                r"^(안녕하세요|안녕|좋은 아침|좋은 오후|좋은 저녁)",
                r"^(감사합니다|고마워|미안합니다|안녕히 가세요)",
                r"^(hello|hi|hey)",
            ],
            "topic_help": [
                r"(주제|제목|선정|무엇을 쓸|연구 방향|연구 과제)",
                r"(주제.*선|주제.*결|주제.*탐|주제.*추천)",
                r"(졸업.*주제|석사.*주제|논문.*주제)",
            ],
            "outline_help": [
                r"(개요|목차|구성|구조|작성법|어디서부터)",
                r"(개요.*작|프레임워크.*구)",
            ],
            "chapter_review": [
                r"(확인|검사|체크|리뷰|평가|분석|첨삭)",
                r"(이 단락|이 부분|어때|좋은지|봐줘)",
                r"(지도교수.*말|지도교수.*수정|지도교수.*피드백)",
                r"(수정.*제안|어떻게.*고칠|어디.*문제)",
            ],
            "proposal_help": [
                r"(연구 계획서|프로포절|개제|연구 계획)",
                r"(연구 배경|연구 의의|선행 연구|문헌 고찰|기술 로드맵)",
            ],
            "format_question": [
                r"(포맷|서식|체裁|폰트|크기|페이지 번호|템플릿)",
                r"(인용.*형식|참고 문헌|APA|MLA|IEEE|Chicago|각주|미주)",
                r"(요약.*글자수|키워드|도표|번호|여백|행간)",
            ],
            "citation_question": [
                r"(인용|참고 문헌|문헌.*형식|인용.*규범|인용.*표준)",
                r"(문헌.*관리|Zotero|EndNote|Mendeley)",
            ],
            "methodology": [
                r"(방법|방법론|설문|인터뷰|SPSS|실증|양적|질적)",
                r"(신뢰도|타당도|Cronbach|KMO|요인|회귀|상관)",
                r"(표본|샘플|데이터.*분석|통계|가설.*검정)",
                r"(연구.*설계|기술.*노선|실험.*계획)",
            ],
            "defense_prep": [
                r"(심사|구두 시험|발표|슬라이드|준비)",
                r"(위원|질문|자주 나오는 질문|답변.*전략)",
                r"(심사.*PPT|PPT.*제작|슬라이드.*제작)",
                r"(긴장|불안|극복|자신감)",
            ],
            "plagiarism": [
                r"(중복|도용|표절|유사도|plagiarism|검출)",
                r"(어떻게.*줄|어떻게.*내|리라이트|수정|다시 쓰기)",
                r"(Turnitin|iThenticate|카피.*체크)",
            ],
            "literature_review": [
                r"(문헌 고찰|선행 연구|서베이|문헌 리뷰|문헌.*정리)",
                r"(연구.*현황|연구.*동향|문헌.*검색)",
                r"(연구.*갭|연구.*부족|향후.*방향)",
                r"(문헌.*관리|Zotero|EndNote|Mendeley)",
            ],
            "writing_guide": [
                r"(작성법|어떻게.*쓸|어떻게.*짓|집필.*기법|학술.*문장)",
                r"(요약.*쓰기|결론.*쓰기|서론.*쓰기|고찰.*쓰기|방법.*쓰기)",
                r"(학술.*표현|학술.*용어|격식체.*표현)",
                r"(단락.*구성|토픽.*센텐스|연결.*표현)",
            ],
            "toolchain": [
                r"(도구|소프트웨어|추천|무엇.*사용|효율.*도구)",
                r"(Word|LaTeX|Overleaf|Markdown|Notion)",
                r"(시간.*계획|스케줄|간트|시간.*관리)",
                r"(문헌.*관리|Zotero|EndNote|Mendeley)",
                r"(통계.*소프트웨어|SPSS|R|Python|Stata)",
            ],
            "checklist": [
                r"(체크|확인|자기.*체크|제출.*전|최종.*확인)",
                r"(포맷.*체크|인용.*체크|논리.*체크)",
                r"(품질.*체크|기준.*체크|표준.*체크)",
            ],
            "config": [
                r"(설정|config|api.*key|apikey|deepseek|key|token)",
                r"(도움말|문서|가이드|튜토리얼)",
                r"(언어|Korean|English|다국어|번역)",
            ],
        }

    def _french_patterns(self) -> Dict:
        """Modeles d'intention francais"""
        return {
            "greeting": [
                r"^(bonjour|bonsoir|salut|hello|hi|hey)",
                r"^(merci|au revoir|a bientot)",
            ],
            "topic_help": [
                r"(sujet|theme|titre|choisir|selectionner|orientation|question de recherche)",
                r"(sujet.*these|sujet.*memoire|trouver.*sujet)",
            ],
            "outline_help": [
                r"(plan|structure|sommaire|cadre|organisation|comment ecrire)",
                r"(plan.*aide|aide.*plan|creer.*structure)",
            ],
            "chapter_review": [
                r"(verifier|examiner|analyser|evaluer|critiquer|corriger)",
                r"(ce paragraphe|cette section|comment.*ecrit|est-ce bien)",
                r"(directeur.*dit|directeur.*correction|encadrant.*commentaire)",
                r"(revision.*suggestion|comment.*ameliorer|quel.*probleme)",
            ],
            "proposal_help": [
                r"(proposition|protocole|projet.*recherche|memoire|comment.*proposition)",
                r"(contexte|problematique|revue.*litterature|plan.*travail)",
            ],
            "format_question": [
                r"(format|mise.*page|police|taille|en-tete|pied.*page|numero|template|style)",
                r"(citation.*format|reference|APA|MLA|IEEE|Chicago|note.*bas.*page)",
                r"(resume.*mots|mot.*cle|figure|tableau|marge|interligne)",
            ],
            "citation_question": [
                r"(citation|reference|bibliographie|comment.*citer|norme.*citation)",
                r"(gestion.*bibliographique|Zotero|EndNote|Mendeley)",
            ],
            "methodology": [
                r"(methode|methodologie|enquete|entretien|SPSS|empirique|quantitatif|qualitatif)",
                r"(fiabilite|validite|Cronbach|KMO|facteur|regression|correlation)",
                r"(echantillon|analyse.*donnees|statistique|hypothese.*test)",
                r"(conception.*recherche|feuille.*route|plan.*experience)",
            ],
            "defense_prep": [
                r"(soutenance|defense|jury|presentation|diapositive|preparation)",
                r"(commission|question|frequemment.*pose|reponse.*strategie)",
                r"(soutenance.*PPT|PPT.*conception|diapositive.*creation)",
                r"(stress|anxiete|surmonter|confiance)",
            ],
            "plagiarism": [
                r"(plagiat|similarite|duplication|turnitin|verification|detection)",
                r"(comment.*reduire|comment.*diminuer|reformulation|reecriture)",
                r"(Turnitin|iThenticate|verification.*anti.*plagiat)",
            ],
            "literature_review": [
                r"(revue.*litterature|comment.*revue|etat.*art|bibliographie|gestion.*biblio)",
                r"(recherche.*etat|tendance.*recherche|recherche.*documentaire)",
                r"(lacune.*recherche|limite.*recherche|future.*direction)",
                r"(gestion.*bibliographique|Zotero|EndNote|Mendeley)",
            ],
            "writing_guide": [
                r"(comment.*ecrire|technique.*redaction|redaction.*academique|ecriture.*scientifique)",
                r"(resume.*ecrire|conclusion.*ecrire|introduction.*ecrire|discussion.*ecrire)",
                r"(langage.*academique|expression.*academique|style.*formel)",
                r"(structure.*paragraphe|phrase.*thematique|transition)",
            ],
            "toolchain": [
                r"(outil|logiciel|recommander|quoi.*utiliser|outil.*productivite)",
                r"(Word|LaTeX|Overleaf|Markdown|Notion)",
                r"(planification|planning|chronogramme|gestion.*temps)",
                r"(gestion.*bibliographique|Zotero|EndNote|Mendeley)",
                r"(logiciel.*statistique|SPSS|\bR\b|Python|Stata)",
            ],
            "checklist": [
                r"(verification|controle|auto.*verification|avant.*soumission|verification.*finale)",
                r"(verification.*format|verification.*citation|verification.*logique)",
                r"(verification.*qualite|norme.*verification)",
            ],
            "config": [
                r"(parametre|config|api.*key|apikey|deepseek|key|token)",
                r"(aide|documentation|guide|tutoriel)",
                r"(langue|French|English|multilingue|traduction)",
            ],
        }

    def _german_patterns(self) -> Dict:
        """Deutsche Absichtsmuster"""
        return {
            "greeting": [
                r"^(hallo|guten tag|guten morgen|guten abend|hi|hey)",
                r"^(danke|auf wiedersehen|tschuss)",
            ],
            "topic_help": [
                r"(thema|titel|themenauswahl|forschungsfrage|was.*schreiben|richtung)",
                r"(thema.*these|thema.*arbeit|thema.*finden)",
            ],
            "outline_help": [
                r"(gliederung|struktur|inhalt|aufbau|wie.*schreiben)",
                r"(gliederung.*hilfe|aufbau.*erstellen)",
            ],
            "chapter_review": [
                r"(prufen|uberprufen|bewerten|analysieren|korrigieren)",
                r"(dieser absatz|dieser teil|wie.*geschrieben|ist.*gut)",
                r"(betreuer.*sagt|betreuer.*korrektur|betreuer.*feedback)",
                r"(uberarbeitung.*vorschlag|wie.*verbessern|wo.*problem)",
            ],
            "proposal_help": [
                r"(expose|forschungsvorschlag|projektbeschreibung|exposee)",
                r"(hintergrund|problemstellung|literaturubersicht)",
            ],
            "format_question": [
                r"(format|layout|schrift|grosse|seitennummer|vorlage|gestaltung)",
                r"(zitationsformat|literaturangabe|APA|MLA|IEEE|Chicago|fussnote)",
                r"(zusammenfassung.*worter|schlusselwort|abbildung|tabelle|\brand\b|zeilenabstand)",
            ],
            "citation_question": [
                r"(zitation|zitat|literaturangabe|wie.*zitieren|zitationsnorm)",
                r"(literaturverwaltung|Zotero|EndNote|Mendeley)",
            ],
            "methodology": [
                r"(methode|methodik|methodologie|befragung|interview|SPSS|empirisch|quantitativ|qualitativ)",
                r"(reliabilitat|validitat|Cronbach|KMO|faktor|regression|korrelation)",
                r"(stichprobe|datenanalyse|statistik|hypothesenprufung)",
                r"(forschungsdesign|methodische.*roadmap|versuchsplan)",
            ],
            "defense_prep": [
                r"(verteidigung|kolloquium|disputation|prasentation|folien|vorbereitung)",
                r"(kommission|frage|haufig.*gestellt|antwort.*strategie)",
                r"(verteidigung.*PPT|PPT.*erstellung|folien.*erstellung)",
                r"(stress|angst|uberwinden|selbstvertrauen)",
            ],
            "plagiarism": [
                r"(plagiat|ahnlichkeit|duplikation|turnitin|prufung|erkennung)",
                r"(wie.*reduzieren|wie.*vermindern|umformulierung|umschreibung)",
                r"(Turnitin|iThenticate|plagiatsprufung)",
            ],
            "literature_review": [
                r"(literaturubersicht|literaturrecherche|recherche|bibliographie)",
                r"(forschungsstand|forschungstendenz|literatursuche)",
                r"(forschungslucke|grenze.*forschung|zukunftige.*richtung)",
                r"(literaturverwaltung|Zotero|EndNote|Mendeley)",
            ],
            "writing_guide": [
                r"(wie.*schreiben|technik.*schreiben|wissenschaftlich.*schreiben)",
                r"(zusammenfassung.*schreiben|schluss.*schreiben|einleitung.*schreiben|diskussion.*schreiben)",
                r"(wissenschaftliche.*sprache|akademische.*sprache|formeller.*stil)",
                r"(absatz.*struktur|themensatz|ubergang)",
            ],
            "toolchain": [
                r"(werkzeug|software|empfehlen|was.*nutzen|werkzeug.*produktivitat)",
                r"(Word|LaTeX|Overleaf|Markdown|Notion)",
                r"(planung|zeitplan|diagramm|zeitmanagement)",
                r"(literaturverwaltung|Zotero|EndNote|Mendeley)",
                r"(statistik.*software|SPSS|\bR\b|Python|Stata)",
            ],
            "checklist": [
                r"(prufung|kontrolle|selbst.*prufung|vor.*abgabe|end.*prufung)",
                r"(prufung.*format|prufung.*zitation|prufung.*logik)",
                r"(prufung.*qualitat|norm.*prufung)",
            ],
            "config": [
                r"(einstellung|config|api.*key|apikey|deepseek|key|token)",
                r"(hilfe|dokumentation|anleitung|tutorial)",
                r"(sprache|German|English|mehrsprachig|ubersetzung)",
            ],
        }

    def _spanish_patterns(self) -> Dict:
        """Patrones de intencion en espanol"""
        return {
            "greeting": [
                r"^(hola|buenos dias|buenas tardes|buenas noches|hi|hey)",
                r"^(gracias|adios|hasta luego)",
            ],
            "topic_help": [
                r"(tema|titulo|seleccion|topico|pregunta.*investigacion|orientacion)",
                r"(tema.*tesis|tema.*trabajo|elegir.*tema|buscar.*tema)",
            ],
            "outline_help": [
                r"(esquema|estructura|indice|esquema.*contenidos|organizacion)",
                r"(esquema.*ayuda|ayuda.*esquema|crear.*estructura)",
            ],
            "chapter_review": [
                r"(revisar|examinar|analizar|evaluar|corregir)",
                r"(este parrafo|esta seccion|como.*escrito|esta bien)",
                r"(director.*dice|director.*correccion|tutor.*comentario)",
                r"(revision.*sugerencia|como.*mejorar|donde.*problema)",
            ],
            "proposal_help": [
                r"(propuesta|anteproyecto|proyecto.*investigacion|protocolo)",
                r"(antecedentes|planteamiento|revision.*bibliografica)",
            ],
            "format_question": [
                r"(formato|diseno|fuente|tamano|numeracion.*pagina|plantilla)",
                r"(formato.*citacion|referencia|APA|MLA|IEEE|Chicago|nota.*pie)",
                r"(resumen.*palabras|palabra.*clave|figura|tabla|margen|interlineado)",
            ],
            "citation_question": [
                r"(citacion|referencia|bibliografia|como.*citar|norma.*citacion)",
                r"(gestor.*bibliografico|Zotero|EndNote|Mendeley)",
            ],
            "methodology": [
                r"(metodo|metodologia|encuesta|entrevista|SPSS|empirico|cuantitativo|cualitativo)",
                r"(fiabilidad|validez|Cronbach|KMO|factor|regresion|correlacion)",
                r"(muestra|analisis.*datos|estadistica|hipotesis.*prueba)",
                r"(diseno.*investigacion|mapa.*ruta|plan.*experimento)",
            ],
            "defense_prep": [
                r"(defensa|sustentacion|tribunal|presentacion|diapositiva|preparacion)",
                r"(comision|pregunta|frecuentemente.*formulada|respuesta.*estrategia)",
                r"(defensa.*PPT|PPT.*diseno|diapositiva.*creacion)",
                r"(estres|ansiedad|superar|confianza)",
            ],
            "plagiarism": [
                r"(plagio|similitud|duplicacion|turnitin|verificacion|deteccion)",
                r"(como.*reducir|como.*disminuir|reformulacion|reescripcion)",
                r"(Turnitin|iThenticate|verificacion.*anti.*plagio)",
            ],
            "literature_review": [
                r"(revision.*bibliografica|como.*revision|estado.*arte|bibliografia)",
                r"(investigacion.*estado|tendencia.*investigacion|busqueda.*documental)",
                r"(brecha.*investigacion|limite.*investigacion|direccion.*futura)",
                r"(gestor.*bibliografico|Zotero|EndNote|Mendeley)",
            ],
            "writing_guide": [
                r"(como.*escribir|tecnica.*redaccion|redaccion.*academica|escritura.*cientifica)",
                r"(resumen.*escribir|conclusion.*escribir|introduccion.*escribir|discusion.*escribir)",
                r"(lenguaje.*academico|expresion.*academica|estilo.*formal)",
                r"(estructura.*parrafo|oracion.*tematica|transicion)",
            ],
            "toolchain": [
                r"(herramienta|software|recomendar|que.*usar|herramienta.*productividad)",
                r"(Word|LaTeX|Overleaf|Markdown|Notion)",
                r"(planificacion|cronograma|diagrama|gestion.*tiempo)",
                r"(gestor.*bibliografico|Zotero|EndNote|Mendeley)",
                r"(software.*estadistico|SPSS|\bR\b|Python|Stata)",
            ],
            "checklist": [
                r"(verificacion|control|auto.*verificacion|antes.*envio|verificacion.*final)",
                r"(verificacion.*formato|verificacion.*citacion|verificacion.*logica)",
                r"(verificacion.*calidad|norma.*verificacion)",
            ],
            "config": [
                r"(configuracion|config|api.*key|apikey|deepseek|key|token)",
                r"(ayuda|documentacion|guia|tutorial)",
                r"(idioma|Spanish|English|multilingue|traduccion)",
            ],
        }

    def classify(self, user_input: str) -> Dict:
        """分类用户意图(支持多语言和同义词扩展)"""
        text = user_input.lower().strip()

        # 扩展同义词到文本中(用于匹配)
        expanded_text = text
        for core_word, synonyms in self.synonyms.items():
            for syn in synonyms:
                if syn in text:
                    # 在文本末尾添加核心词标记，增加匹配概率
                    expanded_text += f" {core_word}"
                    break

        # 检查是否包含论文内容(长文本)
        # 中文标点或英文句号
        has_content = len(text) > 200 and (
            "\u3002" in text or "\uff0c" in text or "." in text)

        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, expanded_text, re.IGNORECASE):
                    return {
                        "type": intent_type,
                        "confidence": 0.85,
                        "matched_pattern": pattern,
                        "has_content": has_content,
                        "length": len(text)
                    }

        # 如果文本很长但没有匹配到意图，可能是论文内容
        if has_content:
            return {
                "type": "chapter_review",
                "confidence": 0.60,
                "matched_pattern": "long_text_fallback",
                "has_content": True,
                "length": len(text)
            }

        return {
            "type": "unknown",
            "confidence": 0.30,
            "matched_pattern": None,
            "has_content": has_content,
            "length": len(text)
        }


class KnowledgeBase:
    """知识库管理(按需动态加载，支持多语言和学科细分)"""

    def __init__(self, base_path: str = "./knowledge_base", language: str = "zh"):
        """
        初始化知识库

        Args:
            base_path: 知识库根目录
            language: 语言代码 (zh/en/ja/ko/de/fr)
        """
        self.base_path = Path(base_path)
        self.language = language
        self.lang_path = self.base_path / language
        self.shared_path = self.base_path / "_shared"

        # 确保语言目录存在
        if not self.lang_path.exists():
            # 回退到默认语言
            self.lang_path = self.base_path / "zh"
            if not self.lang_path.exists():
                self.lang_path = self.base_path

        self.cache = {}  # 缓存已加载的内容
        self.access_time = {}  # 记录访问时间，用于LRU淘汰
        self.max_cache_size = 20  # 最大缓存条目数

        # 加载共享配置
        self.disciplines_config = self._load_json("disciplines.json")
        self.citation_formats = self._load_json("citation_formats.json")

        self._init_default_knowledge()

    def _load_json(self, filename: str) -> Dict:
        """从 _shared 目录加载 JSON 配置文件"""
        filepath = self.shared_path / filename
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load {filename}: {e}")
        return {}

    def get_discipline_config(self, discipline_key: str) -> Dict:
        """获取学科配置信息"""
        return self.disciplines_config.get("disciplines", {}).get(discipline_key, {})

    def get_discipline_name(self, discipline_key: str) -> str:
        """获取学科名称(根据当前语言)"""
        config = self.get_discipline_config(discipline_key)
        if config:
            return config.get(f"name_{self.language}", config.get("name_zh", discipline_key))
        return discipline_key

    def get_discipline_keywords(self, discipline_key: str) -> List[str]:
        """获取学科关键词(根据当前语言)"""
        config = self.get_discipline_config(discipline_key)
        if config:
            return config.get(f"keywords_{self.language}", config.get("keywords_zh", []))
        return []

    def get_subfields(self, discipline_key: str) -> Dict:
        """获取学科细分方向"""
        config = self.get_discipline_config(discipline_key)
        return config.get("subfields", {})

    def get_citation_format(self, format_name: str = None, discipline: str = None) -> Dict:
        """获取引用格式信息"""
        formats = self.citation_formats.get("formats", {})

        if format_name:
            return formats.get(format_name, {})

        # 根据学科返回默认格式
        if discipline:
            default_by_discipline = self.citation_formats.get(
                "default_by_discipline", {})
            format_name = default_by_discipline.get(discipline, "GB/T 7714")
            return formats.get(format_name, {})

        return formats.get("GB/T 7714", {})

    def _load_file(self, path: str) -> str:
        """按需加载文件，带缓存(支持多语言路径)"""
        # 优先从语言目录加载
        lang_path = self.lang_path / path
        if lang_path.exists():
            full_path = lang_path
        else:
            # 回退到根目录
            full_path = self.base_path / path

        cache_key = f"{self.language}/{path}"

        if cache_key in self.cache:
            self.access_time[cache_key] = datetime.now()
            return self.cache[cache_key]

        if full_path.exists():
            content = full_path.read_text(encoding='utf-8')
            self.cache[cache_key] = content
            self.access_time[cache_key] = datetime.now()

            # 缓存淘汰
            if len(self.cache) > self.max_cache_size:
                self._evict_oldest()

            return content
        return ""

    def set_language(self, language: str):
        """切换语言"""
        self.language = language
        self.lang_path = self.base_path / language
        if not self.lang_path.exists():
            self.lang_path = self.base_path / "zh"
            if not self.lang_path.exists():
                self.lang_path = self.base_path
        # 清空缓存，重新加载
        self.cache.clear()
        self.access_time.clear()

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        languages = []
        if self.base_path.exists():
            for item in self.base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                    languages.append(item.name)
        return languages if languages else ['zh']

    def _evict_oldest(self):
        """LRU淘汰最旧的缓存"""
        if not self.access_time:
            return
        oldest = min(self.access_time, key=self.access_time.get)
        del self.cache[oldest]
        del self.access_time[oldest]

    def get_discipline_knowledge(self, discipline: str) -> str:
        """获取学科知识(按需加载)"""
        path = f"disciplines/{discipline}.md"
        return self._load_file(path)

    def load_subdisciplines(self) -> Dict:
        """加载学科细分配置"""
        return self._load_json("subdisciplines.json")

    def match_subdiscipline(self, text: str, discipline_key: str) -> Optional[Dict]:
        """
        匹配学科细分方向

        Args:
            text: 用户输入文本
            discipline_key: 学科键名(如 cs, economics)

        Returns:
            匹配到的细分学科信息，未匹配返回 None
        """
        subdisciplines_config = self.load_subdisciplines()
        lang_config = subdisciplines_config.get(self.language, {})
        discipline_config = lang_config.get(discipline_key, {})

        if not discipline_config:
            return None

        subdisciplines = discipline_config.get("subdisciplines", {})
        text_lower = text.lower()

        best_match = None
        best_score = 0

        for sub_key, sub_info in subdisciplines.items():
            keywords = sub_info.get("keywords", [])
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
                    matched_keywords.append(keyword)

            if score > best_score:
                best_score = score
                best_match = {
                    "key": sub_key,
                    "name": sub_info.get("name", sub_key),
                    "focus": sub_info.get("focus", []),
                    "matched_keywords": matched_keywords,
                    "score": score
                }

        return best_match if best_score > 0 else None

    def get_stage_knowledge(self, stage: str = None) -> str:
        """获取阶段知识(按需加载)

        Args:
            stage: 阶段名称(proposal/revision/writing)，为None时返回全部
        """
        # 所有阶段内容已合并到thesis_stages.md
        content = self._load_file("thesis_stages.md")
        if stage and content:
            # 按标题分割，返回对应部分
            sections = content.split("# ")
            for section in sections:
                if stage.lower() in section.lower()[:50]:  # 检查标题前50字符
                    return "# " + section
        return content

    def get_specialized_knowledge(self, topic: str) -> str:
        """获取专项知识(按需加载)

        Args:
            topic: 专题名称，支持academic_writing/research_methods/research_tools
        """
        # 专题内容已合并为3个文件
        topic_map = {
            "academic_english": "academic_writing",
            "publishing": "academic_writing",
            "literature_review": "research_tools",
            "plagiarism": "research_tools",
            "tools": "research_tools",
            "qualitative": "research_methods",
            "quantitative": "research_methods",
            "data": "research_methods",
        }
        mapped_topic = topic_map.get(topic, topic)
        path = f"{mapped_topic}.md"
        return self._load_file(path)

    def get_faq_knowledge(self, category: str = None) -> str:
        """获取FAQ知识(按需加载)

        Args:
            category: FAQ类别(common/discipline/mindset/technical)，为None时返回全部
        """
        # 所有FAQ内容已合并到faq.md
        content = self._load_file("faq.md")
        if category and content:
            # 按标题分割，返回对应部分
            sections = content.split("# ")
            for section in sections:
                if category.lower() in section.lower()[:50]:  # 检查标题前50字符
                    return "# " + section
        return content

    def _init_default_knowledge(self):
        """初始化默认知识库(硬编码，快速响应，支持多语言)"""
        if self.language == "en":
            self.default_knowledge = self._get_english_defaults()
        elif self.language == "ja":
            self.default_knowledge = self._get_japanese_defaults()
        elif self.language == "ko":
            self.default_knowledge = self._get_korean_defaults()
        elif self.language == "fr":
            self.default_knowledge = self._get_french_defaults()
        elif self.language == "de":
            self.default_knowledge = self._get_german_defaults()
        elif self.language == "es":
            self.default_knowledge = self._get_spanish_defaults()
        else:
            self.default_knowledge = self._get_chinese_defaults()

    def _get_chinese_defaults(self) -> Dict:
        """中文默认回复"""
        return {
            "greeting": """你好!我是论文写作助手，可以帮你:

论文全流程:选题 -> 开题 -> 大纲 -> 写作 -> 修改 -> 查重 -> 答辩
专项辅导:文献综述,量化/质性研究,查重降重,工具推荐
实时批注:粘贴论文段落，我帮你检查问题

直接告诉我你卡在哪个环节?""",

            "topic_help": """[选题诊断]

请告诉我:
1. 你的专业方向?(如:计算机,商科,教育...)
2. 本科还是硕士?
3. 有没有感兴趣的方向?(没有也没关系)

我会根据你的情况推荐 3-5 个选题，并评估难度和创新性.""",

            "outline_help": """[大纲构建]

请提供:
1. 论文题目(或大致方向)
2. 专业/学科
3. 学位类型(本科/硕士)

我会生成多级大纲，包含:
- 章节结构(3-4级)
- 每节写作指引
- 字数分配建议
- 逻辑关系说明""",

            "chapter_review_intro": """[章节批注]

我进行了基础检查，发现以下问题:

{issues}

提示:这是本地基础分析.如需深度逻辑分析,论证评估，建议配置 DeepSeek API Key.""",

            "proposal_help": """[开题报告]

标准结构:
1. 研究背景与意义(从具体问题切入)
2. 国内外研究现状(分类综述+述评)
3. 研究目标与内容(具体可衡量)
4. 研究方法与技术路线(方法匹配问题)
5. 预期成果与创新点(具体说明"新"在哪里)
6. 研究计划与时间安排(预留修改时间)

请告诉我你的题目，我帮你逐节展开.""",

            "format_question": """[格式规范]

常见格式要求:
- 标题:黑体，一级标题三号，二级四号，三级小四
- 正文:宋体/ Times New Roman，小四，1.5倍行距
- 引用:GB/T 7714-2015 标准
- 页边距:上下2.54cm，左右3.17cm(常见)
- 页码:底部居中或外侧

 注意:具体以学校模板为准!

需要我详细说明哪个部分?""",

            "citation_question": """[引用规范]

GB/T 7714-2015 格式示例:

期刊:
[1] 作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.

书籍:
[2] 作者. 书名[M]. 出版地: 出版者, 年: 页码.

学位论文:
[3] 作者. 题名[D]. 保存地: 保存单位, 年.

工具推荐:Zotero(免费，中文友好)

需要具体示例或工具教程?""",

            "methodology": """[研究方法]

量化研究(问卷法):
- 变量设计 -> 问卷编制 -> 预测试 -> 正式发放 -> 数据分析
- 工具:SPSS,AMOS,PROCESS
- 关键:信度(\u03b1>0.7),效度(KMO>0.7)

质性研究(访谈/案例):
- 访谈设计 -> 数据收集 -> 编码分析 -> 主题提取
- 工具:NVivo,Nvivo替代方案
- 关键:三角验证,成员检核

请告诉我你的研究方法，我提供详细指南.""",

            "defense_prep": """[答辩准备]

PPT 框架(7页):
1. 封面(题目+姓名+导师)
2. 研究背景(1.5分钟)
3. 研究目的与意义(1分钟)
4. 研究方法(1.5分钟)
5. 研究结果(2.5分钟，核心)
6. 结论与展望(1分钟)
7. 致谢(0.5分钟)

自述稿模板:
"各位老师好，我是XXX，专业是XXX.我的论文题目是[XXX]，
接下来从研究背景,研究方法,研究结果三个方面汇报..."

高频问题:
- 你的创新点是什么?
- 为什么用这个方法?
- 样本量够吗?
- 研究的局限性?

需要模拟答辩或详细模板?""",

            "plagiarism": """[查重与降重]

查重系统:
- 知网 CNKI(高校主流)
- 维普(部分高校)
- 万方,PaperPass(自查)

降重原则:
 有效:句式重构,加数据/案例,图表替代
 无效:同义替换,中译英再译回,截图

AI 检测:
- 知网 AIGC 检测(2024+)
- 维普 AI 检测
- 建议:用自己的话重写，不是同义替换

需要具体降重示例?""",

            "literature_review": """[文献综述]

四步法:
1. 搜索:知网,Web of Science,Google Scholar
2. 筛选:读标题->摘要->结论，判断相关性
3. 分类:按主题/方法/观点/时间分类
4. 述评:总结+批判+指出研究缺口

写法框架:
"已有研究主要从X个角度展开:
\u2460 ...(张三，2020)
\u2461 ...(李四，2021)
然而，现有研究在XXX方面存在不足..."

需要模板或具体示例?""",

            "writing_guide": """[学术写作]

常见错误:
 "随着互联网的发展..." ->  "在XXX领域，传统方法面临YYY挑战..."
 "我觉得..." ->  "研究表明..." / "本文认为..."
 "越来越好" ->  "从XX%提升至XX%"
 "然后...接着..." ->  "因此...此外...然而..."

段落结构:
- 每段一个中心论点
- 论点->论据->论证->结论
- 段首句概括，段尾句过渡

需要具体修改示例?""",

            "toolchain": """[工具推荐]

文献管理:
- Zotero(免费，中文友好，推荐)
- EndNote(学校可能有授权)

写作工具:
- Word + Zotero(文科/商科)
- LaTeX/Overleaf(理工科公式)

数据分析:
- SPSS(基础统计)
- Python/R(高级分析)
- Stata(经济学)

时间管理:
- 甘特图(Excel/Project)
- 番茄工作法(25+5)
- 倒推法(从答辩日倒排)

需要具体教程?""",

            "checklist": """[提交前自检]

格式检查:
\u25a1 标题层级规范(章/节/小节)
\u25a1 字体字号统一
\u25a1 页眉页脚正确
\u25a1 页码连续
\u25a1 图表编号连续

引用检查:
\u25a1 正文引用与参考文献对应
\u25a1 参考文献格式统一(GB/T 7714)
\u25a1 引用数量达标

逻辑检查:
\u25a1 各章呼应研究问题
\u25a1 结论回应摘要
\u25a1 方法支撑结论
\u25a1 无自相矛盾

常见硬伤:
\u25a1 摘要超字数
\u25a1 关键词不规范
\u25a1 图表无标题
\u25a1 致谢提及导师姓名正确
\u25a1 目录与正文一致

需要逐项检查?""",

            "config": """[配置指南]

配置 DeepSeek API Key:
1. 访问 https://platform.deepseek.com
2. 注册账号(手机号即可)
3. 进入"API Keys"页面
4. 创建新 Key(免费赠送 500 万 tokens)
5. 复制 Key(以 sk- 开头)

在对话中输入:
配置 API Key: <YOUR_API_KEY>

即可解锁:
 无限次深度分析
 精准逻辑推理
 个性化学术建议

当前状态:{status}""",

            "unknown": """抱歉，我不太确定你的需求.你可以:

1. 描述你的论文阶段:
   - "我在选题"
   - "我在写大纲"
   - "我在写正文"
   - "准备答辩"

2. 粘贴论文段落让我检查

3. 问具体问题:
   - "文献综述怎么写"
   - "查重怎么降"
   - "格式怎么调"

4. 配置 DeepSeek API Key 获得更智能的回复

你想做什么?""",
        }

    def _get_english_defaults(self) -> Dict:
        """English default responses"""
        return {
            "greeting": """Hello! I am your thesis writing assistant. I can help with:

Full thesis process: Topic -> Proposal -> Outline -> Writing -> Revision -> Plagiarism check -> Defense
Specialized guidance: Literature review, quantitative/qualitative research, plagiarism reduction, tool recommendations
Real-time review: Paste your thesis paragraphs for analysis

Tell me which stage you are at?""",

            "topic_help": """[Topic Selection Diagnosis]

Please tell me:
1. Your major/discipline? (e.g., Computer Science, Business, Education...)
2. Bachelor's or Master's level?
3. Any specific interests? (No worries if not)

I will recommend 3-5 topics based on your situation and evaluate difficulty and innovation.""",

            "outline_help": """[Outline Construction]

Please provide:
1. Thesis title (or general direction)
2. Major/discipline
3. Degree type(Bachelor's/Master's)

I will generate a multi-level outline including:
- Chapter structure(3-4 levels)
- Writing guidance for each section
- Word count allocation suggestions
- Logical relationship explanations""",

            "chapter_review_intro": """[Chapter Review]

I performed a basic check and found the following issues:

{issues}

Tip: This is basic local analysis. For deep logical analysis and argument evaluation, consider configuring DeepSeek API Key.""",

            "proposal_help": """[Research Proposal]

Standard structure:
1. Research background and significance(start with specific problems)
2. Literature review(classified review + commentary)
3. Research objectives and content(specific and measurable)
4. Research methods and technical route(methods match problems)
5. Expected results and innovation points(explain what is 'new')
6. Research plan and timeline(allow time for revisions)

Tell me your topic, and I will help you develop each section.""",

            "format_question": """[Format Standards]

Common formatting requirements:
- Headings: Bold, Chapter titles 16 pt, Section 14 pt, Subsection 12 pt
- Body text: Times New Roman, 12 pt, 1.5 line spacing
- Citations: APA/MLA/IEEE/Chicago(varies by discipline)
- Margins: 1 inch(2.54 cm) all sides
- Page numbers: Bottom center or outer margin

 Note: Always follow your institution is specific template!

Need detailed explanation of any part?""",

            "citation_question": """[Citation Standards]

Common citation formats:

APA 7 th Edition:
- Journal: Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.
- Book: Author, A. A. (Year). Title of work. Publisher.

MLA 9 th Edition:
- Author. 'Title of Article.' Journal Name, vol.  # , no. #, Year, pp. #-#.

IEEE:
- [1] A. Author, 'Title,' Journal, vol.  # , no. #, pp. #-#, Month Year.

Tool recommendation: Zotero(free, excellent for managing references)

Need specific examples or tool tutorials?""",

            "methodology": """[Research Methods]

Quantitative Research(Surveys):
- Variable design -> Questionnaire development -> Pilot test -> 正式发放 -> Data analysis
- Tools: SPSS, AMOS, PROCESS, R
- Key: Reliability(alpha > 0.7), Validity(KMO > 0.7)

Qualitative Research(Interviews/Cases):
- Interview design -> Data collection -> Coding analysis -> Theme extraction
- Tools: NVivo, Atlas.ti, MAXQDA
- Key: Triangulation, member checking

Tell me your research method, and I will provide a detailed guide.""",

            "defense_prep": """[Defense Preparation]

PPT Framework(7 slides):
1. Title page(Title + Name + Advisor)
2. Research background(1.5 minutes)
3. Research objectives and significance(1 minute)
4. Research methods(1.5 minutes)
5. Research results(2.5 minutes, core)
6. Conclusion and future directions(1 minute)
7. Acknowledgments(0.5 minutes)

Presentation script template:
'Good morning/afternoon, distinguished committee members. My name is XXX, majoring in XXX. My thesis is titled XXX. Today, I will present my research from three aspects: background, methods, and findings...'

Common questions:
- What is your innovation/novelty?
- Why did you choose this method?
- Is your sample size sufficient?
- What are the limitations of your study?

Need mock defense or detailed templates?""",

            "plagiarism": """[Plagiarism Check & Reduction]

Plagiarism detection systems:
- Turnitin(widely used internationally)
- iThenticate(for researchers/publishers)
- University-specific systems

Reduction principles:
[OK] Effective: Sentence restructuring, adding data/cases, using figures/tables
[X] Ineffective: Simple synonym replacement, back-translation, screenshots

AI Detection:
- Turnitin AI Detection
- GPTZero
- Recommendation: Rewrite in your own words, not just synonym replacement

Need specific reduction examples?""",

            "literature_review": """[Literature Review]

Four-step method:
1. Search: Web of Science, Scopus, Google Scholar, discipline databases
2. Screen: Read title -> abstract -> conclusion, judge relevance
3. Classify: By theme/method/perspective/chronology
4. Critique: Summarize + critique + identify research gaps

Writing framework:
Example: Existing research has mainly explored from X perspectives:
1. ... (Author A, Year)
2. ... (Author B, Year)
However, existing research has limitations in XXX...

Need templates or specific examples?""",

            "writing_guide": """[Academic Writing]

Common mistakes:
[X] 'With the development of the internet...' -> [OK] 'In the field of XXX, traditional methods face YYY challenges...'
[X] 'I think...' -> [OK] 'Research shows...' / 'This study argues that...'
[X] 'Getting better and better' -> [OK] 'Increased from XX% to XX%'
[X] 'Then... Next...' -> [OK] 'Therefore... Furthermore... However...'

Paragraph structure:
- One central argument per paragraph
- Argument -> Evidence -> Analysis -> Conclusion
- Topic sentence at beginning, transition at end

Need specific revision examples?""",

            "toolchain": """[Tool Recommendations]

Reference Management:
- Zotero(free, recommended)
- EndNote(institutional licenses available)
- Mendeley(good PDF management)

Writing Tools:
- Word + Zotero(Humanities/Social Sciences)
- LaTeX/Overleaf(STEM with formulas)
- Google Docs(collaboration)

Data Analysis:
- SPSS(basic statistics)
- R/Python(advanced analysis)
- Stata(Economics)
- NVivo(qualitative research)

Time Management:
- Gantt charts(Excel/Project)
- Pomodoro Technique(25+5)
- Backward planning(from defense date)

Need specific tutorials?""",

            "checklist": """[Pre-submission Checklist]

Format check:
[] Heading hierarchy(Chapter/Section/Subsection)
[] Consistent font and size
[] Correct headers and footers
[] Continuous page numbers
[] Continuous figure/table numbering

Citation check:
[] In-text citations match reference list
[] Consistent citation format(APA/MLA/IEEE/Chicago)
[] Sufficient number of references

Logic check:
[] Each chapter addresses research questions
[] Conclusion responds to abstract
[] Methods support conclusions
[] No contradictions

Common issues:
[] Abstract within word limit
[] Keywords properly formatted
[] Figures/tables have titles
[] Acknowledgments mention correct advisor name
[] Table of contents matches body

Want item-by-item checking?""",

            "config": """[Configuration Guide]

Configure DeepSeek API Key:
1. Visit https: // platform.deepseek.com
2. Register an account
3. Go to "API Keys" page
4. Create a new Key(free 5 million tokens)
5. Copy the Key(starts with sk-)

In the chat, type:
Configure API Key: <YOUR_API_KEY>

To unlock:
[OK] Unlimited deep analysis
[OK] Precise logical reasoning
[OK] Personalized academic advice

Current status: {status}""",

            "unknown": """Sorry, I am not sure what you need. You can:

1. Describe your thesis stage:
   - "I am choosing a topic"
   - "I am writing an outline"
   - "I am writing the body"
   - "Preparing for defense"

2. Paste thesis paragraphs for review

3. Ask specific questions:
   - "How to write a literature review"
   - "How to reduce plagiarism score"
   - "How to format citations"

4. Configure DeepSeek API Key for smarter responses

What would you like to do?""",
        }

    def _get_japanese_defaults(self) -> Dict:
        """日本語のデフォルト応答"""
        return {
            "greeting": """こんにちは!論文執筆アシスタントです.以下をお手伝いします:

論文全流程:テーマ選定 -> 研究計画書 -> アウトライン -> 執筆 -> 修正 -> 重複チェック -> 答弁
専門指導:文献綜述,量的/質的研究,重複削減,ツール推奨
リアルタイム批注:論文段落を貼り付けてチェックします

どの段階でつまづいていますか?""",

            "topic_help": """[テーマ選定診断]

以下を教えてください:
1. あなたの専門分野は?(例:コンピュータサイエンス,経営学,教育学...)
2. 学部か大学院か?
3. 興味のある方向性は?(なくても大丈夫です)

あなたの状況に基づいて3-5つのテーマを推薦し,難易度と革新性を評価します.""",

            "outline_help": """[アウトライン構築]

以下を提供してください:
1. 論文タイトル(または大まかな方向)
2. 専門分野
3. 学位タイプ(学部/修士)

以下を含む多階層アウトラインを生成します:
- 章節構造(3-4階層)
- 各節の執筆指針
- 文字数配分の提案
- 論理関係の説明""",

            "chapter_review_intro": """[章節批注]

基本チェックを実施し,以下の問題を発見しました:

{issues}

ヒント:これはローカル基本分析です.深い論理分析や論証評価には,DeepSeek API Keyの設定をお勧めします.""",

            "proposal_help": """[研究計画書]

標準構造:
1. 研究背景と意義(具体的な問題から切入)
2. 国内外の研究現状(分類綜述+評価)
3. 研究目標と内容(具体的で測定可能)
4. 研究方法と技術ロードマップ(手法が問題にマッチ)
5. 期待される成果と革新点([新しさ]を具体的に説明)
6. 研究計画とスケジュール(修正時間を確保)

テーマを教えてください.各節の展開をお手伝いします.""",

            "format_question": """[フォーマット規範]

よくあるフォーマット要件:
- タイトル:太字,第1級タイトル16 pt,第2級14 pt,第3級12 pt
- 本文:Times New Roman,12 pt,1.5倍行間
- 引用:APA/MLA/IEEE/Chicago(分野による)
- 余白:1インチ(2.54 cm)四方
- ページ番号:下部中央または外側

注意:必ず学校のテンプレートに従ってください!

どの部分の詳細説明が必要ですか?""",

            "citation_question": """[引用規範]

よくある引用形式:

APA第7版:
- 雑誌:Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.
- 書籍:Author, A. A. (Year). Title of work. Publisher.

MLA第9版:
- Author. "Title of Article." Journal Name, vol. #, no. #, Year, pp. #-#.

IEEE:
- [1] A. Author, "Title," Journal, vol. #, no. #, pp. #-#, Month Year.

ツール推奨:Zotero(無料,参考文献管理に優れた)

具体的な例やツールチュートリアルが必要ですか?""",

            "methodology": """[研究方法]

量的研究(アンケート法):
- 変数設計 -> アンケート作成 -> 予備テスト -> 本格実施 -> データ分析
- ツール:SPSS,AMOS,PROCESS,R
- 重点:信頼性(alpha>0.7),妥当性(KMO>0.7)

質的研究(インタビュー/ケース):
- インタビュー設計 -> データ収集 -> コーディング分析 -> テーマ抽出
- ツール:NVivo,Atlas.ti,MAXQDA
- 重点:三角測量,メンバー検証

研究方法を教えてください.詳細なガイドを提供します.""",

            "defense_prep": """[答弁準備]

PPTフレームワーク(7枚):
1. 表紙(タイトル+氏名+指導教員)
2. 研究背景(1.5分)
3. 研究目的と意義(1分)
4. 研究方法(1.5分)
5. 研究結果(2.5分,核心)
6. 結論と展望(1分)
7. 謝辞(0.5分)

陳述原稿テンプレート:
[審査委員の先生方,こんにちは.XXXと申します.専門はXXXです.論文のタイトルは[XXX]です.本日は,研究背景,研究方法,研究結果の3つの側面からご報告いたします...]

よくある質問:
- 革新点は何ですか?
- なぜこの手法を選んだのですか?
- サンプル量は十分ですか?
- 研究の限界は?

模擬答弁や詳細なテンプレートが必要ですか?""",

            "plagiarism": """[重複チェックと削減]

重複検出システム:
- 知网CNKI(中国高校主流)
- Turnitin(国際的に広く使用)
- iThenticate(研究者/出版社向け)

削減原則:
[OK] 効果的:文再構成,データ/事例追加,図表活用
[X] 非効果的:単純な同義語置き換え,往復翻訳,スクリーンショット

AI検出:
- Turnitin AI Detection
- GPTZero
- 推奨:自分の言葉で書き直す,単なる同義語置き換えではない

具体的な削減例が必要ですか?""",

            "literature_review": """[文献綜述]

4ステップ法:
1. 検索:Web of Science,Scopus,Google Scholar,分野別データベース
2. 絞り込み:タイトル->要旨->結論を読み,関連性を判断
3. 分類:テーマ/方法/視点/年代別
4. 評価:まとめ+批判+研究ギャップの特定

執筆フレームワーク:
例:既存研究は主にXつの視点から探索してきた:
1. ...(著者A,年)
2. ...(著者B,年)
しかし,既存研究はXXX方面で限界がある...

テンプレートや具体的な例が必要ですか?""",

            "writing_guide": """[学術執筆]

よくある間違い:
[X] [インターネットの発展に伴い...]-> [OK] [XXX分野では,従来の手法はYYY課題に直面している...]
[X] [我认为...]-> [OK] [研究は示している...]/[本研究は主張する...]
[X] [越来越好]-> [OK] [XX%からXX%に向上]
[X] [然后...接着...]-> [OK] [Therefore... Furthermore... However...]

段落構造:
- 各段落に1つの中心論点
- 論点->論拠->分析->結論
- 段落冒頭にトピックセンテンス,末尾に遷移

具体的な修正例が必要ですか?""",

            "toolchain": """[ツール推奨]

文献管理:
- Zotero(無料,推奨)
- EndNote(学校ライセンスあり)
- Mendeley(PDF管理に優れた)

執筆ツール:
- Word + Zotero(人文科学/社会科学)
- LaTeX/Overleaf(理工系,数式向け)
- Google Docs(コラボレーション)

データ分析:
- SPSS(基礎統計)
- R/Python(高度分析)
- Stata(経済学)
- NVivo(質的研究)

時間管理:
- ガントチャート(Excel/Project)
- ポモドーロテクニック(25+5)
- 逆算計画(答弁日から逆算)

具体的なチュートリアルが必要ですか?""",

            "checklist": """[提出前自己チェック]

フォーマットチェック:
[] タイトル階層(章/節/小節)
[] フォントとサイズの統一
[] ヘッダーとフッターの正確性
[] 連続するページ番号
[] 連続する図表番号

引用チェック:
[] 本文引用と参考文献リストの対応
[] 統一された引用形式(APA/MLA/IEEE/Chicago)
[] 十分な引用数

論理チェック:
[] 各章が研究問題に対応
[] 結論が要旨に応答
[] 手法が結論を裏付け
[] 矛盾がない

よくある問題:
[] 要旨が文字数制限内
[] キーワードが適切にフォーマット
[] 図表にタイトルあり
[] 謝辞で正しい指導教員名を言及
[] 目次が本文と一致

逐項チェックが必要ですか?""",

            "config": """[設定ガイド]

DeepSeek API Keyの設定:
1. https://platform.deepseek.com にアクセス
2. アカウント登録
3. [API Keys]ページに移動
4. 新しいKeyを作成(無料500万トークン)
5. Keyをコピー(sk-で始まる)

チャットで入力:
設定 API Key: <YOUR_API_KEY>

ロック解除:
[OK] 無制限の深度分析
[OK] 正確な論理推論
[OK] パーソナライズされた学術アドバイス

現在の状態:{status}""",

            "unknown": """申し訳ありませんが,ご要望が明確ではありません.以下が可能です:

1. 論文の段階を記述:
   - [テーマを選定中です]
   - [アウトラインを作成中です]
   - [本文を執筆中です]
   - [答弁準備中です]

2. 論文段落を貼り付けてレビュー

3. 具体的な質問:
   - [文献綜述の書き方]
   - [重複スコアの下げ方]
   - [引用フォーマットの方法]

4. DeepSeek API Keyを設定してよりスマートな応答を取得

何をしたいですか?""",
        }

    def _get_korean_defaults(self) -> Dict:
        """한국어 기본 응답"""
        return {
            "greeting": """안녕하세요! 논문 작성 어시스턴트입니다. 다음과 같은 내용을 도와드립니다:

논문 전체 과정: 주제 선정 -> 연구 계획서 -> 개요 -> 작성 -> 수정 -> 유사도 검사 -> 심사
전문 지도: 문헌 고찰, 양적/질적 연구, 유사도 감소, 도구 추천
실시간 첨삭: 논문 단락을 붙여넣으면 검토해 드립니다

어느 단계에서 막히셨나요?""",

            "topic_help": """[주제 선정 진단]

다음을 알려주세요:
1. 전공 분야는? (예: 컴퓨터 과학, 경영학, 교육학...)
2. 학부생인가요 대학원생인가요?
3. 관심 있는 방향이 있나요? (없어도 괜찮습니다)

상황에 맞춰 3-5개의 주제를 추천하고, 난이도와 혁신성을 평가해 드립니다.""",

            "outline_help": """[개요 작성]

다음을 제공해 주세요:
1. 논문 제목 (또는 대략적인 방향)
2. 전공 분야
3. 학위 유형 (학사/석사)

다음을 포함하는 다층 개요를 생성합니다:
- 장절 구성 (3-4 단계)
- 각 절의 작성 지침
- 글자 수 배분 제안
- 논리 관계 설명""",

            "chapter_review_intro": """[장절 첨삭]

기본 검사를 실시하여 다음과 같은 문제를 발견했습니다:

{issues}

팁: 이것은 로컬 기본 분석입니다. 심층 논리 분석과 논증 평가에는 DeepSeek API Key 설정을 권장합니다.""",

            "proposal_help": """[연구 계획서]

표준 구조:
1. 연구 배경과 의의 (구체적인 문제에서 시작)
2. 국내외 연구 현황 (분류 고찰 + 평가)
3. 연구 목표와 내용 (구체적이고 측정 가능)
4. 연구 방법과 기술 로드맵 (방법이 문제에 부합)
5. 기대 성과와 혁신점 (새로움을 구체적으로 설명)
6. 연구 계획과 일정 (수정 시간 확보)

주제를 알려주세요. 각 절의 전개를 도와드리겠습니다.""",

            "format_question": """[포맷 규범]

자주 있는 포맷 요구사항:
- 제목: 굵게, 1급 제목 16pt, 2급 14pt, 3급 12pt
- 본문: Times New Roman, 12pt, 1.5배 행간
- 인용: APA/MLA/IEEE/Chicago (분야에 따라 다름)
- 여백: 1인치 (2.54cm) 사방
- 페이지 번호: 하단 중앙 또는 바깥쪽

주의: 반드시 학교 템플릿을 따라주세요!

어떤 부분의 상세 설명이 필요한가요?""",

            "citation_question": """[인용 규범]

자주 있는 인용 형식:

APA 제7판:
- 저널: Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.
- 도서: Author, A. A. (Year). Title of work. Publisher.

MLA 제9판:
- Author. "Title of Article." Journal Name, vol. #, no. #, Year, pp. #-#.

IEEE:
- [1] A. Author, "Title," Journal, vol. #, no. #, pp. #-#, Month Year.

도구 추천: Zotero (무료, 참고 문헌 관리에 우수)

구체적인 예시나 도구 튜토리얼이 필요한가요?""",

            "methodology": """[연구 방법]

양적 연구 (설문법):
- 변수 설계 -> 설문 작성 -> 사전 테스트 -> 본격 실시 -> 데이터 분석
- 도구: SPSS, AMOS, PROCESS, R
- 중점: 신뢰도 (alpha > 0.7), 타당도 (KMO > 0.7)

질적 연구 (인터뷰/사례):
- 인터뷰 설계 -> 데이터 수집 -> 코딩 분석 -> 테마 추출
- 도구: NVivo, Atlas.ti, MAXQDA
- 중점: 삼각 검증, 구성원 검증

연구 방법을 알려주세요. 상세한 가이드를 제공합니다.""",

            "defense_prep": """[심사 준비]

PPT 프레임워크 (7장):
1. 표지 (제목 + 성명 + 지도교수)
2. 연구 배경 (1.5분)
3. 연구 목적과 의의 (1분)
4. 연구 방법 (1.5분)
5. 연구 결과 (2.5분, 핵심)
6. 결론과 전망 (1분)
7. 감사 인사 (0.5분)

진술 원고 템플릿:
[심사 위원님들, 안녕하세요. XXX라고 합니다. 전공은 XXX입니다. 논문 제목은 [XXX]입니다. 오늘 연구 배경, 연구 방법, 연구 결과의 세 가지 측면에서 보고드리겠습니다...]

자주 나오는 질문:
- 혁신점은 무엇인가요?
- 왜 이 방법을 선택했나요?
- 표본 수는 충분한가요?
- 연구의 한계는?

모의 심사나 상세한 템플릿이 필요한가요?""",

            "plagiarism": """[유사도 검사와 감소]

유사도 검출 시스템:
- Turnitin (국제적으로 널리 사용)
- iThenticate (연구자/출판사용)
- 대학별 시스템

감소 원칙:
[OK] 효과적: 문장 재구성, 데이터/사례 추가, 도표 활용
[X] 비효과적: 단순한 동의어 치환, 왕복 번역, 스크린샷

AI 검출:
- Turnitin AI Detection
- GPTZero
- 추천: 자신의 말로 다시 쓰기, 단순한 동의어 치환 아님

구체적인 감소 예시가 필요한가요?""",

            "literature_review": """[문헌 고찰]

4단계 법:
1. 검색: Web of Science, Scopus, Google Scholar, 분야별 데이터베이스
2. 선별: 제목 -> 초록 -> 결론을 읽고 관련성 판단
3. 분류: 테마/방법/시각/연대별
4. 평가: 요약 + 비판 + 연구 갭 파악

작성 프레임워크:
예: 기존 연구는 주로 X가지 시각에서 탐색해 왔다:
1. ... (저자 A, 연도)
2. ... (저자 B, 연도)
그러나 기존 연구는 XXX 측면에서 한계가 있다...

템플릿이나 구체적인 예시가 필요한가요?""",

            "writing_guide": """[학술 집필]

자주 있는 실수:
[X] [인터넷의 발전에 따라...] -> [OK] [XXX 분야에서는 기존 방법이 YYY 과제에 직면하고 있다...]
[X] [나는 생각한다...] -> [OK] [연구는 보여준다...] / [본 연구는 주장한다...]
[X] [점점 좋아진다] -> [OK] [XX%에서 XX%로 향상]
[X] [그런 다음... 이어서...] -> [OK] [Therefore... Furthermore... However...]

단락 구조:
- 각 단락에 1개의 중심 논점
- 논점 -> 근거 -> 분석 -> 결론
- 단락 앞에 토픽 센텐스, 끝에 전환

구체적인 수정 예시가 필요한가요?""",

            "toolchain": """[도구 추천]

문헌 관리:
- Zotero (무료, 추천)
- EndNote (학교 라이선스 있음)
- Mendeley (PDF 관리에 우수)

집필 도구:
- Word + Zotero (인문학/사회과학)
- LaTeX/Overleaf (이공계, 수식용)
- Google Docs (협업)

데이터 분석:
- SPSS (기초 통계)
- R/Python (고급 분석)
- Stata (경제학)
- NVivo (질적 연구)

시간 관리:
- 간트 차트 (Excel/Project)
- 포모도로 기법 (25+5)
- 역산 계획 (심사일에서 역산)

구체적인 튜토리얼이 필요한가요?""",

            "checklist": """[제출 전 자가 체크]

포맷 체크:
[] 제목 계층 (장/절/소절)
[] 폰트와 크기 통일
[] 머리글과 바닥글의 정확성
[] 연속된 페이지 번호
[] 연속된 도표 번호

인용 체크:
[] 본문 인용과 참고 문헌 목록의 대응
[] 통일된 인용 형식 (APA/MLA/IEEE/Chicago)
[] 충분한 인용 수

논리 체크:
[] 각 장이 연구 문제에 대응
[] 결론이 초록에 응답
[] 방법이 결론을 뒷받침
[] 모순이 없음

자주 있는 문제:
[] 초록이 글자 수 제한 내
[] 키워드가 적절하게 포맷
[] 도표에 제목 있음
[] 감사 인사에서 올바른 지도교수명 언급
[] 목차가 본문과 일치

항목별 체크가 필요한가요?""",

            "config": """[설정 가이드]

DeepSeek API Key 설정:
1. https://platform.deepseek.com 접속
2. 계정 등록
3. [API Keys] 페이지로 이동
4. 새로운 Key 생성 (무료 500만 토큰)
5. Key 복사 (sk-로 시작)

채팅에서 입력:
설정 API Key: <YOUR_API_KEY>

잠금 해제:
[OK] 무제한 심층 분석
[OK] 정확한 논리 추론
[OK] 맞춤형 학술 조언

현재 상태: {status}""",

            "unknown": """죄송합니다만, 요청이 명확하지 않습니다. 다음과 같은 것이 가능합니다:

1. 논문 단계를 기술:
   - [주제를 선정 중입니다]
   - [개요를 작성 중입니다]
   - [본문을 집필 중입니다]
   - [심사 준비 중입니다]

2. 논문 단락을 붙여넣어 리뷰 요청

3. 구체적인 질문:
   - [문헌 고찰 작성법]
   - [유사도 점수 낮추는 법]
   - [인용 포맷 방법]

4. DeepSeek API Key를 설정하여 더 스마트한 응답 받기

무엇을 하시겠습니까?""",
        }

    def _get_french_defaults(self) -> Dict:
        """Reponses par defaut en francais"""
        return {
            "greeting": """Bonjour! Je suis votre assistant de redaction de these. Je peux vous aider avec:

Processus complet: Choix du sujet -> Proposition -> Plan -> Redaction -> Revision -> Verification anti-plagiat -> Soutenance
Guidance specialisee: Revue de litterature, recherche quantitative/qualitative, reduction du plagiat, recommandations d'outils
Annotation en temps reel: Collez vos paragraphes de these pour analyse

A quelle etape etes-vous bloque?""",

            "topic_help": """[Diagnostic du choix de sujet]

Veuillez me dire:
1. Votre domaine d'etudes? (ex: Informatique, Gestion, Education...)
2. Licence ou Master?
3. Avez-vous des interets specifiques? (pas grave si non)

Je recommanderai 3-5 sujets base sur votre situation et evaluerai la difficulte et l'innovation.""",

            "outline_help": """[Construction du plan]

Veuillez fournir:
1. Titre de la these (ou direction generale)
2. Domaine d'etudes
3. Type de diplome (Licence/Master)

Je generai un plan multiniveau incluant:
- Structure des chapitres (3-4 niveaux)
- Directives de redaction pour chaque section
- Proposition de repartition des mots
- Explication des relations logiques""",

            "chapter_review_intro": """[Annotation de chapitre]

J'ai effectue une verification de base et trouve les problemes suivants:

{issues}

Conseil: Ceci est une analyse de base locale. Pour une analyse logique approfondie et une evaluation de l'argumentation, configurez la cle API DeepSeek.""",

            "proposal_help": """[Proposition de recherche]

Structure standard:
1. Contexte et signification (partir de problemes specifiques)
2. Etat de l'art national et international (revue classee + evaluation)
3. Objectifs et contenu (specifiques et mesurables)
4. Methodes et feuille de route (methodes adequates au probleme)
5. Resultats attendus et points d'innovation (expliquer ce qui est nouveau)
6. Plan et calendrier (prevoir du temps pour les revisions)

Dites-moi votre sujet. Je vous aiderai a developper chaque section.""",

            "format_question": """[Normes de format]

Exigences de format courantes:
- Titres: Gras, titre niveau 1: 16pt, niveau 2: 14pt, niveau 3: 12pt
- Corps: Times New Roman, 12pt, interligne 1.5
- Citations: APA/MLA/IEEE/Chicago (selon la discipline)
- Marges: 1 pouce (2.54 cm) tous les cotes
- Numeros de page: Bas de page centre ou exterieur

Attention: Suivez toujours le modele de votre universite!

Quelle partie necessite une explication detaillee?""",

            "citation_question": """[Normes de citation]

Formats de citation courants:

APA 7e edition:
- Journal: Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.
- Livre: Author, A. A. (Year). Title of work. Publisher.

MLA 9e edition:
- Author. "Title of Article." Journal Name, vol. #, no. #, Year, pp. #-#.

IEEE:
- [1] A. Author, "Title," Journal, vol. #, no. #, pp. #-#, Month Year.

Outil recommande: Zotero (gratuit, excellent pour la gestion bibliographique)

Avez-vous besoin d'exemples specifiques ou de tutoriels?""",

            "methodology": """[Methodes de recherche]

Recherche quantitative (enquete):
- Conception des variables -> Questionnaire -> Test pilote -> Enquete complete -> Analyse des donnees
- Outils: SPSS, AMOS, PROCESS, R
- Points cles: Fiabilite (alpha > 0.7), Validite (KMO > 0.7)

Recherche qualitative (entretiens/cas):
- Conception de l'entretien -> Collecte de donnees -> Analyse par codage -> Extraction des themes
- Outils: NVivo, Atlas.ti, MAXQDA
- Points cles: Triangulation, verification par les membres

Dites-moi votre methode de recherche. Je fournirai un guide detaille.""",

            "defense_prep": """[Preparation de la soutenance]

Cadre PPT (7 diapositives):
1. Page de titre (Titre + Nom + Directeur)
2. Contexte de recherche (1.5 min)
3. Objectifs et signification (1 min)
4. Methodes de recherche (1.5 min)
5. Resultats (2.5 min, noyau)
6. Conclusion et perspectives (1 min)
7. Remerciements (0.5 min)

Modele de discours:
[Mesdames et Messieurs les membres du jury, bonjour. Je suis XXX, specialise(e) en XXX. Ma these s'intitule [XXX]. Aujourd'hui, je presenterai ma recherche sous trois aspects: le contexte, les methodes et les resultats...]

Questions frequentes:
- Quelle est votre innovation?
- Pourquoi avez-vous choisi cette methode?
- Votre echantillon est-il suffisant?
- Quelles sont les limites de votre etude?

Avez-vous besoin d'une soutenance simulee ou de modeles detailles?""",

            "plagiarism": """[Verification et reduction du plagiat]

Systemes de detection:
- Turnitin (largement utilise internationalement)
- iThenticate (pour chercheurs/editeurs)
- Systemes specifiques aux universites

Principes de reduction:
[OK] Efficace: Restructuration de phrases, ajout de donnees/exemples, utilisation de figures/tableaux
[X] Inefficace: Simple substitution de synonymes, traduction aller-retour, captures d'ecran

Detection IA:
- Turnitin AI Detection
- GPTZero
- Recommandation: Recrire dans vos propres mots, pas seulement substituer des synonymes

Avez-vous besoin d'exemples specifiques de reduction?""",

            "literature_review": """[Revue de litterature]

Methode en 4 etapes:
1. Recherche: Web of Science, Scopus, Google Scholar, bases de donnees par discipline
2. Tri: Lire titre -> resume -> conclusion, juger la pertinence
3. Classification: Par theme/methode/perspective/chronologie
4. Evaluation: Synthese + critique + identification des lacunes

Cadre de redaction:
Exemple: Les recherches existantes ont principalement explore sous X perspectives:
1. ... (Auteur A, annee)
2. ... (Auteur B, annee)
Cependant, les recherches existantes presentent des limites dans XXX...

Avez-vous besoin de modeles ou d'exemples specifiques?""",

            "writing_guide": """[Redaction academique]

Erreurs courantes:
[X] [Avec le developpement d'internet...] -> [OK] [Dans le domaine de XXX, les methodes traditionnelles font face a des defis YYY...]
[X] [Je pense que...] -> [OK] [La recherche montre que...] / [Cette etude soutient que...]
[X] [De mieux en mieux] -> [OK] [Augmentation de XX% a XX%]
[X] [Puis... Ensuite...] -> [OK] [Therefore... Furthermore... However...]

Structure des paragraphes:
- Un argument central par paragraphe
- Argument -> Preuve -> Analyse -> Conclusion
- Phrase thematique au debut, transition a la fin

Avez-vous besoin d'exemples de revision specifiques?""",

            "toolchain": """[Recommandations d'outils]

Gestion bibliographique:
- Zotero (gratuit, recommande)
- EndNote (licences institutionnelles)
- Mendeley (bonne gestion PDF)

Outils de redaction:
- Word + Zotero (Sciences humaines/sociales)
- LaTeX/Overleaf (STEM, formules)
- Google Docs (collaboration)

Analyse de donnees:
- SPSS (statistiques de base)
- R/Python (analyse avancee)
- Stata (economie)
- NVivo (recherche qualitative)

Gestion du temps:
- Diagramme de Gantt (Excel/Project)
- Technique Pomodoro (25+5)
- Planification retrograde (a partir de la date de soutenance)

Avez-vous besoin de tutoriels specifiques?""",

            "checklist": """[Verification avant soumission]

Verification du format:
[] Hierarchie des titres (chapitre/section/sous-section)
[] Police et taille uniformes
[] En-tetes et pieds de page corrects
[] Numeros de page continus
[] Numerotation continue des figures/tableaux

Verification des citations:
[] Correspondance entre citations dans le texte et liste de references
[] Format de citation uniforme (APA/MLA/IEEE/Chicago)
[] Nombre suffisant de references

Verification logique:
[] Chaque chapitre repond aux questions de recherche
[] La conclusion repond au resume
[] Les methodes soutiennent les conclusions
[] Pas de contradictions

Problemes courants:
[] Resume dans la limite de mots
[] Mots-cles correctement formates
[] Figures/tableaux avec titre
[] Remerciements mentionnant le bon directeur
[] Table des matieres correspond au texte

Avez-vous besoin d'une verification element par element?""",

            "config": """[Guide de configuration]

Configuration de la cle API DeepSeek:
1. Acceder a https://platform.deepseek.com
2. Creer un compte
3. Aller sur la page "API Keys"
4. Creer une nouvelle cle (5 millions de tokens gratuits)
5. Copier la cle (commence par sk-)

Entrez dans le chat:
Configurer API Key: <YOUR_API_KEY>

Debloquer:
[OK] Analyse approfondie illimitee
[OK] Raisonnement logique precis
[OK] Conseils academiques personnalises

Statut actuel: {status}""",

            "unknown": """Desole, votre demande n'est pas claire. Voici ce que vous pouvez faire:

1. Decrivez votre etape de redaction:
   - [Je choisis un sujet]
   - [Je redige le plan]
   - [Je redige le corps du texte]
   - [Je prepare la soutenance]

2. Collez des paragraphes pour revue

3. Posez des questions specifiques:
   - [Comment rediger une revue de litterature]
   - [Comment reduire le score de plagiat]
   - [Comment formater les citations]

4. Configurez la cle API DeepSeek pour des reponses plus intelligentes

Que souhaitez-vous faire?""",
        }

    def _get_german_defaults(self) -> Dict:
        """Deutsche Standardantworten"""
        return {
            "greeting": """Hallo! Ich bin Ihr Assistent beim Schreiben wissenschaftlicher Arbeiten. Ich kann Ihnen helfen bei:

Gesamter Prozess: Themenwahl -> Expose -> Gliederung -> Schreiben -> Uberarbeitung -> Plagiatsprufung -> Verteidigung
Spezialisierte Beratung: Literaturubersicht, quantitative/qualitative Forschung, Plagiarismusreduktion, Werkzeugempfehlungen
Echtzeit-Annotation: Fugen Sie Ihre Absatze zur Uberprufung ein

In welchem Stadium sind Sie gerade?""",

            "topic_help": """[Diagnose der Themenauswahl]

Bitte teilen Sie mir mit:
1. Ihr Fachgebiet? (z.B. Informatik, BWL, Padagogik...)
2. Bachelor- oder Masterarbeit?
3. Haben Sie besondere Interessen? (auch ohne geht es)

Ich empfehle 3-5 Themen basierend auf Ihrer Situation und bewerte Schwierigkeitsgrad und Innovation.""",

            "outline_help": """[Gliederung erstellen]

Bitte geben Sie an:
1. Titel der Arbeit (oder ungefahre Richtung)
2. Fachgebiet
3. Abschlusstyp (Bachelor/Master)

Ich erstelle eine mehrstufige Gliederung mit:
- Kapitelstruktur (3-4 Ebenen)
- Schreibrichtlinien fur jeden Abschnitt
- Wortanzahl-Vorschlag
- Erklarung der logischen Beziehungen""",

            "chapter_review_intro": """[Kapitel-Annotation]

Ich habe eine grundlegende Uberprufung durchgefuhrt und folgende Probleme gefunden:

{issues}

Tipp: Dies ist eine lokale Basisanalyse. Fur eine tiefgehende logische Analyse und Argumentationsbewertung konfigurieren Sie bitte den DeepSeek API Key.""",

            "proposal_help": """[Expose]

Standardstruktur:
1. Hintergrund und Bedeutung (von konkreten Problemen ausgehen)
2. Stand der Forschung (klassifizierte Ubersicht + Bewertung)
3. Forschungsziele und Inhalte (konkret und messbar)
4. Methoden und methodische Roadmap (Methoden passen zum Problem)
5. Erwartete Ergebnisse und Innovationen (was ist neu, konkret erklaren)
6. Forschungsplan und Zeitplan (Zeit fur Uberarbeitungen einplanen)

Nennen Sie mir Ihr Thema. Ich helfe bei der Entwicklung jedes Abschnitts.""",

            "format_question": """[Formatnormen]

Haufige Formatanforderungen:
- Uberschriften: Fett, Uberschrift 1: 16pt, Uberschrift 2: 14pt, Uberschrift 3: 12pt
- Flie?text: Times New Roman, 12pt, 1,5-zeilig
- Zitationen: APA/MLA/IEEE/Chicago (je nach Fachgebiet)
- Raender: 1 Zoll (2,54 cm) auf allen Seiten
- Seitenzahlen: Unten mittig oder au?en

Wichtig: Folgen Sie immer der Vorlage Ihrer Universitat!

Welcher Teil benotigt eine detaillierte Erklarung?""",

            "citation_question": """[Zitationsnormen]

Haufige Zitationsformate:

APA 7. Auflage:
- Zeitschrift: Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.
- Buch: Author, A. A. (Year). Title of work. Publisher.

MLA 9. Auflage:
- Author. "Title of Article." Journal Name, vol. #, no. #, Year, pp. #-#.

IEEE:
- [1] A. Author, "Title," Journal, vol. #, no. #, pp. #-#, Month Year.

Empfohlenes Werkzeug: Zotero (kostenlos, ausgezeichnet fur Literaturverwaltung)

Benotigen Sie konkrete Beispiele oder Tutorials?""",

            "methodology": """[Forschungsmethoden]

Quantitative Forschung (Befragung):
- Variablenkonzeption -> Fragebogen -> Pilotierung -> Durchfuhrung -> Datenanalyse
- Werkzeuge: SPSS, AMOS, PROCESS, R
- Schwerpunkte: Reliabilitat (alpha > 0,7), Validitat (KMO > 0,7)

Qualitative Forschung (Interviews/Fallstudien):
- Interviewkonzeption -> Datenerhebung -> Kodierung -> Themeextraktion
- Werkzeuge: NVivo, Atlas.ti, MAXQDA
- Schwerpunkte: Triangulation, Mitgliederuberprufung

Nennen Sie mir Ihre Forschungsmethode. Ich liefere eine detaillierte Anleitung.""",

            "defense_prep": """[Verteidigungsvorbereitung]

PPT-Rahmenwerk (7 Folien):
1. Titelfolie (Titre + Name + Betreuer)
2. Forschungshintergrund (1,5 Min.)
3. Forschungsziele und Bedeutung (1 Min.)
4. Forschungsmethoden (1,5 Min.)
5. Forschungsergebnisse (2,5 Min., Kern)
6. Schlussfolgerung und Ausblick (1 Min.)
7. Danksagung (0,5 Min.)

Redemanuskript-Vorlage:
[Sehr geehrte Mitglieder der Prufungskommission, mein Name ist XXX. Ich studiere XXX. Der Titel meiner Arbeit ist [XXX]. Heute werde ich meine Forschung in drei Aspekten vorstellen: den Hintergrund, die Methoden und die Ergebnisse...]

Haufig gestellte Fragen:
- Was ist Ihre Innovation?
- Warum haben Sie diese Methode gewahlt?
- Ist Ihre Stichprobe ausreichend?
- Was sind die Grenzen Ihrer Studie?

Benotigen Sie eine simulierte Verteidigung oder detaillierte Vorlagen?""",

            "plagiarism": """[Plagiatsprufung und -reduktion]

Erkennungssysteme:
- Turnitin (international weit verbreitet)
- iThenticate (fur Forscher/Verlage)
- Universitatseigene Systeme

Reduktionsprinzipien:
[OK] Wirksam: Satzumstrukturierung, Hinzufugung von Daten/Beispielen, Verwendung von Abbildungen/Tabellen
[X] Unwirksam: Einfache Synonymersetzung, Hin- und Herubersetzung, Screenshots

KI-Erkennung:
- Turnitin AI Detection
- GPTZero
- Empfehlung: In eigenen Worten umschreiben, nicht nur Synonyme ersetzen

Benotigen Sie konkrete Reduktionsbeispiele?""",

            "literature_review": """[Literaturubersicht]

4-Schritte-Methode:
1. Suche: Web of Science, Scopus, Google Scholar, fachspezifische Datenbanken
2. Auswahl: Titel -> Zusammenfassung -> Schlussfolgerung lesen, Relevanz beurteilen
3. Klassifizierung: Nach Thema/Methode/Perspektive/Chronologie
4. Bewertung: Zusammenfassung + Kritik + Forschungslucken identifizieren

Schreibrahmenwerk:
Beispiel: Bestehende Forschungen haben hauptsachlich unter X Perspektiven untersucht:
1. ... (Autor A, Jahr)
2. ... (Autor B, Jahr)
Allerdings zeigen bestehende Forschungen Grenzen in XXX...

Benotigen Sie Vorlagen oder konkrete Beispiele?""",

            "writing_guide": """[Wissenschaftliches Schreiben]

Haufige Fehler:
[X] [Mit der Entwicklung des Internets...] -> [OK] [Im Bereich XXX stehen traditionelle Methoden vor Herausforderungen YYY...]
[X] [Ich denke...] -> [OK] [Die Forschung zeigt...] / [Diese Studie argumentiert...]
[X] [Immer besser] -> [OK] [Steigerung von XX% auf XX%]
[X] [Dann... Danach...] -> [OK] [Therefore... Furthermore... However...]

Absatzstruktur:
- Ein zentrales Argument pro Absatz
- Argument -> Beweis -> Analyse -> Schlussfolgerung
- Themensatz am Anfang, ubergang am Ende

Benotigen Sie konkrete Uberarbeitungsbeispiele?""",

            "toolchain": """[Werkzeugempfehlungen]

Literaturverwaltung:
- Zotero (kostenlos, empfohlen)
- EndNote (Universitatslizenzen)
- Mendeley (gute PDF-Verwaltung)

Schreibwerkzeuge:
- Word + Zotero (Geistes-/Sozialwissenschaften)
- LaTeX/Overleaf (MINT-Facher, Formeln)
- Google Docs (Zusammenarbeit)

Datenanalyse:
- SPSS (Basisstatistik)
- R/Python (Fortgeschrittene Analyse)
- Stata (Wirtschaftswissenschaften)
- NVivo (Qualitative Forschung)

Zeitmanagement:
- Gantt-Diagramm (Excel/Project)
- Pomodoro-Technik (25+5)
- Ruckwartsplanung (ab Verteidigungsdatum)

Benotigen Sie konkrete Tutorials?""",

            "checklist": """[Prufung vor der Abgabe]

Formatprufung:
[] Uberschriftshierarchie (Kapitel/Abschnitt/Unterabschnitt)
[] Einheitliche Schrift und Gro?e
[] Korrekte Kopf- und Fu?zeilen
[] Fortlaufende Seitenzahlen
[] Fortlaufende Abbildungs-/Tabellennummerierung

Zitationsprufung:
[] Ubereinstimmung zwischen Textzitationen und Literaturverzeichnis
[] Einheitliches Zitationsformat (APA/MLA/IEEE/Chicago)
[] Ausreichende Anzahl an Referenzen

Logikprufung:
[] Jedes Kapitel beantwortet die Forschungsfragen
[] Schlussfolgerung beantwortet die Zusammenfassung
""Methoden stutzen die Schlussfolgerungen
""Keine Widerspruche

Haufige Probleme:
[] Zusammenfassung innerhalb der Wortgrenze
[] Schlussworter korrekt formatiert
""Abbildungen/Tabellen mit Titel
""Danksagung mit korrektem Betreuernamen
""Inhaltsverzeichnis stimmt mit Text uberein

Benotigen Sie eine punktweise Prufung?""",

            "config": """[Konfigurationsanleitung]

DeepSeek API Key konfigurieren:
1. Besuchen Sie https://platform.deepseek.com
2. Konto erstellen
3. Zur Seite "API Keys" gehen
4. Neuen Key erstellen (5 Millionen Token kostenlos)
5. Key kopieren (beginnt mit sk-)

Im Chat eingeben:
API Key konfigurieren: <YOUR_API_KEY>

Freischalten:
[OK] Unbegrenzte tiefgehende Analyse
[OK] Prazise logische Argumentation
[OK] Personalisierte wissenschaftliche Beratung

Aktueller Status: {status}""",

            "unknown": """Es tut mir leid, Ihre Anfrage ist nicht klar. Hier ist, was Sie tun konnen:

1. Beschreiben Sie Ihre Schreibphase:
   - [Ich wahle ein Thema]
   - [Ich erstelle die Gliederung]
   - [Ich schreibe den Haupttext]
   - [Ich bereite die Verteidigung vor]

2. Fugen Sie Absatze zur Uberprufung ein

3. Stellen Sie konkrete Fragen:
   - [Wie schreibe ich eine Literaturubersicht]
   - [Wie reduziere ich den Plagiatsgrad]
   - [Wie formatiere ich Zitationen]

4. Konfigurieren Sie den DeepSeek API Key fur intelligentere Antworten

Was mochten Sie tun?""",
        }

    def _get_spanish_defaults(self) -> Dict:
        """Respuestas predeterminadas en espanol"""
        return {
            "greeting": """¡Hola! Soy su asistente de redaccion de tesis. Puedo ayudarle con:

Proceso completo: Seleccion de tema -> Propuesta -> Esquema -> Redaccion -> Revision -> Verificacion de plagio -> Defensa
Asesoramiento especializado: Revision bibliografica, investigacion cuantitativa/cualitativa, reduccion de plagio, recomendacion de herramientas
Anotacion en tiempo real: Pegue sus parrafos de tesis para revision

En que etapa se encuentra?""",

            "topic_help": """[Diagnostico de seleccion de tema]

Por favor, indiqueme:
1. ¿Su area de estudio? (ej.: Informatica, Administracion, Educacion...)
2. ¿Licenciatura o Maestria?
3. ¿Tiene algun interes especifico? (no importa si no)

Recomendare 3-5 temas segun su situacion y evaluare la dificultad e innovacion.""",

            "outline_help": """[Construccion del esquema]

Por favor, proporcione:
1. Titulo de la tesis (o direccion aproximada)
2. Area de estudio
3. Tipo de grado (Licenciatura/Maestria)

Creare un esquema multinivel que incluya:
- Estructura de capitulos (3-4 niveles)
- Directrices de redaccion para cada seccion
- Proporcion de palabras sugerida
- Explicacion de las relaciones logicas""",

            "chapter_review_intro": """[Anotacion de capitulo]

He realizado una verificacion basica y encontrado los siguientes problemas:

{issues}

Consejo: Este es un analisis basico local. Para un analisis logico profundo y evaluacion de argumentacion, configure la clave API de DeepSeek.""",

            "proposal_help": """[Propuesta de investigacion]

Estructura estandar:
1. Antecedentes y significado (partir de problemas especificos)
2. Estado de la cuestion (revision clasificada + evaluacion)
3. Objetivos y contenido (especificos y medibles)
4. Metodos y mapa de ruta (metodos adecuados al problema)
5. Resultados esperados e innovaciones (explicar que es nuevo)
6. Plan y cronograma (dejar tiempo para revisiones)

Diganos su tema. Le ayudare a desarrollar cada seccion.""",

            "format_question": """[Normas de formato]

Requisitos de formato comunes:
- Titulos: Negrita, titulo nivel 1: 16pt, nivel 2: 14pt, nivel 3: 12pt
- Texto: Times New Roman, 12pt, interlineado 1.5
- Citas: APA/MLA/IEEE/Chicago (segun la disciplina)
- Margenes: 1 pulgada (2.54 cm) por lado
- Numeros de pagina: Pie de pagina central o exterior

¡Importante: Siga siempre la plantilla de su universidad!

¿Que parte necesita una explicacion detallada?""",

            "citation_question": """[Normas de citacion]

Formatos de citacion comunes:

APA 7ma edicion:
- Revista: Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.
- Libro: Author, A. A. (Year). Title of work. Publisher.

MLA 9na edicion:
- Author. "Title of Article." Journal Name, vol. #, no. #, Year, pp. #-#.

IEEE:
- [1] A. Author, "Title," Journal, vol. #, no. #, pp. #-#, Month Year.

Herramienta recomendada: Zotero (gratuito, excelente para gestion bibliografica)

¿Necesita ejemplos especificos o tutoriales?""",

            "methodology": """[Metodos de investigacion]

Investigacion cuantitativa (encuesta):
- Diseno de variables -> Cuestionario -> Piloto -> Encuesta completa -> Analisis de datos
- Herramientas: SPSS, AMOS, PROCESS, R
- Puntos clave: Fiabilidad (alpha > 0.7), Validez (KMO > 0.7)

Investigacion cualitativa (entrevistas/casos):
- Diseno de entrevista -> Recoleccion de datos -> Codificacion -> Extraccion de temas
- Herramientas: NVivo, Atlas.ti, MAXQDA
- Puntos clave: Triangulacion, verificacion por miembros

Digame su metodo de investigacion. Proporcionare una guia detallada.""",

            "defense_prep": """[Preparacion de la defensa]

Marco PPT (7 diapositivas):
1. Portada (Titulo + Nombre + Director)
2. Antecedentes de investigacion (1.5 min)
3. Objetivos y significado (1 min)
4. Metodos de investigacion (1.5 min)
5. Resultados (2.5 min, nucleo)
6. Conclusion y perspectivas (1 min)
7. Agradecimientos (0.5 min)

Modelo de discurso:
[Estimados miembros del tribunal, buenos dias. Mi nombre es XXX, especializado en XXX. Mi tesis se titula [XXX]. Hoy presentare mi investigacion en tres aspectos: los antecedentes, los metodos y los resultados...]

Preguntas frecuentes:
- ¿Cual es su innovacion?
- ¿Por que eligio este metodo?
- ¿Su muestra es suficiente?
- ¿Cuales son las limitaciones de su estudio?

¿Necesita una defensa simulada o modelos detallados?""",

            "plagiarism": """[Verificacion y reduccion de plagio]

Sistemas de deteccion:
- Turnitin (ampliamente usado internacionalmente)
- iThenticate (para investigadores/editores)
- Sistemas propios de la universidad

Principios de reduccion:
[OK] Efectivo: Reestructuracion de oraciones, adicion de datos/ejemplos, uso de figuras/tablas
[X] Inefectivo: Simple sustitucion de sinonimos, traduccion ida y vuelta, capturas de pantalla

Deteccion IA:
- Turnitin AI Detection
- GPTZero
- Recomendacion: Reescribir con sus propias palabras, no solo sustituir sinonimos

¿Necesita ejemplos especificos de reduccion?""",

            "literature_review": """[Revision bibliografica]

Metodo de 4 pasos:
1. Busqueda: Web of Science, Scopus, Google Scholar, bases de datos especificas
2. Seleccion: Leer titulo -> resumen -> conclusion, juzgar relevancia
3. Clasificacion: Por tema/metodo/perspectiva/cronologia
4. Evaluacion: Resumen + critica + identificacion de brechas

Marco de redaccion:
Ejemplo: Las investigaciones existentes han explorado principalmente bajo X perspectivas:
1. ... (Autor A, ano)
2. ... (Autor B, ano)
Sin embargo, las investigaciones existentes muestran limitaciones en XXX...

¿Necesita modelos o ejemplos especificos?""",

            "writing_guide": """[Redaccion academica]

Errores comunes:
[X] [Con el desarrollo de Internet...] -> [OK] [En el campo de XXX, los metodos tradicionales enfrentan desafios YYY...]
[X] [Yo creo que...] -> [OK] [La investigacion muestra...] / [Este estudio argumenta...]
[X] [Cada vez mejor] -> [OK] [Aumento del XX% al XX%]
[X] [Luego... Despues...] -> [OK] [Therefore... Furthermore... However...]

Estructura de parrafos:
- Un argumento central por parrafo
- Argumento -> Evidencia -> Analisis -> Conclusion
- Oracion tematica al inicio, transicion al final

¿Necesita ejemplos especificos de revision?""",

            "toolchain": """[Recomendaciones de herramientas]

Gestion bibliografica:
- Zotero (gratuito, recomendado)
- EndNote (licencias universitarias)
- Mendeley (buena gestion de PDF)

Herramientas de escritura:
- Word + Zotero (Ciencias sociales/humanidades)
- LaTeX/Overleaf (STEM, formulas)
- Google Docs (colaboracion)

Analisis de datos:
- SPSS (estadistica basica)
- R/Python (analisis avanzado)
- Stata (economia)
- NVivo (investigacion cualitativa)

Gestion del tiempo:
- Diagrama de Gantt (Excel/Project)
- Tecnica Pomodoro (25+5)
- Planificacion regresiva (desde fecha de defensa)

¿Necesita tutoriales especificos?""",

            "checklist": """[Verificacion antes del envio]

Verificacion de formato:
[] Jerarquia de titulos (capitulo/seccion/subseccion)
[] Fuente y tamano uniformes
[] Encabezados y pies de pagina correctos
[] Numeros de pagina continuos
[] Numeracion continua de figuras/tablas

Verificacion de citas:
[] Correspondencia entre citas en texto y lista de referencias
[] Formato de citacion uniforme (APA/MLA/IEEE/Chicago)
[] Numero suficiente de referencias

Verificacion logica:
[] Cada capitulo responde a las preguntas de investigacion
[] La conclusion responde al resumen
[] Los metodos sustentan las conclusiones
[] Sin contradicciones

Problemas comunes:
[] Resumen dentro del limite de palabras
[] Palabras clave correctamente formateadas
[] Figuras/tablas con titulo
[] Agradecimientos mencionando al director correcto
[] Indice coincide con el texto

¿Necesita verificacion punto por punto?""",

            "config": """[Guia de configuracion]

Configurar clave API de DeepSeek:
1. Visite https://platform.deepseek.com
2. Crear cuenta
3. Ir a la pagina "API Keys"
4. Crear nueva clave (5 millones de tokens gratis)
5. Copiar clave (comienza con sk-)

Ingrese en el chat:
Configurar API Key: <YOUR_API_KEY>

Desbloquear:
[OK] Analisis profundo ilimitado
[OK] Argumentacion logica precisa
[OK] Asesoramiento academico personalizado

Estado actual: {status}""",

            "unknown": """Lo siento, su solicitud no es clara. Esto es lo que puede hacer:

1. Describa su etapa de redaccion:
   - [Estoy eligiendo un tema]
   - [Estoy creando el esquema]
   - [Estoy redactando el texto principal]
   - [Estoy preparando la defensa]

2. Pegue parrafos para revision

3. Haga preguntas especificas:
   - [Como redactar una revision bibliografica]
   - [Como reducir el puntaje de plagio]
   - [Como formatear citas]

4. Configure la clave API de DeepSeek para respuestas mas inteligentes

¿Que desea hacer?""",
        }

    def get(self, key: str, **kwargs) -> str:
        """获取知识库内容"""
        content = self.default_knowledge.get(key, "")
        if kwargs:
            content = content.format(**kwargs)
        return content

    def load_file(self, path: str) -> str:
        """从文件加载知识(按需)"""
        return self._load_file(path)


class ConversationContext:
    """对话上下文管理器"""

    def __init__(self, max_history: int = 10):
        self.history = []  # 对话历史
        self.max_history = max_history
        self.user_profile = {}  # 用户画像
        self.current_state = {
            "discipline": None,      # 当前学科
            "subfield": None,        # 学科细分
            "level": None,           # 学位级别
            "stage": None,           # 当前阶段
            "topic": None,           # 选题方向
            "method": None,          # 研究方法
            "last_intent": None,     # 上一条意图
            "last_topic": None,      # 上一条主题
        }

    def add_message(self, role: str, content: str, intent: str = None):
        """添加对话记录"""
        self.history.append({
            "role": role,
            "content": content,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })

        # 限制历史长度
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def update_state(self, **kwargs):
        """更新对话状态"""
        for key, value in kwargs.items():
            if key in self.current_state and value is not None:
                self.current_state[key] = value

    def get_state(self, key: str) -> Optional[str]:
        """获取状态值"""
        return self.current_state.get(key)

    def get_all_state(self) -> Dict:
        """获取完整状态"""
        return self.current_state.copy()

    def get_history_summary(self) -> str:
        """获取对话历史摘要"""
        if not self.history:
            return ""

        # 提取最近3轮的关键信息
        recent = self.history[-6:]  # 最近6条(3轮)
        summary = []
        for msg in recent:
            if msg["role"] == "user":
                intent = msg.get("intent", "unknown")
                summary.append(f"用户[{intent}]: {msg['content'][:50]}...")
            else:
                summary.append(f"助手: {msg['content'][:50]}...")

        return "\n".join(summary)

    def get_related_context(self, current_intent: str) -> str:
        """获取与当前意图相关的上下文"""
        # 查找历史中的相关对话
        related = []
        for msg in self.history:
            if msg.get("intent") == current_intent and msg["role"] == "user":
                related.append(msg["content"])

        if related:
            return "相关历史:\n" + "\n".join(related[-3:])  # 最近3条相关
        return ""

    def set_user_profile(self, key: str, value: str):
        """设置用户画像"""
        self.user_profile[key] = value

    def get_user_profile(self, key: str) -> Optional[str]:
        """获取用户画像"""
        return self.user_profile.get(key)

    def save(self, file_path: str):
        """保存对话上下文到文件"""
        data = {
            "history": self.history,
            "user_profile": self.user_profile,
            "current_state": self.current_state,
            "max_history": self.max_history,
            "saved_at": datetime.now().isoformat()
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, file_path: str):
        """从文件加载对话上下文"""
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.history = data.get("history", [])
            self.user_profile = data.get("user_profile", {})
            self.current_state = data.get("current_state", self.current_state)
            return True
        except Exception as e:
            print(f"加载对话上下文失败: {e}")
            return False


class LocalAssistant:
    """本地助手 - 纯规则引擎(支持多轮对话)"""

    def __init__(self, knowledge_base: KnowledgeBase = None, context_file: str = None):
        self.kb = knowledge_base or KnowledgeBase()
        self.matcher = IntentMatcher(language=self.kb.language)
        self.context = ConversationContext()
        self.context_file = context_file

        # 如果指定了上下文文件，尝试加载
        if context_file and os.path.exists(context_file):
            self.context.load(context_file)

    def handle(self, user_input: str, user_config: Dict = None) -> Dict:
        """
        处理用户输入(支持多轮对话和多语言)

        返回: {
            "response": "回复内容",
            "type": "意图类型",
            "confidence": 置信度,
            "suggestions": ["建议"],
            "need_advanced": 是否需要高级AI,
            "context": 上下文信息
        }
        """
        # 0. 处理多语言配置
        if user_config:
            language = user_config.get("language", "zh")
            # 动态切换语言
            if language != self.matcher.language:
                self.matcher = IntentMatcher(language=language)
            if language != self.kb.language:
                self.kb.set_language(language)

        # 1. 意图识别
        intent = self.matcher.classify(user_input)

        # 2. 更新上下文
        self._update_context(user_input, intent)

        # 3. 根据意图处理
        handler_map = {
            "greeting": self._handle_greeting,
            "topic_help": self._handle_topic_help,
            "outline_help": self._handle_outline_help,
            "chapter_review": self._handle_chapter_review,
            "proposal_help": self._handle_proposal_help,
            "format_question": self._handle_format_question,
            "citation_question": self._handle_citation_question,
            "methodology": self._handle_methodology,
            "defense_prep": self._handle_defense_prep,
            "plagiarism": self._handle_plagiarism,
            "literature_review": self._handle_literature_review,
            "writing_guide": self._handle_writing_guide,
            "toolchain": self._handle_toolchain,
            "checklist": self._handle_checklist,
            "config": self._handle_config,
            "unknown": self._handle_unknown,
        }

        handler = handler_map.get(intent["type"], self._handle_unknown)
        result = handler(user_input, intent, user_config)

        # 4. 添加上下文信息
        result["context"] = {
            "discipline": self.context.get_state("discipline"),
            "subfield": self.context.get_state("subfield"),
            "level": self.context.get_state("level"),
            "stage": self.context.get_state("stage"),
            "topic": self.context.get_state("topic"),
            "history_count": len(self.context.history),
            "language": self.kb.language
        }

        # 5. 记录对话
        self.context.add_message("user", user_input, intent["type"])
        self.context.add_message(
            "assistant", result["response"], intent["type"])

        # 6. 自动保存上下文(如果配置了文件路径)
        if self.context_file:
            self.context.save(self.context_file)

        return result

    def _update_context(self, text: str, intent: Dict):
        """更新对话上下文"""
        # 提取学科
        discipline = self._extract_discipline(text)
        if discipline:
            self.context.update_state(discipline=discipline)

        # 提取学位级别
        level = self._extract_level(text)
        if level:
            self.context.update_state(level=level)

        # 提取阶段
        stage = self._extract_stage(text)
        if stage:
            self.context.update_state(stage=stage)

        # 更新最后意图
        self.context.update_state(last_intent=intent["type"])

    def _extract_stage(self, text: str) -> Optional[str]:
        """提取论文阶段"""
        stages = {
            "选题": ["选题", "选题目", "定题", "题目"],
            "开题": ["开题", "开题报告", "研究计划"],
            "大纲": ["大纲", "框架", "结构", "目录"],
            "写作": ["写作", "正文", "撰写", "草稿"],
            "修改": ["修改", "润色", "完善", "修订"],
            "查重": ["查重", "降重", "检测", "重复率"],
            "答辩": ["答辩", "预答辩", "毕业答辩"],
        }
        for stage, keywords in stages.items():
            if any(kw in text for kw in keywords):
                return stage
        return None

    def _handle_greeting(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理问候"""
        # 如果有上下文，提供个性化问候
        discipline = self.context.get_state("discipline")
        level = self.context.get_state("level")
        stage = self.context.get_state("stage")

        response = self.kb.get("greeting")

        if discipline or level or stage:
            response += f"\n\n[记住你的信息:"
            if discipline:
                response += f" {discipline}专业"
            if level:
                response += f" {level}"
            if stage:
                response += f" 当前阶段:{stage}"
            response += "]"

        return {
            "response": response,
            "type": "greeting",
            "confidence": intent["confidence"],
            "suggestions": ["帮我选题", "生成大纲", "检查论文段落"],
            "need_advanced": False
        }

    def _handle_topic_help(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理选题求助(支持多轮对话和学科细分)"""
        # 提取专业信息
        discipline = self._extract_discipline(text)
        level = self._extract_level(text)

        # 更新上下文
        if discipline:
            self.context.update_state(discipline=discipline)
        if level:
            self.context.update_state(level=level)

        # 检查是否有历史上下文
        prev_discipline = self.context.get_state("discipline")
        prev_level = self.context.get_state("level")

        response = self.kb.get("topic_help")

        # 如果有已知的学科信息，提供更精准的建议
        if prev_discipline:
            discipline_key = self._get_discipline_key(prev_discipline)
            discipline_knowledge = self.kb.get_discipline_knowledge(
                discipline_key)

            # 尝试匹配学科细分
            subdiscipline_match = self.kb.match_subdiscipline(
                text, discipline_key)
            if subdiscipline_match:
                sub_name = subdiscipline_match["name"]
                focus_areas = subdiscipline_match["focus"]
                response += f"\n\n检测到细分方向:**{sub_name}**"
                response += f"\n研究重点领域:{', '.join(focus_areas[:3])}"

                # 更新上下文
                self.context.update_state(subfield=sub_name)

            if discipline_knowledge:
                # 提取选题方向部分
                if "## 选题方向" in discipline_knowledge:
                    start = discipline_knowledge.find("## 选题方向")
                    end = discipline_knowledge.find("##", start + 1)
                    if end == -1:
                        end = len(discipline_knowledge)
                    topic_section = discipline_knowledge[start:end].strip()
                    response += f"\n\n[{prev_discipline}专业选题方向]\n{topic_section[:500]}..."

        # 构建个性化回复
        if prev_discipline or prev_level:
            response += f"\n\n检测到信息:"
            if prev_discipline:
                response += f" {prev_discipline}专业"
            if prev_level:
                response += f" {prev_level}"
            response += "\n\n请告诉我具体兴趣方向，我为你生成选题建议."

        return {
            "response": response,
            "type": "topic_help",
            "confidence": intent["confidence"],
            "suggestions": ["计算机专业", "商科专业", "教育专业", "法学专业"],
            "need_advanced": False,
            "extracted": {"discipline": discipline, "level": level}
        }

    def _handle_chapter_review(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理章节审查"""
        # 提取文本内容
        content = self._extract_text_content(text)

        if not content or len(content) < 50:
            return {
                "response": "请粘贴你要我检查的论文段落(建议200字以上)，我帮你分析基础问题.",
                "type": "chapter_review",
                "confidence": intent["confidence"],
                "suggestions": ["粘贴论文段落", "配置 API Key 进行深度分析"],
                "need_advanced": False
            }

        # 本地基础检查
        issues = self._basic_check(content)

        # 格式化问题
        issues_text = self._format_issues(issues)

        response = self.kb.get("chapter_review_intro", issues=issues_text)

        # 如果有复杂问题，建议高级分析
        has_complex = any(i["severity"] == "high" for i in issues)

        return {
            "response": response,
            "type": "chapter_review",
            "confidence": 0.75 if issues else 0.5,
            "suggestions": ["查看详细修改建议", "配置 API Key 进行深度分析"],
            "need_advanced": has_complex or len(content) > 1000,
            "issues_count": len(issues),
            "issues": issues
        }

    def _basic_check(self, text: str) -> List[Dict]:
        """基础文本检查"""
        issues = []

        # 1. 口语化检测
        oral_patterns = [
            ("我觉得", "学术写作避免使用'我觉得'，改为'研究表明'或'本文认为'"),
            ("挺好的", "避免口语化评价，改为具体描述或数据支撑"),
            ("很不错", "避免主观评价，提供客观数据或文献支撑"),
            ("非常好", "避免主观评价，提供客观数据或文献支撑"),
            ("随着...的发展", "避免陈词滥调，直接切入具体问题或研究背景"),
            ("众所周知", "避免空泛表述，引用具体文献支撑"),
            ("毫无疑问", "避免绝对化表述，学术写作应保持审慎"),
        ]

        for pattern, suggestion in oral_patterns:
            if pattern.replace("...", "") in text or pattern in text:
                issues.append({
                    "type": "oral_expression",
                    "severity": "medium",
                    "pattern": pattern,
                    "suggestion": suggestion,
                    "position": text.find(pattern.replace("...", "")) if pattern.replace("...", "") in text else text.find(pattern)
                })

        # 2. 格式问题
        if "\u3010" in text or "\u3011" in text:
            issues.append({
                "type": "format",
                "severity": "low",
                "message": "使用了中文方括号\u3010\u3011",
                "suggestion": "论文中建议使用英文括号[]或根据学校格式要求"
            })

        # 3. 段落长度
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        for i, para in enumerate(paragraphs):
            if len(para) > 800:
                issues.append({
                    "type": "structure",
                    "severity": "low",
                    "message": f"第{i+1}段过长({len(para)}字)",
                    "suggestion": "将长段落拆分为2-3个短段落，每段聚焦一个论点"
                })

        # 4. 弱逻辑连接词
        weak_connectors = [
            ("然后", "改为'因此','随后'或'在此基础上'"),
            ("接着", "改为'此外','同时'或'另一方面'"),
            ("还有", "改为'另外','此外'或'值得注意的是'"),
            ("另外", "注意上下文逻辑关系，确保真正是补充关系"),
        ]

        for connector, suggestion in weak_connectors:
            count = text.count(connector)
            if count > 0:
                issues.append({
                    "type": "logic",
                    "severity": "medium" if count > 2 else "low",
                    "message": f"使用了'{connector}'(出现{count}次)",
                    "suggestion": suggestion
                })

        # 5. 绝对化表述
        absolute_terms = [
            ("绝对", "改为'相对'或'在一定程度上'"),
            ("完全", "改为'基本'或'很大程度上'"),
            ("所有", "改为'多数'或'大部分'，除非有数据支撑"),
            ("一定", "改为'可能'或'在一定程度上'"),
            ("必然", "改为'很可能'或'具有较高概率'"),
        ]

        for term, suggestion in absolute_terms:
            if term in text:
                issues.append({
                    "type": "academic_tone",
                    "severity": "medium",
                    "message": f"使用了绝对化表述'{term}'",
                    "suggestion": suggestion
                })

        # 6. 缺乏数据支撑
        if any(x in text for x in ["显著", "明显", "大幅", "极大"]):
            if not any(x in text for x in ["%", "百分比", "数据", "统计", "p<", "p\u503c"]):
                issues.append({
                    "type": "evidence",
                    "severity": "high",
                    "message": "使用了'显著','明显'等评价词，但未提供数据支撑",
                    "suggestion": "补充具体数据，如'提升了XX%','p<0.05'等"
                })

        return issues

    def _format_issues(self, issues: List[Dict]) -> str:
        """格式化问题列表"""
        if not issues:
            return " \u672a\u68c0\u6d4b\u5230\u660e\u663e\u95ee\u9898\uff08\u57fa\u7840\u68c0\u67e5\u901a\u8fc7\uff09"

        severity_icons = {
            "high": "\u274c",
            "medium": "\u26a0\ufe0f",
            "low": "\ud83d\udca1"
        }

        lines = []
        for i, issue in enumerate(issues, 1):
            icon = severity_icons.get(issue["severity"], "\u26aa")
            lines.append(
                f"{icon} \u95ee\u9898{i}\uff08{issue['severity']}\uff09")
            lines.append(
                f"   \u7c7b\u578b\uff1a{issue.get('type', 'general')}")
            if "message" in issue:
                lines.append(f"   \u63cf\u8ff0\uff1a{issue['message']}")
            if "pattern" in issue:
                lines.append(f"   \u68c0\u6d4b\u5230\uff1a{issue['pattern']}")
            lines.append(
                f"   \u5efa\u8bae\uff1a{issue.get('suggestion', '\u8bf7\u68c0\u67e5\u5e76\u4fee\u6539')}")
            lines.append("")

        return "\n".join(lines)

    def _extract_discipline(self, text: str) -> Optional[str]:
        """提取专业方向"""
        disciplines = {
            "计算机": ["计算机", "软件", "人工智能", "AI", "大数据", "网络安全", "物联网", "数据科学"],
            "商科": ["商科", "管理", "营销", "市场", "人力资源", "MBA", "工商", "会计", "财务"],
            "教育": ["教育", "教学", "师范", "课程", "学习科学", "教育学", "高等教育", "职业教育"],
            "法学": ["法学", "法律", "司法", "立法", "合规", "刑法", "民法", "行政法"],
            "文学": ["文学", "语言", "汉语", "外语", "翻译", "语言学", "比较文学"],
            "传媒": ["传媒", "传播", "新闻", "广告", "影视", "新媒体", "数字媒体"],
            "艺术": ["艺术", "设计", "视觉", "音乐", "美术", "非遗", "艺术学"],
            "医学": ["医学", "临床", "药学", "公卫", "护理", "生物", "基础医学", "预防医学"],
            "经济": ["经济", "金融", "财政", "保险", "银行", "投资", "国际经济", "产业经济"],
            "工科": ["机械", "电子", "通信", "自动化", "土木", "化工", "材料", "能源", "环境", "航空航天"],
            "心理学": ["心理学", "心理", "认知", "发展心理学", "社会心理学", "临床心理学"],
            "社会学": ["社会学", "社会工作", "社会", "人类学", "人口学"],
            "政治学": ["政治", "国际关系", "外交", "公共管理", "行政管理"],
            "历史学": ["历史", "考古", "文博", "史学"],
            "哲学": ["哲学", "逻辑", "伦理", "宗教学"],
            "理学": ["数学", "物理", "化学", "生物", "地理", "天文", "统计学"],
            "农学": ["农学", "林学", "畜牧", "兽医", "水产", "农业经济"],
        }

        for discipline, keywords in disciplines.items():
            if any(kw in text for kw in keywords):
                return discipline
        return None

    def _get_discipline_key(self, discipline_name: str) -> str:
        """将专业名称映射到知识库键"""
        mapping = {
            "计算机": "cs", "软件": "cs", "人工智能": "cs", "AI": "cs", "大数据": "cs",
            "商科": "management", "管理": "management", "营销": "management", "市场": "management",
            "人力资源": "management", "MBA": "management", "工商": "management", "会计": "management", "财务": "management",
            "教育": "education", "教学": "education", "师范": "education", "课程": "education",
            "学习科学": "education", "教育学": "education", "高等教育": "education", "职业教育": "education",
            "法学": "law", "法律": "law", "司法": "law", "立法": "law", "合规": "law",
            "刑法": "law", "民法": "law", "行政法": "law",
            "文学": "literature", "语言": "literature", "汉语": "literature", "外语": "literature",
            "翻译": "literature", "语言学": "literature", "比较文学": "literature",
            "传媒": "media", "传播": "media", "新闻": "media", "广告": "media",
            "影视": "media", "新媒体": "media", "数字媒体": "media",
            "艺术": "art", "设计": "art", "视觉": "art", "音乐": "art", "美术": "art",
            "非遗": "art", "艺术学": "art",
            "医学": "medical", "临床": "medical", "药学": "medical", "公卫": "medical",
            "护理": "medical", "生物": "medical", "基础医学": "medical", "预防医学": "medical",
            "经济": "economics", "金融": "economics", "财政": "economics", "保险": "economics",
            "银行": "economics", "投资": "economics", "国际经济": "economics", "产业经济": "economics",
            "工科": "engineering", "机械": "engineering", "电子": "engineering", "通信": "engineering",
            "自动化": "engineering", "土木": "engineering", "化工": "engineering", "材料": "engineering",
            "能源": "engineering", "环境": "engineering", "航空航天": "engineering",
            "心理学": "psychology", "心理": "psychology", "认知": "psychology",
            "发展心理学": "psychology", "社会心理学": "psychology", "临床心理学": "psychology",
            "社会学": "sociology", "社会工作": "sociology", "社会": "sociology",
            "人类学": "sociology", "人口学": "sociology",
            "政治学": "politics", "政治": "politics", "国际关系": "politics",
            "外交": "politics", "公共管理": "politics", "行政管理": "politics",
            "历史学": "history", "历史": "history", "考古": "history", "文博": "history", "史学": "history",
            "哲学": "philosophy", "逻辑": "philosophy", "伦理": "philosophy", "宗教学": "philosophy",
            "理学": "science", "数学": "science", "物理": "science", "化学": "science",
            "生物": "science", "地理": "science", "天文": "science", "统计学": "science",
            "农学": "agriculture", "林学": "agriculture", "畜牧": "agriculture",
            "兽医": "agriculture", "水产": "agriculture", "农业经济": "agriculture",
        }
        return mapping.get(discipline_name, "general")

    def _extract_level(self, text: str) -> Optional[str]:
        """提取学位级别"""
        if "博士" in text or "PhD" in text or "phd" in text:
            return "博士"
        elif "硕士" in text or "研究生" in text or "master" in text.lower():
            return "硕士"
        elif "本科" in text or "学士" in text or "bachelor" in text.lower() or "毕业" in text:
            return "本科"
        return None

    def _extract_text_content(self, text: str) -> str:
        """提取用户粘贴的论文内容"""
        # 去除常见的引导语
        prefixes = [
            "帮我看看", "看看这段", "检查", "审查", "评价", "分析",
            "这段写得怎么样", "写得如何", "帮我分析", "请检查",
        ]

        content = text
        for prefix in prefixes:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()

        # 去除冒号
        if content.startswith(":") or content.startswith(":"):
            content = content[1:].strip()

        return content

    def _handle_outline_help(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理大纲求助"""
        # 检查是否有已知学科
        discipline = self.context.get_state("discipline")
        level = self.context.get_state("level")

        response = self.kb.get("outline_help")

        if discipline:
            response += f"\n\n检测到专业:{discipline}"
            if level:
                response += f" {level}"
            response += "\n\n请提供论文题目或大致方向，我为你生成大纲."

        return {
            "response": response,
            "type": "outline_help",
            "confidence": intent["confidence"],
            "suggestions": ["计算机专业", "商科专业", "教育专业", "法学专业"],
            "need_advanced": False
        }

    def _handle_proposal_help(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理开题求助"""
        return self._simple_response("proposal_help", intent, ["研究背景写法", "文献综述写法", "技术路线"])

    def _handle_format_question(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理格式问题"""
        return self._simple_response("format_question", intent, ["字体字号", "引用格式", "页边距设置"])

    def _handle_citation_question(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理引用问题"""
        return self._simple_response("citation_question", intent, ["GB/T 7714格式", "Zotero使用", "引用常见问题"])

    def _handle_methodology(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理方法问题"""
        return self._simple_response("methodology", intent, ["问卷设计", "SPSS分析", "访谈设计"])

    def _handle_defense_prep(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理答辩准备"""
        return self._simple_response("defense_prep", intent, ["PPT框架", "自述稿", "高频问题"])

    def _handle_plagiarism(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理查重问题"""
        return self._simple_response("plagiarism", intent, ["降重方法", "AI检测", "查重系统"])

    def _handle_literature_review(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理文献综述"""
        return self._simple_response("literature_review", intent, ["搜索策略", "分类方法", "述评写法"])

    def _handle_writing_guide(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理写作指导"""
        return self._simple_response("writing_guide", intent, ["学术用语", "段落结构", "常见错误"])

    def _handle_toolchain(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理工具推荐"""
        return self._simple_response("toolchain", intent, ["文献管理", "数据分析", "时间管理"])

    def _handle_checklist(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理检查清单"""
        return self._simple_response("checklist", intent, ["格式检查", "引用检查", "逻辑检查"])

    def _handle_config(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理配置"""
        has_key = config and config.get("api_key")
        status = "已配置" if has_key else "未配置"

        response = self.kb.get("config", status=status)

        return {
            "response": response,
            "type": "config",
            "confidence": intent["confidence"],
            "suggestions": ["配置 API Key", "了解功能"],
            "need_advanced": False
        }

    def _handle_unknown(self, text: str, intent: Dict, config: Dict) -> Dict:
        """处理未知意图"""
        # 检查是否有上下文可以帮助理解
        last_intent = self.context.get_state("last_intent")

        response = self.kb.get("unknown")

        if last_intent:
            response += f"\n\n你刚才在讨论:{last_intent}，继续这个话题吗?"

        return {
            "response": response,
            "type": "unknown",
            "confidence": intent["confidence"],
            "suggestions": ["帮我选题", "检查论文", "文献综述怎么写"],
            "need_advanced": False
        }

    def _simple_response(self, key: str, intent: Dict, suggestions: List[str]) -> Dict:
        """生成简单响应"""
        return {
            "response": self.kb.get(key),
            "type": intent["type"],
            "confidence": intent["confidence"],
            "suggestions": suggestions,
            "need_advanced": False
        }


if __name__ == "__main__":
    # 测试
    assistant = LocalAssistant()

    test_inputs = [
        "你好",
        "帮我选题，我是计算机专业的",
        "随着互联网的发展，深度学习越来越重要.我觉得这个方向挺好的.",
        "导师说论证不够，怎么改?",
        "文献综述怎么写?",
        "配置 API Key",
    ]

    for inp in test_inputs:
        print(f"\n{'='*50}")
        print(f"输入: {inp}")
        print(f"{'='*50}")
        result = assistant.handle(inp)
        print(f"意图: {result['type']}")
        print(f"置信度: {result['confidence']}")
        print(f"需要高级AI: {result['need_advanced']}")
        print(f"上下文: {result['context']}")
        print(f"回复:\n{result['response'][:200]}...")
