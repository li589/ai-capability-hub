#!/usr/bin/env python3
"""
车系解读报告生成器 — 自包含 Python 脚本

用法：修改下方 SERIES_NAME，然后 `python generate_report.py`
输出：car_report.html

架构：
  1. 车系搜索接口（串行）→ 车系ID + 基础数据
  2. 口碑接口 + 价格接口（ThreadPoolExecutor 并行）
  3. build_radar_svg() 数学计算雷达图
  4. 内嵌 HTML 模板填充 → 写出文件

依赖：仅 Python 标准库（无需 pip install）
"""

import json
import urllib.request
import urllib.parse
import math
import datetime
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# 用户输入 — 替换此处车系名
# ============================================================
SERIES_NAME = "{{SERIES_NAME}}"

# ============================================================
# 输出文件
# ============================================================
OUTPUT_FILE = "car_report.html"

# ============================================================
# HTTP 工具
# ============================================================

def http_get(url, timeout=15):
    """发起 GET 请求并解析 JSON 响应"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except Exception as e:
        print(f"  [WARN] HTTP GET 失败: {url[:80]}... — {e}")
        return None

# ============================================================
# 价格转换
# ============================================================

def to_wan(val):
    """将原始价格（元）转为万，保留 2 位小数。返回 None 表示无数据"""
    if val is None:
        return None
    try:
        v = float(val)
        if v <= 0:
            return None
        return round(v / 10000, 2)
    except (TypeError, ValueError):
        return None

def fmt_wan(val, suffix="万"):
    """格式化价格字符串，如 '12.98万'，无数据返回 '暂无报价'"""
    w = to_wan(val)
    if w is None:
        return "暂无报价"
    return f"{w:.2f}{suffix}"

# ============================================================
# 销售状态映射
# ============================================================

def sale_status(state):
    """返回 (CSS类名, 显示文案)"""
    s = state if isinstance(state, int) else (int(state) if state is not None else None)
    if s == 0:
        return ("not-sale", "未售")
    elif s == 10:
        return ("coming-soon", "待售")
    elif s in (20, 30):
        return ("on-sale", "在售")
    elif s == 40:
        return ("off-sale", "停售")
    return ("", "")

def is_on_sale(state):
    """判断状态是否为在售（20 或 30）"""
    s = state if isinstance(state, int) else (int(state) if state is not None else None)
    return s in (20, 30)

# ============================================================
# 星级换算
# ============================================================

def stars_from_score(score):
    """口碑分 → 星级字符串"""
    if score is None:
        return ""
    s = float(score)
    if s >= 4.5:
        return "★★★★★"
    elif s >= 4.0:
        return "★★★★☆"
    elif s >= 3.5:
        return "★★★☆☆"
    else:
        return "★★☆☆☆"

# ============================================================
# 摘要生成（基于数据自动生成）
# ============================================================

def build_info_summary(series_name, level_name, price_range, sale_text, koubei_score):
    """生成基础信息模块的一句话总结"""
    parts = [f"{series_name}是一款{level_name}" if level_name else series_name]
    if price_range and price_range != "暂无报价":
        parts.append(f"指导价{price_range}")
    if sale_text:
        parts.append(f"目前{sale_text}状态")
    if koubei_score is not None:
        s = float(koubei_score)
        if s >= 4.5:
            parts.append("综合口碑表现出色")
        elif s >= 4.0:
            parts.append("综合口碑表现良好")
        else:
            parts.append("综合口碑尚可")
    if len(parts) <= 1:
        parts.append("具体信息详见下方详情")
    return "，".join(parts) + "。"

def build_review_summary(series_name, koubei_score, tags):
    """生成口碑模块的一句话总结"""
    if koubei_score is None:
        return f"<strong>{series_name}</strong>暂未收录足够用户口碑评价，待更多车主分享真实体验。"
    s = float(koubei_score)
    quality = ""
    if s >= 4.5:
        quality = "在同级别车型中口碑<strong>表现出色</strong>，"
    elif s >= 4.0:
        quality = "在同级别车型中口碑<strong>表现良好</strong>，"
    else:
        quality = ""
    tag_names = [t.get("label", "") for t in (tags or []) if t.get("label")]
    tag_text = ""
    if tag_names:
        tag_text = f"用户对{'、'.join(tag_names[:3])}等方面评价较高。"
    if s >= 4.0:
        suggestion = "适合注重综合品质的家庭用户考虑。"
    else:
        suggestion = "具体表现可参考下方详细评分。"
    return f"<strong>{series_name}</strong>{quality}综合口碑分为<strong>{s:.2f}</strong>分。{tag_text}{suggestion}"

# ============================================================
# API 调用
# ============================================================

def api_search(series_name):
    """
    车系搜索接口
    GET https://sou.api.autohome.com.cn/v1/search?&pid=90300023&ext={"q":"车系名"}
    """
    ext = json.dumps({"q": series_name}, ensure_ascii=False)
    url = f"https://sou.api.autohome.com.cn/v1/search?&pid=90300023&ext={urllib.parse.quote(ext)}"
    print(f"  [API] 车系搜索: {series_name}")
    data = http_get(url)
    if not data:
        return None

    items = data.get("result", {}).get("itemlist", [])
    for item in items:
        info = item.get("iteminfo", {})
        if info.get("id") != 144:
            continue
        d = info.get("data", {})
        if not d:
            continue

        # 车型列表
        models = []
        tags = d.get("tags", [])
        for tag in tags:
            if tag.get("type") == "specs":
                spec_list = tag.get("list", [])
                if spec_list:
                    inner = spec_list[0].get("list", [])
                    for spec in inner[:3]:
                        models.append({
                            "id": str(spec.get("id", "")),
                            "name": spec.get("name", ""),
                            "minprice": spec.get("minprice"),
                            "price": spec.get("price"),
                        })
                break

        # 竞品列表
        competitors = []
        for tag in tags:
            if tag.get("type") == "competing":
                car_list = tag.get("car_list", [])
                for car in car_list[:5]:
                    competitors.append({
                        "seriesId": car.get("seriesId", ""),
                        "seriesName": car.get("seriesName", ""),
                        "minPrice": car.get("minPrice"),
                        "maxPrice": car.get("maxPrice"),
                        "url": car.get("url", ""),
                    })
                break

        return {
            "seriesid": str(d.get("seriesid", "")),
            "seriesname": d.get("seriesname", series_name),
            "levelname": d.get("levelname", ""),
            "seriesminprice": d.get("seriesminprice"),
            "seriesmaxprice": d.get("seriesmaxprice"),
            "dealer_minOriginalPrice": d.get("dealer_minOriginalPrice"),
            "state": d.get("state"),
            "pnglogo": d.get("pnglogo", ""),
            "models": models,
            "competitors": competitors,
        }

    print("  [WARN] 未找到 id=144 的车系结果")
    return None


def api_koubei(series_id):
    """
    车系口碑接口
    GET https://koubeiipv6.app.autohome.com.cn/pc/series/list?seriesId=xxx
    """
    url = f"https://koubeiipv6.app.autohome.com.cn/pc/series/list?seriesId={series_id}"
    print(f"  [API] 车系口碑: seriesId={series_id}")
    data = http_get(url)
    if not data:
        return {"seriesAverage": None, "brandName": "", "tags": [], "radar": []}

    result = data.get("result") or {}

    # 口碑标签
    tags = []
    structured = result.get("structuredlist", [])
    for item in structured:
        if item.get("name") == "全部":
            summary = item.get("Summary", [])
            for s in summary:
                if s.get("Combination") == "全部":
                    continue
                tags.append({
                    "label": s.get("Combination", ""),
                    "volume": s.get("Volume", 0),
                })
                if len(tags) >= 6:
                    break
            break

    # 雷达分
    radar = []
    for s in result.get("seriesScoreList", [])[:7]:
        radar.append({
            "typeName": s.get("typeName", ""),
            "score": s.get("score", 0),
        })

    return {
        "seriesAverage": result.get("seriesAverage"),
        "brandName": result.get("brandName", ""),
        "tags": tags,
        "radar": radar,
    }


def api_price(series_id, spec_id):
    """
    车系价格接口
    GET https://www.autohome.com.cn/web-main/car/web/spec/getPriceInfo?seriesid=xxx&specid=yyy&cityid=110100
    """
    url = f"https://www.autohome.com.cn/web-main/car/web/spec/getPriceInfo?seriesid={series_id}&specid={spec_id}&cityid=110100"
    print(f"  [API] 车系价格: seriesId={series_id}, specId={spec_id}")
    data = http_get(url)
    if not data:
        return {"factory_items": [], "local_items": []}

    result = data.get("result") or {}
    butie = result.get("butie", {})

    # 厂商优惠
    factory_items = []
    factory = butie.get("factory", {})
    # 优先使用 labels 字段（如 ["2年0息", "动力总成终身质保"]）
    label_list = factory.get("labels", [])
    if label_list:
        factory_items = [str(l) for l in label_list[:3] if l]
    else:
        # 兜底：从 items 结构中提取
        for item in factory.get("items", [])[:3]:
            name = item.get("name") or item.get("label") or ""
            if name:
                factory_items.append(name)

    # 国家补贴
    local_items = []
    local = butie.get("local", {})
    for item in local.get("items", [])[:3]:
        subtitle = item.get("subtitle", "")
        amount = item.get("amount", "")
        if subtitle:
            local_items.append(f"{subtitle}，至高{amount}元")

    return {"factory_items": factory_items, "local_items": local_items}


# ============================================================
# 雷达图 SVG 生成（纯数学计算，无需手动推理）
# ============================================================

def build_radar_svg(scores, dimensions, cx=150, cy=140, R=100):
    """生成 n 边形雷达图 SVG。

    参数:
        scores:     各维度得分列表 (0-5)，如 [4.5, 4.2, 3.9, 4.8, 4.1, 3.7, 4.3]
        dimensions: 各维度名称列表，如 ['空间','配置','性价比','内饰','外观','油耗','驾驶感受']
        cx, cy:     中心坐标
        R:          满分半径
    """
    n = len(scores)
    if n < 3:
        return ""

    def point(radius, i):
        angle = -math.pi / 2 + i * 2 * math.pi / n  # 从顶部顺时针
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        return (round(x, 1), round(y, 1))

    # 5 圈同心背景网格
    grid_r = [20, 40, 60, 80, 100]
    grid_polygons = []
    for r in grid_r:
        pts = " ".join(f"{point(r, i)[0]},{point(r, i)[1]}" for i in range(n))
        grid_polygons.append(f'<polygon points="{pts}" fill="none" stroke="#e8eaed" stroke-width="1"/>')

    # 轴线
    axes = []
    for i in range(n):
        x, y = point(R, i)
        axes.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#e8eaed" stroke-width="1"/>')

    # 数据填充多边形
    data_pts = " ".join(f"{point(scores[i] / 5.0 * R, i)[0]},{point(scores[i] / 5.0 * R, i)[1]}" for i in range(n))
    data_poly = f'<polygon points="{data_pts}" fill="rgba(26,115,232,0.12)" stroke="#1a73e8" stroke-width="1.5" stroke-linejoin="round"/>'

    # 数据点
    dots = []
    for i in range(n):
        x, y = point(scores[i] / 5.0 * R, i)
        dots.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#1a73e8"/>')

    # 维度标签（向外偏移）
    labels = []
    for i in range(n):
        x, y = point(R + 18, i)
        labels.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="12" fill="#5f6368" font-family="PingFang SC,Microsoft YaHei,sans-serif">{dimensions[i] if i < len(dimensions) else ""}</text>'
        )

    # 分数标签（贴近数据点内侧，避免与维度标签重叠）
    score_labels = []
    for i in range(n):
        data_r = scores[i] / 5.0 * R
        offset_r = max(8, data_r - 12)  # 向内偏移12px，最小8px
        x, y = point(offset_r, i)
        score_labels.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="11" fill="#1a73e8" font-weight="600">{scores[i]:.2f}</text>'
        )

    svg_parts = grid_polygons + axes + [data_poly] + dots + labels + score_labels
    svg = f'<svg viewBox="0 0 300 300" width="300" height="300" xmlns="http://www.w3.org/2000/svg">\n  ' + "\n  ".join(svg_parts) + "\n</svg>"
    return svg


# ============================================================
# HTML 模板（内嵌多行字符串）
# ============================================================

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RAV4荣放 车系解读报告</title>
<style>
  :root{--primary:#1a73e8;--primary-light:#e8f0fe;--success:#34a853;--danger:#ea4335;--warning:#fbbc04;--text-primary:#202124;--text-secondary:#5f6368;--text-light:#80868b;--bg-page:#f8f9fa;--bg-card:#ffffff;--border:#e0e0e0;--shadow:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.06);--radius:12px;--radius-sm:8px}
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg-page);color:var(--text-primary);line-height:1.6;-webkit-font-smoothing:antialiased}
  .container{max-width:800px;margin:0 auto;padding:20px 16px 40px}
  .report-title{text-align:center;margin-bottom:16px}
  .report-title h1{font-size:24px;font-weight:700;letter-spacing:-.3px}
  .report-title h1 span{color:var(--primary)}
  .info-card{background:var(--bg-card);border-radius:var(--radius);padding:20px 24px;margin-bottom:20px;box-shadow:var(--shadow)}
  .info-header{display:flex;align-items:flex-start;gap:16px;margin-bottom:14px}
  .info-header-text{flex:1;min-width:0}
  .info-series-name{font-size:22px;font-weight:700;letter-spacing:-.5px;margin-bottom:4px;display:flex;align-items:center;gap:8px}
  .info-series-img-wrap{width:120px;flex-shrink:0}
  .info-series-img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:var(--radius-sm);background:var(--bg-page);display:block}
  .info-series-img-placeholder{width:100%;aspect-ratio:4/3;border-radius:var(--radius-sm);background:var(--bg-page);border:1px dashed var(--border);display:none;align-items:center;justify-content:center;font-size:11px;color:var(--text-light)}
  .info-summary{font-size:14px;color:var(--text-secondary);line-height:1.7;margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid var(--border)}
  .info-summary strong{color:var(--primary)}
  .info-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-bottom:14px}
  .info-meta-item{text-align:center;padding:8px 4px;border-right:1px solid var(--border)}
  .info-meta-item:last-child{border-right:none}
  .info-meta-item .meta-label{font-size:12px;color:var(--text-light);margin-bottom:4px}
  .info-meta-item .meta-val{font-size:15px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .info-meta-item .meta-val.highlight{color:var(--primary)}
  .info-link{display:block;text-align:center;font-size:13px;color:var(--primary);text-decoration:none}
  .section{background:var(--bg-card);border-radius:var(--radius);padding:24px;margin-bottom:20px;box-shadow:var(--shadow)}
  .section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--border)}
  .section-title{font-size:18px;font-weight:700;display:flex;align-items:center;gap:8px}
  .section-title .icon{width:28px;height:28px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-size:15px}
  .section-link{font-size:13px;color:var(--primary);text-decoration:none;display:inline-flex;align-items:center;gap:4px}
  .section-link::after{content:"\203A";font-size:16px;font-weight:600}
  .section-summary{padding:12px 14px;border-radius:var(--radius-sm);font-size:13px;line-height:1.6;margin-bottom:18px}
  .section-summary strong{font-weight:600}
  .section-summary.review-summary{background:var(--primary-light);color:var(--text-secondary);border-left:3px solid var(--primary)}
  .section-summary.review-summary strong{color:var(--primary)}
  .sale-status{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500}
  .sale-status.on-sale{background:#e6f4ea;color:#1e7e34}
  .sale-status.off-sale{background:#f5f5f5;color:#888}
  .sale-status.not-sale{background:#fce8e6;color:#c62828}
  .sale-status.coming-soon{background:#fff3e0;color:#e65100}
  .model-item{display:grid;grid-template-columns:1fr 90px 100px 36px;align-items:center;gap:16px;padding:14px 16px;border-radius:var(--radius-sm);background:var(--bg-page)}
  .model-item:hover{background:var(--primary-light)}
  .model-name{font-size:14px;font-weight:600}
  .model-price-col{text-align:right}
  .model-price-val{font-size:14px;font-weight:700;color:var(--danger);white-space:nowrap}
  .model-price-val.dealer{color:var(--primary)}
  .model-view-all{display:block;text-align:center;margin-top:14px;padding:10px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;color:var(--primary);text-decoration:none}
  .dealer-price-row{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-radius:var(--radius-sm);background:var(--bg-page);margin-bottom:14px}
  .dealer-price-row .dealer-label{font-size:14px;color:var(--text-secondary)}
  .dealer-price-row .dealer-value{font-size:20px;font-weight:700;color:var(--danger)}
  .dealer-price-row .dealer-note{font-size:11px;color:var(--text-light);margin-top:2px}
  .discount-group{display:flex;flex-direction:column;gap:10px;margin-bottom:14px}
  .discount-row{display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap}
  .discount-row-label{font-size:13px;color:var(--text-secondary);font-weight:500;white-space:nowrap;padding-top:1px;min-width:56px}
  .discount-row-tags{display:flex;flex-wrap:wrap;gap:8px}
  .discount-tag{display:inline-flex;align-items:center;gap:5px;padding:5px 12px;border-radius:6px;font-size:13px;font-weight:500}
  .discount-tag.manufacturer{background:#fff3e0;color:#e65100;border:1px solid #ffe0b2}
  .discount-tag.national{background:#e8f5e9;color:#2e7d32;border:1px solid #c8e6c9}
  .discount-notice{font-size:11px;color:var(--text-light);line-height:1.6;padding:8px 10px;background:var(--bg-page);border-radius:6px;border-left:2px solid var(--border);margin-top:4px}
  .review-layout{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}
  .review-score-block{display:flex;align-items:flex-end;gap:8px;margin-bottom:18px}
  .review-score-num{font-size:48px;font-weight:800;color:var(--warning);line-height:1}
  .review-score-stars{font-size:16px;color:var(--warning);letter-spacing:1px;padding-bottom:2px}
  .review-score-source{font-size:11px;color:var(--text-light);margin-top:2px}
  .review-tag-list{display:flex;flex-wrap:wrap;gap:8px}
  .review-tag-item{display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border-radius:16px;background:#e8f0fe;font-size:13px;color:var(--primary);font-weight:500}
  .review-tag-count{font-size:11px;color:var(--text-light);font-weight:400;margin-left:2px}
  .review-radar-side{display:flex;flex-direction:column;align-items:center}
  .radar-title{font-size:12px;color:var(--text-light);margin-bottom:4px}
  .competitor-list{display:flex;flex-direction:column;gap:10px}
  .competitor-item{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-radius:var(--radius-sm);background:var(--bg-page);text-decoration:none;color:inherit;gap:16px}
  .competitor-item:hover{background:var(--primary-light)}
  .competitor-rank{width:26px;height:26px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;flex-shrink:0}
  .competitor-rank.top3{background:#f57c00}
  .competitor-img{width:80px;height:60px;border-radius:6px;object-fit:contain;flex-shrink:0;background:#fff;padding:4px}
  .competitor-img-placeholder{display:none;width:80px;height:60px;border-radius:6px;background:#fff;align-items:center;justify-content:center;font-size:11px;color:#80868b;flex-shrink:0}
  .competitor-name{font-weight:600;font-size:15px}
  .competitor-price{font-weight:600;font-size:15px;color:var(--primary);white-space:nowrap}
  .competitor-arrow{font-size:18px;color:var(--text-light);margin-left:4px;flex-shrink:0}
  .report-footer{text-align:center;padding:20px;font-size:12px;color:var(--text-light);line-height:1.6}
  .report-footer a{color:var(--primary);text-decoration:none}
  @media(max-width:600px){.report-title h1{font-size:20px}.info-series-name{font-size:18px}.info-series-img-wrap{width:90px}.review-layout{grid-template-columns:1fr}.info-meta{grid-template-columns:repeat(3,1fr)}.info-meta-item:nth-child(n+4){border-top:1px solid var(--border)}.section{padding:18px}.model-item{grid-template-columns:1fr auto auto}.model-item .model-price-col:last-of-type{display:none}}
</style>
</head>
<body>
<div class="container">

  <div class="report-title"><h1><span>RAV4荣放</span> 车系解读报告</h1></div>

  <!-- 1. 基础信息 -->
  <div class="info-card">
    <div class="info-header">
      <div class="info-header-text">
        <div class="info-series-name">RAV4荣放 <span class="sale-status {{SALE_STATUS_CLASS}}">{{SALE_STATUS_TEXT}}</span></div>
        <div class="info-summary">
          {{INFO_SUMMARY}}
        </div>
      </div>
      <div class="info-series-img-wrap">
        <img class="info-series-img" src="{{SERIES_IMAGE}}" alt="RAV4荣放" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
        <div class="info-series-img-placeholder">暂无图片</div>
      </div>
    </div>
    <div class="info-meta">
      <div class="info-meta-item"><div class="meta-label">品牌</div><div class="meta-val">{{BRAND}}</div></div>
      <div class="info-meta-item"><div class="meta-label">指导价</div><div class="meta-val highlight">{{PRICE_RANGE}}</div></div>
      <div class="info-meta-item"><div class="meta-label">车系级别</div><div class="meta-val">{{LEVEL_NAME}}</div></div>
      <div class="info-meta-item"><div class="meta-label">口碑分</div><div class="meta-val highlight">{{KOUBEI_SCORE}}</div></div>
    </div>
    <a class="info-link" href="https://www.autohome.com.cn/{{SERIES_ID}}#pvareaid=6885686" target="_blank" rel="noopener noreferrer">查看车系详情 &#8250;</a>
  </div>

  <!-- 2. 车型列表 -->
  <div class="section">
    <div class="section-header">
      <div class="section-title"><span class="icon" style="background:#e8f0fe;color:#1a73e8;">&#x1F697;</span>车型列表</div>
    </div>
    <div class="model-item" style="background:transparent;padding:4px 16px;font-size:12px;color:var(--text-light);font-weight:500;border-bottom:1px solid var(--border);margin-bottom:4px;">
      <span>车型名称</span><span style="text-align:right;">指导价（万）</span><span style="text-align:right;">经销商价&#183;北京</span><span></span>
    </div>
    <div class="model-list" style="display:flex;flex-direction:column;gap:4px;">
      {{MODEL_ROWS}}
    </div>
    <a class="model-view-all" href="https://www.autohome.com.cn/{{SERIES_ID}}#pvareaid=6885686" target="_blank" rel="noopener noreferrer">查看全部车型 &#8250;</a>
  </div>

  <!-- 3. 用户口碑 -->
  <div class="section">
    <div class="section-header">
      <div class="section-title"><span class="icon" style="background:#fce8e6;color:#ea4335;">&#x1F4AC;</span>用户口碑</div>
      <a class="section-link" href="https://k.autohome.com.cn/{{SERIES_ID}}#pvareaid=6885686" target="_blank" rel="noopener noreferrer">查看口碑详情</a>
    </div>
    <div class="section-summary review-summary">
      {{REVIEW_SUMMARY}}
    </div>
    <div class="review-layout">
      <div class="review-score-side">
        <div class="review-score-block">
          <div class="review-score-num">{{KOUBEI_SCORE}}</div>
          <div>
            <div class="review-score-stars">{{STARS_DISPLAY}}</div>
            <div class="review-score-source">汽车之家用户口碑分</div>
          </div>
        </div>
        <div class="review-tag-list">
          {{REVIEW_TAGS}}
        </div>
      </div>
      <div class="review-radar-side">
        <div class="radar-title">综合能力雷达（满分 5 分）</div>
        {{RADAR_SVG}}
      </div>
    </div>
  </div>

  <!-- 4. 经销商报价&优惠 -->
  <div class="section">
    <div class="section-header">
      <div class="section-title"><span class="icon" style="background:#fff3e0;color:#e65100;">&#x1F4B0;</span>经销商报价&amp;优惠（参考北京）</div>
      {{PROMO_LINK}}
    </div>
    <div class="dealer-price-row">
      <div>
        <div class="dealer-label">经销商报价</div>
        <div class="dealer-note">实际价格以当地经销商为准</div>
      </div>
      <div class="dealer-value">{{DEALER_PRICE}}</div>
    </div>
    <div class="discount-group">
      <div class="discount-row">
        <span class="discount-row-label">厂商优惠：</span>
        <div class="discount-row-tags">
          {{MANUFACTURER_DISCOUNTS}}
        </div>
      </div>
      <div class="discount-row">
        <span class="discount-row-label">国家补贴：</span>
        <div class="discount-row-tags">
          {{NATIONAL_SUBSIDIES}}
        </div>
      </div>
    </div>
    <div class="discount-notice">信息仅供参考，政府实际补贴金额以最终发票成交价为准来计算，实际厂商优惠以官方公布的最新信息为准。</div>
  </div>

  <!-- 5. 同级竞品 -->
  {{COMPETITOR_SECTION}}

  <div class="report-footer">
    数据来源：汽车之家 &nbsp;&#183;&nbsp; 报告生成时间：{{REPORT_DATE}}<br>
    内容由 AI 生成，更多数据可访问 <a href="https://www.autohome.com.cn/" target="_blank" rel="noopener noreferrer">汽车之家</a> 查询
  </div>
</div>
</body>
</html>"""


