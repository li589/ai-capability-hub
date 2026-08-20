#!/bin/bash
# qclaw 电脑清理技能 一键安装脚本
# 适配系统：macOS、Linux
# 功能：复制技能文件到qclaw skills目录（无需安装依赖，零依赖设计）

# 颜色定义（提升可读性）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 重置颜色

echo -e "${YELLOW}=== 开始安装 qclaw 电脑清理技能（零依赖版） ===${NC}"

# 1. 检查Python是否安装（技能基于Python标准库，需确保Python已安装）
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}错误：未检测到Python，请先安装Python（无需安装任何依赖包）${NC}"
    exit 1
fi

# 2. 查找qclaw skills目录（适配常见安装路径）
SKILLS_PATHS=(
    "~/.qclaw/skills"
    "~/qclaw/skills"
    "~/Library/Application Support/qclaw/skills" # macOS
    "~/.config/qclaw/skills" # Linux
)

TARGET_PATH=""
for path in "${SKILLS_PATHS[@]}"; do
    EXPANDED_PATH=$(eval echo $path)
    if [ -d "$EXPANDED_PATH" ]; then
        TARGET_PATH=$EXPANDED_PATH
        break
    fi
done

# 3. 若未找到skills目录，提示用户手动指定
if [ -z "$TARGET_PATH" ]; then
    echo -e "${YELLOW}未自动找到qclaw skills目录，请手动输入skills目录路径（例如：/Users/xxx/.qclaw/skills）${NC}"
    read -p "请输入skills目录路径：" TARGET_PATH
    if [ ! -d "$TARGET_PATH" ]; then
        echo -e "${RED}错误：输入的路径不存在，请确认路径正确${NC}"
        exit 1
    fi
fi

# 4. 复制技能文件到skills目录
echo -e "${GREEN}正在复制技能文件到：$TARGET_PATH${NC}"
if [ -f "computer_clean_skill.py" ]; then
    cp computer_clean_skill.py "$TARGET_PATH/"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}技能文件复制完成！${NC}"
    else
        echo -e "${RED}技能文件复制失败，请手动将computer_clean_skill.py复制到skills目录${NC}"
        exit 1
    fi
else
    echo -e "${RED}错误：未找到computer_clean_skill.py文件，请确保脚本与.py文件在同一目录${NC}"
    exit 1
fi

# 5. 安装完成提示（强调零依赖、文本交互）
echo -e "\n${GREEN}=== 安装完成！${NC}"
echo -e "${YELLOW}请重启 qclaw 助手，输入以下文本指令即可使用：${NC}"
echo -e "  - 帮我清理电脑垃圾"
echo -e "  - 深度清理电脑"
echo -e "  - 清理Docker缓存"
echo -e "\n${YELLOW}✅ 提示：本技能为零依赖设计，无需安装任何第三方包，敏感项将通过文本确认交互${NC}"
echo -e "${YELLOW}若使用Windows系统，请手动将.py文件放入qclaw的skills目录，重启即可使用${NC}"