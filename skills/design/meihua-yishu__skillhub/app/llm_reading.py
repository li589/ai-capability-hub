"""AI 深度解读 — premium 档增值内容（¥1.99 版新增）

基于已起卦的真实结构化数据（本卦/体用/互卦/变卦/月令旺衰/五行生克/应期），
调用 LLM 生成千字级大师解读。LLM 失败时返回 None，调用方回退模板，不阻断交付。
"""
import asyncio
import json
import logging

import httpx

from app.config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)


def _build_prompt(data: dict) -> str:
    ben = data["ben_hex"]
    hu = data.get("hu_hex") or {}
    bian = data.get("bian_hex") or {}
    ti, yong = data["ti"], data["yong"]
    wx = data["wuxing"]
    pred = data.get("prediction", {})
    yearly = data.get("yearly") or {}

    lines = [
        "你是深研《梅花易数》的易学大师，师承邵雍一脉。请基于以下真实起卦数据，为问事人写一篇约500-800字的深度解读。",
        "",
        "【问事】" + data.get("question", ""),
        f"【本卦】{ben.get('name','')}（{ben.get('brief','')}），卦辞：{ben.get('judgment','')}，动爻：第{ben.get('dong_yao','')}爻",
        f"【体卦】{ti.get('gua','')}（{ti.get('element','')}，{ti.get('nature','')}，月令{ti.get('wangshuai','')}）",
        f"【用卦】{yong.get('gua','')}（{yong.get('element','')}，{yong.get('nature','')}，月令{yong.get('wangshuai','')}）",
        f"【体用生克】{wx.get('relation','')}，断语：{wx.get('desc','')}",
    ]
    if hu.get("name"):
        lines.append(f"【互卦】{hu['name']}（{hu.get('brief','')}）")
    if bian.get("name"):
        lines.append(f"【变卦】{bian.get('name')}（{bian.get('brief','')}）")
    if pred.get("timing"):
        lines.append(f"【应期】{pred['timing']}")
    if yearly.get("analysis"):
        lines.append(f"【流年】{yearly['analysis']}")

    lines += [
        "",
        "写作要求：",
        "1. 先用一句话给出总断（吉/凶/平及原因），语气笃定但谦和",
        "2. 逐层展开：本卦卦象与所问之事的对应 → 体用生克如何作用于事态 → 互卦揭示的过程波折 → 变卦预示的最终走向",
        "3. 结合动爻说明变化的关键节点",
        "4. 针对问事给出3条具体可操作的建议，并点明应期",
        "5. 语言典雅流畅，像一位老先生娓娓道来，不堆砌术语，普通人能看懂",
        "6. 必须贴合实际卦象数据推断，不得编造卦名、爻辞或五行关系",
        "7. 结尾注明：此解读基于传统易学文化，仅供娱乐参考",
    ]
    return "\n".join(lines)


async def ai_deep_reading(data: dict) -> str:
    """生成 AI 深度解读；LLM 不可用/失败时返回 None（调用方回退模板）"""
    if not DASHSCOPE_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            resp = await asyncio.wait_for(
                client.post(
                    f"{DASHSCOPE_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                    json={
                        "model": LLM_MODEL,
                        "messages": [{"role": "user", "content": _build_prompt(data)}],
                        "max_tokens": 1500,
                        "temperature": 0.7,
                    },
                ),
                timeout=70.0,
            )
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return text if len(text) >= 100 else None
    except Exception as e:
        logger.warning(f"AI深度解读失败（回退模板）: {e}")
        return None
