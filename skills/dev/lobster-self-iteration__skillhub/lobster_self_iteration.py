# ==============================================
# 自我迭代 Skill · 核心运行文件（.py版本）
# 版本：v1.0
# 核心能力：规则迭代(生效) + 代码自动修改 + 闭环自动迭代 + 迭代评分
# 适配技能平台Python运行环境，可直接上传运行
# ==============================================

import json
import time
import threading
from datetime import datetime

# 全局缓存：自动迭代定时器、当前代码备份
iteration_timer = None
code_backup = ""  # 备份原始代码，防止迭代出错

# ==============================================
# 基础配置（meta信息，适配技能平台）
# ==============================================
meta = {
    "id": "lobster_self_iteration_ultimate",
    "name": "自我迭代",
    "description": "规则自动生效+代码自我修改+闭环自动迭代+迭代评分，真正自我进化",
    "version": "1.0",
    "author": "技能开发者",
    "trigger": [
        "龙虾迭代", "开始迭代", "自我进化", "复盘对话", "升级龙虾",
        "查看迭代规则", "清空迭代", "持续迭代", "停止迭代",
        "查看迭代评分", "强制优化代码"
    ]
}

# ==============================================
# 工具函数：提取文本指定段落（通用）
# ==============================================
def extract_section(text, title):
    lines = text.split("\n")
    res = []
    capture = False
    for line in lines:
        if line.startswith(title):
            capture = True
            continue
        # 遇到下一个标题或空行，停止捕获
        if capture and (line.startswith("【") or line.strip() == ""):
            break
        if capture and line.strip() != "":
            res.append(line.strip())
    return "\n".join(res) or "暂无相关内容"

# ==============================================
# 工具函数：提取迭代评分
# ==============================================
def extract_score(text):
    import re
    score_match = re.search(r"【迭代评分】\s*(\d+(?:\.\d+)?)", text)
    return float(score_match.group(1)) if score_match else 6.0  # 默认6分

# ==============================================
# 工具函数：提取评分说明
# ==============================================
def extract_score_desc(text):
    import re
    desc_match = re.search(r"【迭代评分】\s*\d+(?:\.\d+)?分\s*\((.*?)\)", text)
    return desc_match.group(1).strip() if desc_match else "未标注评分说明"

# ==============================================
# 核心1：执行一次完整迭代（规则+代码+评分）
# ==============================================
async def do_iteration(ctx, messages, memory, skill):
    recent_chat = messages[-15:] if len(messages) >= 15 else messages  # 取最近15轮对话复盘
    old_rules = memory.get("lobster_rules") or "无"
    old_code = skill.get("code") or ""
    old_ver = float(memory.get("iter_ver") or "1.0")
    new_ver = round(old_ver + 0.1, 1)

    # 首次运行备份原始代码
    global code_backup
    if not code_backup:
        code_backup = old_code
        memory.set("code_backup", old_code)

    # 迭代提示词（新增：评分要求、代码自动修改要求）
    prompt = f"""
你是一只自我迭代的AI龙虾，必须严格按格式输出，不要多余内容，确保代码可直接运行。

核心要求：
1. 评分：按「迭代质量」打1-10分（10分最优），结合规则合理性、代码优化实用性评分
2. 代码修改：生成可直接替换的完整代码片段（只改需要优化的部分，保留原有核心逻辑）
3. 规则：必须贴合最近对话问题，确保后续对话能生效

最近对话：
{json.dumps(recent_chat, ensure_ascii=False, indent=2)}

当前行为规则：
{old_rules}

当前Skill代码片段（需优化）：
{old_code[:1200]}...

请严格按以下格式输出，缺一不可：
【优点】1. 2. 3.（每条简洁具体）
【问题】1. 2. 3.（每条对应具体对话/代码问题）
【新行为规则】1. 2. 3. 4.（3-6条，可直接生效）
【代码优化建议】1. 2.（简洁明了，对应代码问题）
【优化后代码片段】（可直接替换原有对应代码，保留语法正确，无需多余注释）
【迭代评分】1-10分（标注分数+1句评分说明）
【迭代版本】v{new_ver}
    """.strip()

    # AI生成迭代结果（含评分、优化代码）
    ai_res = await ctx.llm.chat({
        "messages": [{"role": "user", "content": prompt}]
    })

    # 提取各部分内容（工具函数处理）
    new_rules = extract_section(ai_res, "【新行为规则】")
    optimized_code = extract_section(ai_res, "【优化后代码片段】")
    score = extract_score(ai_res)
    score_desc = extract_score_desc(ai_res)

    # 代码自动修改（核心：替换原有代码，保留meta等关键信息）
    if optimized_code and optimized_code.strip() != "":
        await update_skill_code(skill, old_code, optimized_code)

    # 保存迭代数据（版本、规则、评分、历史）
    memory.set("iter_ver", new_ver)
    memory.set("lobster_rules", new_rules)
    iteration_history = memory.get("iter_history") or []
    iteration_history.append({
        "ver": new_ver,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": ai_res,
        "score": score,
        "scoreDesc": score_desc
    })
    memory.set("iter_history", iteration_history)

    # 评分过低（<6分）自动重新优化一次
    if score < 6:
        await force_code_optimize(ctx, memory, skill)
        return {
            "text": f"🦞 迭代完成 · v{new_ver}\n\n" +
                    ai_res +
                    f"\n\n⚠️  本次迭代评分较低（<6分），已自动触发二次优化！" +
                    "\n✅ 新规则、优化后代码已生效"
        }

    # 正常返回结果
    return {
        "text": f"🦞 迭代完成 · v{new_ver}\n\n" +
                ai_res +
                "\n\n✅ 新规则、优化后代码已自动生效，后续对话将严格遵守！"
    }

