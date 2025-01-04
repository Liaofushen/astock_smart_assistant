#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}Virtual environment not found!${NC}"
    exit 1
fi

# 参数处理
coverage_report=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --coverage) coverage_report=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${BLUE}Running tests...${NC}"

if [ "$coverage_report" = true ]; then
    # 运行测试并生成覆盖率报告
    pytest tests/ --cov=src --cov-report=html --cov-report=term
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
else
    # 只运行测试
    pytest tests/
fi 