#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 目录定义
LOGS_DIR="logs"
LOG_FILE="$LOGS_DIR/app.log"
PID_FILE="$LOGS_DIR/app.pid"

# 确保日志目录存在
ensure_log_dir() {
    if [ ! -d "$LOGS_DIR" ]; then
        echo -e "${BLUE}Creating logs directory...${NC}"
        mkdir -p "$LOGS_DIR"
    fi
}

# 检查虚拟环境是否存在
check_venv() {
    if [ ! -d ".venv" ]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        uv venv
    fi
}

# 激活虚拟环境
activate_venv() {
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}Virtual environment not found!${NC}"
        exit 1
    fi
}

# 启动应用
start() {
    check_venv
    activate_venv
    ensure_log_dir
    
    # 检查是否已经在运行
    if [ -f "$PID_FILE" ]; then
        echo -e "${RED}Application is already running!${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Starting application...${NC}"
    nohup streamlit run src/astock_assistant/app.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo -e "${GREEN}Application started! PID: $(cat $PID_FILE)${NC}"
}

# 停止应用
stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${BLUE}Stopping application (PID: $PID)...${NC}"
        kill $PID
        rm "$PID_FILE"
        echo -e "${GREEN}Application stopped!${NC}"
    else
        echo -e "${RED}Application is not running!${NC}"
    fi
}

# 重启应用
restart() {
    stop
    sleep 2
    start
}

# 安装/更新依赖
setup() {
    check_venv
    activate_venv
    echo -e "${BLUE}Installing/updating dependencies...${NC}"
    uv sync --all-extras
    echo -e "${GREEN}Dependencies installed/updated!${NC}"
}

# 查看状态
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo -e "${GREEN}Application is running (PID: $PID)${NC}"
            echo -e "${BLUE}Log file: $LOG_FILE${NC}"
        else
            echo -e "${RED}Application crashed! Check $LOG_FILE for details${NC}"
            rm "$PID_FILE"
        fi
    else
        echo -e "${RED}Application is not running${NC}"
    fi
}

# 查看日志
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${RED}Log file not found!${NC}"
    fi
}

# 清理日志
clean() {
    echo -e "${BLUE}Cleaning logs...${NC}"
    if [ -d "$LOGS_DIR" ]; then
        rm -rf "$LOGS_DIR"/*
        echo -e "${GREEN}Logs cleaned!${NC}"
    else
        echo -e "${RED}Logs directory not found!${NC}"
    fi
}

# 命令行参数处理
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    setup)
        setup
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    clean)
        clean
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|setup|status|logs|clean}"
        exit 1
        ;;
esac

exit 0 