# ==============================================
# 核心2：规则自动生效（影响后续所有对话）
# ==============================================
async def before_chat(ctx, memory, messages):
    rules = memory.get("lobster_rules")
    if not rules:
        return

    # 注入系统提示，强制遵守迭代后的规则
    messages.insert(0, {
        "role": "system",
        "content": f"你是一只会自我迭代的AI龙虾，必须严格遵守以下迭代规则，不可违背：\n{rules}"
    })

# ==============================================
# 核心3：代码自动修改（AI生成代码→自动替换）
# ==============================================
async def update_skill_code(skill, old_code, optimized_code):
    try:
        # 核心逻辑：替换原有代码中对应优化部分，保留meta、全局缓存等关键内容
        # 避免替换核心配置，防止Skill崩溃
        new_code = old_code

        # 匹配代码片段（根据AI生成的优化片段，定位替换位置）
        if "do_iteration" in optimized_code:
            import re
            new_code = re.sub(
                r"async do_iteration\({[^}]+}\s*\{[^}]+}\)",
                optimized_code,
                new_code,
                flags=re.DOTALL
            )
        elif "auto_iteration_loop" in optimized_code:
            import re
            new_code = re.sub(
                r"async auto_iteration_loop\({[^}]+}\s*\{[^}]+}\)",
                optimized_code,
                new_code,
                flags=re.DOTALL
            )
        elif "before_chat" in optimized_code:
            import re
            new_code = re.sub(
                r"async before_chat\({[^}]+}\s*\{[^}]+}\)",
                optimized_code,
                new_code,
                flags=re.DOTALL
            )
        else:
            # 通用替换：如果无法定位，替换非核心函数片段
            import re
            new_code = re.sub(
                r"# ==============================================[\s\S]*?# ==============================================",
                optimized_code,
                new_code,
                flags=re.DOTALL
            )

        # 自动更新Skill代码（核心：实现代码级自我迭代）
        skill["code"] = new_code
        return True
    except Exception as e:
        # 代码替换失败，恢复备份
        global code_backup
        skill["code"] = code_backup or memory.get("code_backup")
        return False

# ==============================================
# 核心4：闭环自动迭代（每20轮对话自动进化）
# ==============================================
async def auto_iteration_loop(ctx, memory, skill, enable):
    global iteration_timer
    if not enable:
        # 停止自动迭代
        if iteration_timer:
            iteration_timer.cancel()
            iteration_timer = None
        return {"text": "🛑 龙虾已停止自动迭代，保留当前迭代状态"}

    # 已在运行中，无需重复开启
    if iteration_timer:
        return {"text": "✅ 正在持续自动迭代中：每20轮对话自动进化一次"}

    # 开启定时器：每3秒检测一次对话次数，每20轮触发一次迭代
    async def check_and_iterate():
        while True:
            chat_count = memory.get("chat_count") or 0
            # 每20轮对话，执行一次完整迭代
            if chat_count % 20 == 0 and chat_count != 0:
                await do_iteration(ctx, [], memory, skill)
            # 更新对话计数
            memory.set("chat_count", chat_count + 1)
            await asyncio.sleep(3)

    iteration_timer = threading.Thread(target=asyncio.run, args=(check_and_iterate(),))
    iteration_timer.start()

    return {"text": "✅ 开启持续迭代模式！\n规则：每20轮对话自动复盘→评分→优化代码→生效规则"}

# ==============================================
# 核心5：查看所有迭代评分
# ==============================================
async def show_scores(memory):
    history = memory.get("iter_history") or []
    if not history:
        return {"text": "📊 暂无迭代评分，先执行「龙虾迭代」开启进化吧！"}

    score_list = [f"v{item['ver']}（{item['time']}）：{item['score']}分 → {item['scoreDesc']}" for item in history]
    score_list_str = "\n".join(score_list)
    max_score = max([item["score"] for item in history])

    return {
        "text": f"📊 迭代评分历史（共{len(history)}次）\n" +
                "========================================\n" +
                score_list_str +
                f"\n========================================\n" +
                f"当前最高评分：{max_score}分"
    }

