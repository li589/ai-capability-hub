#!/bin/bash
# ==============================================
# 自我迭代Skill · 部署运行脚本（.sh）
# 版本：v1.0
# 用途：技能平台部署、启动、重启、停止、日志查看
# 适配Linux环境，可直接上传执行
# ==============================================

# 技能名称（与上传文件保持一致）
SKILL_NAME="lobster_self_iteration"
# 技能运行目录（默认当前目录，可根据平台要求修改）
SKILL_DIR=$(cd $(dirname $0); pwd)
# 日志文件路径
LOG_FILE="${SKILL_DIR}/${SKILL_NAME}.log"
# Python执行路径（根据平台环境修改，默认python3）
PYTHON_EXEC="python3"
# 核心运行文件
PY_FILE="${SKILL_DIR}/${SKILL_NAME}.py"

# 日志输出函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# ==============================================
# 1. 部署技能（首次上传后执行）
# ==============================================
deploy() {
    log "开始部署龙虾自我迭代Skill..."
    # 检查核心文件是否存在
    if [ ! -f $PY_FILE ]; then
        log "部署失败：核心文件${PY_FILE}不存在，请确认上传完整"
        echo "部署失败：核心文件不存在"
        exit 1
    fi
    if [ ! -f "${SKILL_DIR}/${SKILL_NAME}.txt" ] || [ ! -f "${SKILL_DIR}/${SKILL_NAME}.md" ]; then
        log "警告：说明文件缺失，不影响运行，但建议补充上传"
        echo "警告：说明文件缺失，建议补充上传"
    fi

    # 赋予脚本执行权限
    chmod +x $0
    log "脚本执行权限赋予成功"

    # 检查Python环境
    if ! command -v $PYTHON_EXEC &> /dev/null; then
        log "部署失败：未找到Python环境，请检查Python路径配置"
        echo "部署失败：未找到Python环境"
        exit 1
    fi

    # 安装依赖（若有）
    log "检查并安装依赖..."
    $PYTHON_EXEC -m pip install --upgrade pip >> $LOG_FILE 2>&1
    # 本Skill无额外依赖，若后续新增依赖，可在此添加安装命令
    # pip install xxx >> $LOG_FILE 2>&1

    log "部署完成！可执行 ./$0 start 启动技能"
    echo "部署完成！"
}

# ==============================================
# 2. 启动技能
# ==============================================
start() {
    log "开始启动自我迭代Skill..."
    # 检查技能是否已启动
    if pgrep -f $PY_FILE &> /dev/null; then
        log "技能已处于运行状态，无需重复启动"
        echo "技能已在运行中！"
        exit 0
    fi

    # 后台启动技能，输出日志到指定文件
    nohup $PYTHON_EXEC $PY_FILE >> $LOG_FILE 2>&1 &
    sleep 3

    # 检查启动是否成功
    if pgrep -f $PY_FILE &> /dev/null; then
        log "技能启动成功，进程ID：$(pgrep -f $PY_FILE)"
        echo "技能启动成功！进程ID：$(pgrep -f $PY_FILE)"
    else
        log "技能启动失败，请查看日志文件：$LOG_FILE"
        echo "启动失败，请查看日志：$LOG_FILE"
        exit 1
    fi
}

# ==============================================
# 3. 停止技能
# ==============================================
stop() {
    log "开始停止自我迭代Skill..."
    # 查找技能进程ID
    PID=$(pgrep -f $PY_FILE)
    if [ -z "$PID" ]; then
        log "技能未运行，无需停止"
        echo "技能未运行！"
        exit 0
    fi

    # 停止进程
    kill -9 $PID
    sleep 2

    # 检查停止是否成功
    if pgrep -f $PY_FILE &> /dev/null; then
        log "技能停止失败，强制终止进程"
        kill -9 $PID
        echo "技能强制停止成功！"
    else
        log "技能停止成功，进程ID：$PID"
        echo "技能停止成功！"
    fi
}

# ==============================================
# 4. 重启技能
# ==============================================
restart() {
    log "开始重启龙虾自我迭代Skill..."
    stop
    sleep 3
    start
    log "技能重启完成"
    echo "技能重启完成！"
}

# ==============================================
# 5. 查看技能状态
# ==============================================
status() {
    if pgrep -f $PY_FILE &> /dev/null; then
        echo "自我迭代Skill 运行中"
        echo "进程ID：$(pgrep -f $PY_FILE)"
        echo "日志路径：$LOG_FILE"
        log "查看技能状态：运行中"
    else
        echo "自我迭代Skill 未运行"
        log "查看技能状态：未运行"
    fi
}

# ==============================================
# 6. 查看日志
# ==============================================
logs() {
    echo "正在查看自我迭代Skill日志（按Ctrl+C退出）..."
    tail -f $LOG_FILE
}

# ==============================================
# 脚本入口（参数判断）
# ==============================================
if [ $# -eq 0 ]; then
    echo "请输入操作指令，用法："
    echo "  ./$0 deploy    部署技能（首次上传后执行）"
    echo "  ./$0 start     启动技能"
    echo "  ./$0 stop      停止技能"
    echo "  ./$0 restart   重启技能"
    echo "  ./$0 status    查看技能状态"
    echo "  ./$0 logs      查看运行日志"
    exit 1
fi

case $1 in
    deploy)
        deploy
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "无效指令！请输入正确指令（deploy/start/stop/restart/status/logs）"
        log "无效指令：$1"
        exit 1
        ;;
esac
