#!/bin/bash
# HealthCheck Dashboard API Server 启动脚本
# 版本: 4.0.0

set -e

API_DIR="${HOME}/.openclaw/healthcheck/api"
API_PORT=8888
LOG_FILE="${API_DIR}/api.log"
PID_FILE="${API_DIR}/api.pid"

# 初始化API目录
init_api() {
    if [ ! -d "$API_DIR" ]; then
        mkdir -p "$API_DIR"
        echo "✅ API目录已创建: $API_DIR"
    fi
}

# 启动API服务器
start_api() {
    echo "🚀 启动API服务器..."
    
    # 检查是否已在运行
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "❌ API服务器已在运行 (PID: $(cat $PID_FILE))"
        echo ""
        echo "使用 './api.sh stop' 停止服务器"
        return 1
    fi
    
    cd "$API_DIR" && nohup python3 -m uvicorn api:app --host 0.0.0.0 --port "$API_PORT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    echo "✅ API服务器已启动在 $API_PORT 端口"
    echo "   PID: $(cat $PID_FILE)"
    echo "   日志: $LOG_FILE"
}

# 停止API服务器
stop_api() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ API服务器未运行"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    echo "正在停止API服务器 (PID: $pid)..."
    kill $pid 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "✅ API服务器已停止"
}

# API状态
api_status() {
    if pgrep -f "uvicorn.*api:app" > /dev/null 2>&1; then
        echo "✅ API服务器运行中 (端口: $API_PORT)"
        return 0
    else
        echo "❌ API服务器未运行"
        return 1
    fi
}

# 显示帮助
show_help() {
    cat << EOF
HealthCheck Dashboard API Server v4.0.0

用法: $0 [命令] [参数]

命令:
  init                  初始化API目录和文件
  start                 启动API服务器
  stop                  停止API服务器
  status                查看API服务状态
  help                  显示此帮助

示例:
  # 初始化
  ./api.sh init
  
  # 启动
  ./api.sh start
  
  # 查看状态
  ./api.sh status
  
  # 停止
  ./api.sh stop

端口: $API_PORT (默认8888)
日志: $LOG_FILE
EOF
}

# 主函数
main() {
    init_api
    
    case "${1:-start}" in
        start)
            start_api
            ;;
        stop)
            stop_api
            ;;
        status)
            api_status
            ;;
        init)
            echo "✅ API目录已初始化"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "❌ 未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