# ============================================================
# HTML 片段生成
# ============================================================

def build_model_rows(models, series_id):
    """生成车型列表 HTML 片段"""
    if not models:
        return '<div style="padding:20px;text-align:center;color:var(--text-light);">暂无车型数据</div>'

    rows = []
    for m in models:
        mid = m.get("id", "")
        mname = m.get("name", "未知车型")
        guide = fmt_wan(m.get("minprice"))
        dealer = fmt_wan(m.get("price"))
        rows.append(
            f'<div class="model-item">'
            f'<div class="model-name">{mname}</div>'
            f'<div class="model-price-col"><div class="model-price-val">{guide}</div></div>'
            f'<div class="model-price-col"><div class="model-price-val dealer">{dealer}</div></div>'
            f'<a href="https://www.autohome.com.cn/spec/{mid}#pvareaid=6885686" target="_blank" rel="noopener noreferrer" style="font-size:12px;color:var(--primary);text-decoration:none;white-space:nowrap;">详情&#8250;</a>'
            f'</div>'
        )
    return "\n".join(rows)


def build_review_tags(tags):
    """生成口碑标签 HTML 片段"""
    if not tags:
        return '<span style="color:var(--text-light);font-size:13px;">暂无用户评价</span>'

    items = []
    for t in tags:
        label = t.get("label", "")
        vol = t.get("volume", 0)
        if not label:
            continue
        vol_str = f'<span class="review-tag-count">{vol}人评</span>' if vol else ""
        items.append(f'<span class="review-tag-item">{label}{vol_str}</span>')
    return "\n".join(items) if items else '<span style="color:var(--text-light);font-size:13px;">暂无用户评价</span>'