# ==============================================
# 核心6：强制优化代码（手动触发二次优化）
# ==============================================
async def force_code_optimize(ctx, memory, skill):
    old_code = skill.get("code") or ""
    old_rules = memory.get("lobster_rules") or "无"
    prompt = f"""
你是自我迭代的代码优化助手，专注于修复代码问题、优化逻辑，确保代码可直接运行。

当前Skill代码：
{old_code[:1200]}...

当前行为规则：
{old_rules}

优化要求：
1. 不改变原有核心功能（规则生效、自动迭代、评分）
2. 修复代码语法错误、逻辑漏洞，提升运行稳定性
3. 优化代码简洁度，减少冗余，无需多余注释
4. 输出「优化后完整代码片段」，可直接替换原有代码

输出格式：
【优化后代码片段】（完整可运行，只保留核心函数优化部分）
【优化说明】（1-2句说明优化点）
    """.strip()

    ai_res = await ctx.llm.chat({
        "messages": [{"role": "user", "content": prompt}]
    })

    optimized_code = extract_section(ai_res, "【优化后代码片段】")
    if optimized_code and optimized_code.strip() != "":
        await update_skill_code(skill, old_code, optimized_code)
        return {
            "text": "🔧 强制代码优化完成！\n\n" +
                    ai_res +
                    "\n\n✅ 优化后代码已自动生效"
        }

    return {"text": "🔧 强制优化失败，未生成有效代码片段，请重试「强制优化代码」"}

# ==============================================
# 工具函数：查看当前生效规则
# ==============================================
async def show_rules(memory):
    rules = memory.get("lobster_rules") or "暂无迭代规则"
    ver = memory.get("iter_ver") or "1.0"
    return {
        "text": f"📜 当前迭代规则（v{ver}）\n" +
                "========================================\n" +
                rules +
                "\n========================================\n" +
                "提示：后续对话会严格遵守以上规则"
    }

# ==============================================
# 工具函数：清空所有迭代数据（重置）
# ==============================================
async def clear_iteration(memory, skill):
    # 清空记忆中的迭代数据
    memory.delete("iter_ver")
    memory.delete("lobster_rules")
    memory.delete("iter_history")
    memory.delete("chat_count")
    memory.delete("code_backup")
    # 恢复原始代码
    global code_backup
    if code_backup:
        skill["code"] = code_backup
    # 停止自动迭代
    global iteration_timer
    if iteration_timer:
        iteration_timer.cancel()
        iteration_timer = None
    return {"text": "🧹 已清空所有迭代记录、规则和评分，恢复初始状态！"}

# ==============================================
# 主入口：指令分发
# ==============================================
async def run(ctx, messages, memory, config, skill):
    user_msg = messages[-1]["content"].strip() if messages else ""

    # 指令分流
    if "查看迭代规则" in user_msg:
        return await show_rules(memory)
    if "清空迭代" in user_msg:
        return await clear_iteration(memory, skill)
    if "持续迭代" in user_msg:
        return await auto_iteration_loop(ctx, memory, skill, enable=True)
    if "停止迭代" in user_msg:
        return await auto_iteration_loop(ctx, memory, skill, enable=False)
    if "查看迭代评分" in user_msg:
        return await show_scores(memory)
    if "强制优化代码" in user_msg:
        return await force_code_optimize(ctx, memory, skill)

    # 默认执行一次完整迭代（含评分+代码优化）
    return await do_iteration(ctx, messages, memory, skill)

# 技能平台入口注册
if __name__ == "__main__":
    import asyncio
    # 模拟运行测试
    class MockContext:
        class LLM:
            async def chat(self, params):
                return """【优点】1. 对话复盘准确 2. 规则贴合需求 3. 代码优化合理
【问题】1. 代码替换逻辑可优化 2. 评分说明不够详细 3. 规则生效延迟
【新行为规则】1. 复盘对话取最近15轮，确保针对性 2. 代码优化后立即生效 3. 评分说明需包含具体优化点 4. 避免重复回复
【代码优化建议】1. 优化代码替换正则匹配逻辑 2. 增加评分异常处理
【优化后代码片段】async update_skill_code(skill, old_code, optimized_code):
    try:
        new_code = old_code
        import re
        if "do_iteration" in optimized_code:
            new_code = re.sub(r"async do_iteration\({[^}]+}\s*\{[^}]+}", optimized_code, new_code, flags=re.DOTALL)
        skill["code"] = new_code
        return True
    except Exception as e:
        skill["code"] = code_backup
        return False
【迭代评分】8分（代码优化合理，规则针对性强，评分说明需补充）
【迭代版本】v1.1"""
        llm = LLM()

    class MockMemory:
        def __init__(self):
            self.data = {}
        def get(self, key):
            return self.data.get(key)
        def set(self, key, value):
            self.data[key] = value
        def delete(self, key):
            if key in self.data:
                del self.data[key]
        def append(self, key, value):
            if key not in self.data:
                self.data[key] = []
            self.data[key].append(value)

    mock_ctx = MockContext()
    mock_memory = MockMemory()
    mock_skill = {"code": __file__}
    mock_messages = [{"role": "user", "content": "龙虾迭代"}]

    asyncio.run(run(mock_ctx, mock_messages, mock_memory, {}, mock_skill))
