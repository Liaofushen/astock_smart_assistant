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

echo -e "${BLUE}Running code quality checks...${NC}"

# 运行各种代码检查工具
echo -e "\n${BLUE}Running black...${NC}"
black src tests

echo -e "\n${BLUE}Running isort...${NC}"
isort src tests

echo -e "\n${BLUE}Running flake8...${NC}"
flake8 src tests

echo -e "\n${BLUE}Running mypy...${NC}"
mypy src

echo -e "\n${GREEN}All quality checks completed!${NC}" 