def build_discount_tags(items, cls):
    """生成优惠/补贴标签 HTML 片段"""
    if not items:
        return '<span style="color:var(--text-light);font-size:13px;">暂无</span>'
    return "\n".join(f'<span class="discount-tag {cls}">{item}</span>' for item in items)


def build_competitor_rows(competitors):
    """生成竞品行 HTML 片段"""
    if not competitors:
        return ""

    rows = []
    for idx, c in enumerate(competitors):
        rank = idx + 1
        rank_cls = ' top3' if rank <= 3 else ''
        sid = c.get("seriesId", "")
        sname = c.get("seriesName", "未知")
        img_url = c.get("url", "")
        min_p = to_wan(c.get("minPrice"))
        max_p = to_wan(c.get("maxPrice"))

        # 价格
        if min_p is not None and max_p is not None:
            if min_p == max_p:
                price_str = f"{min_p:.2f}万"
            else:
                price_str = f"{min_p:.2f}-{max_p:.2f}万"
        elif min_p is not None:
            price_str = f"{min_p:.2f}万"
        else:
            price_str = "暂无报价"

        rows.append(
            f'<a class="competitor-item" href="https://www.autohome.com.cn/{sid}#pvareaid=6885686" target="_blank" rel="noopener noreferrer">'
            f'<span class="competitor-rank{rank_cls}">{rank}</span>'
            f'<img class="competitor-img" src="{img_url}" alt="{sname}" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
            f'<div class="competitor-img-placeholder">暂无图片</div>'
            f'<div style="flex:1;"><div class="competitor-name">{sname}</div></div>'
            f'<div class="competitor-price">{price_str}</div>'
            f'<span class="competitor-arrow">&#8250;</span>'
            f'</a>'
        )
    return "\n".join(rows)


def build_competitor_section(competitors):
    """生成竞品模块 HTML（不足 2 个则返回空字符串）"""
    if not competitors or len(competitors) < 2:
        return ""
    rows_html = build_competitor_rows(competitors)
    return f"""  <!-- 5. 同级竞品 -->
  <div class="section">
    <div class="section-header">
      <div class="section-title"><span class="icon" style="background:#f3e5f5;color:#9c27b0;">&#x1F3C6;</span>同级竞品车</div>
    </div>
    <div class="competitor-list">
      {rows_html}
    </div>
  </div>"""


# ============================================================
# 占位符替换
# ============================================================

def fill_template(search_data, koubei_data, price_data):
    """将所有占位符替换为实际数据，返回完整 HTML"""
    s = search_data
    k = koubei_data
    p = price_data

    sid = s["seriesid"]
    sname = s["seriesname"]
    first_spec_id = str(s["models"][0]["id"]) if s["models"] else ""

    # 价格范围
    min_w = to_wan(s["seriesminprice"])
    max_w = to_wan(s["seriesmaxprice"])
    if min_w is not None and max_w is not None:
        price_range = f"{min_w:.2f}-{max_w:.2f}万" if min_w != max_w else f"{min_w:.2f}万"
    elif min_w is not None:
        price_range = f"{min_w:.2f}万"
    else:
        price_range = "暂无报价"

    # 销售状态
    status_cls, status_text = sale_status(s["state"])
    if not status_text:
        status_text_markup = ""
    else:
        status_text_markup = f'<span class="sale-status {status_cls}">{status_text}</span>'

    # 经销商价
    dealer_w = to_wan(s["dealer_minOriginalPrice"])
    dealer_price = f"{dealer_w:.2f}万起" if dealer_w else "暂无报价"

    # 口碑分
    kscore = k["seriesAverage"]
    if kscore == "" or kscore is None:
        kscore = None
    kscore_display = f"{float(kscore):.2f}" if kscore is not None else "暂无"

    # 雷达图
    if k["radar"] and len(k["radar"]) >= 3:
        radar_scores = [item["score"] for item in k["radar"]]
        radar_dims = [item["typeName"] for item in k["radar"]]
        radar_svg = build_radar_svg(radar_scores, radar_dims)
    else:
        radar_svg = '<div style="padding:40px;color:var(--text-light);text-align:center;">暂无雷达数据</div>'

    # 摘要
    info_summary = build_info_summary(sname, s["levelname"], price_range, status_text, kscore)
    review_summary = build_review_summary(sname, kscore, k["tags"])

    # 替换
    html = HTML_TEMPLATE
    html = html.replace("RAV4荣放", sname)
    html = html.replace("{{SALE_STATUS_CLASS}}", status_cls)
    html = html.replace("{{SALE_STATUS_TEXT}}", status_text)

    # 修复：带 sale-status 的 span 需要特殊处理
    html = html.replace(
        f'{sname} <span class="sale-status {{SALE_STATUS_CLASS}}">{{SALE_STATUS_TEXT}}</span>',
        f'{sname} {status_text_markup}'
    )

    html = html.replace("{{INFO_SUMMARY}}", info_summary)
    html = html.replace("{{SERIES_IMAGE}}", s["pnglogo"] or "")
    html = html.replace("{{BRAND}}", k["brandName"] or "暂无")
    html = html.replace("{{PRICE_RANGE}}", price_range)
    html = html.replace("{{LEVEL_NAME}}", s["levelname"] or "暂无")
    html = html.replace("{{KOUBEI_SCORE}}", kscore_display)
    html = html.replace("{{SERIES_ID}}", sid)
    html = html.replace("{{FIRST_SPEC_ID}}", first_spec_id)
    html = html.replace("{{MODEL_ROWS}}", build_model_rows(s["models"], sid))
    html = html.replace("{{REVIEW_SUMMARY}}", review_summary)
    html = html.replace("{{STARS_DISPLAY}}", stars_from_score(kscore))
    html = html.replace("{{REVIEW_TAGS}}", build_review_tags(k["tags"]))
    html = html.replace("{{RADAR_SVG}}", radar_svg)
    html = html.replace("{{DEALER_PRICE}}", dealer_price)
    html = html.replace("{{MANUFACTURER_DISCOUNTS}}", build_discount_tags(p["factory_items"], "manufacturer"))
    html = html.replace("{{NATIONAL_SUBSIDIES}}", build_discount_tags(p["local_items"], "national"))

    # 优惠链接（仅状态为在售 20/30 时显示）
    if is_on_sale(s["state"]) and first_spec_id:
        promo_link = f'<a class="section-link" href="https://www.autohome.com.cn/cars/startingprice/{sid}-{first_spec_id}.html/#pvareaid=6885686" target="_blank" rel="noopener noreferrer">查看完整优惠信息</a>'
    else:
        promo_link = ""
    html = html.replace("{{PROMO_LINK}}", promo_link)

    html = html.replace("{{REPORT_DATE}}", datetime.date.today().strftime("%Y-%m-%d"))

    # 竞品模块（不足 2 个则整个隐藏）
    comp_section = build_competitor_section(s["competitors"])
    html = html.replace("{{COMPETITOR_SECTION}}", comp_section)

    # 清理未替换的模板占位符（以防万一）
    for ph in ["{{SALE_STATUS_TEXT}}", "{{SALE_STATUS_CLASS}}"]:
        html = html.replace(ph, "")

    return html


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print(f"  车系解读报告生成器")
    print(f"  车系: {SERIES_NAME}")
    print("=" * 60)

    # ---- Step 1: 车系搜索（串行）----
    print("\n[Step 1/3] 搜索车系...")
    search_data = api_search(SERIES_NAME)

    if not search_data:
        print("\n[ERROR] 未能识别车系，请检查车系全称是否正确。")
        sys.exit(1)

    sid = search_data["seriesid"]
    sname = search_data["seriesname"]
    first_spec_id = str(search_data["models"][0]["id"]) if search_data["models"] else ""
    print(f"  -> 车系: {sname} (ID: {sid})")
    print(f"  -> 车型数: {len(search_data['models'])}, 竞品数: {len(search_data['competitors'])}")

    # ---- Step 2: 口碑 + 价格（并行）----
    print("\n[Step 2/3] 并行获取口碑 & 价格数据...")
    koubei_data = None
    price_data = {"factory_items": [], "local_items": []}

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_koubei = executor.submit(api_koubei, sid)
        if first_spec_id:
            f_price = executor.submit(api_price, sid, first_spec_id)
        else:
            print("  [WARN] 无车型ID，跳过价格接口")

        for future in as_completed([f_koubei] + ([f_price] if first_spec_id else [])):
            try:
                result = future.result()
                if future == f_koubei:
                    koubei_data = result
                elif first_spec_id and future == f_price:
                    price_data = result
            except Exception as e:
                print(f"  [ERROR] 并行请求失败: {e}")

    if koubei_data is None:
        koubei_data = {"seriesAverage": None, "brandName": "", "tags": [], "radar": []}
    if price_data is None:
        price_data = {"factory_items": [], "local_items": []}

    print(f"  -> 口碑分: {koubei_data.get('seriesAverage', 'N/A')}")
    print(f"  -> 优惠标签: {len(price_data.get('factory_items', []))}, 补贴标签: {len(price_data.get('local_items', []))}")

    # ---- 数据充足性检查 ----
    # 如果口碑和价格数据都为空，说明该车系数据不足，不生成报告
    koubei_score = koubei_data.get("seriesAverage")
    koubei_empty = (
        not koubei_score and  # 处理 None 和空字符串 ''
        len(koubei_data.get("tags", [])) == 0 and
        len(koubei_data.get("radar", [])) == 0
    )
    price_empty = (
        len(price_data.get("factory_items", [])) == 0 and
        len(price_data.get("local_items", [])) == 0
    )
    
    if koubei_empty and price_empty:
        print("\n[WARN] 口碑和价格数据均为空，数据不足，无法生成有价值的报告。")
        print("[DATA_INSUFFICIENT]")
        sys.exit(2)

    # ---- Step 3: 填充模板 & 输出 ----
    print("\n[Step 3/3] 生成 HTML 报告...")
    html = fill_template(search_data, koubei_data, price_data)

    output_path = os.path.join(os.getcwd(), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  -> 报告已保存: {output_path}")
    print(f"  -> 文件大小: {len(html):,} 字节")
    print("\n" + "=" * 60)
    print(f"  完成! 打开 {OUTPUT_FILE} 查看报告")
    print("=" * 60)


if __name__ == "__main__":
    main()
