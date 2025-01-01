# 构建阶段
FROM python:3.13-slim as builder

WORKDIR /app

# 使用 root 用户执行安装命令
USER root

# 配置 apt 镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 配置 pip 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装系统依赖和 ta-lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xvzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib-0.4.0-src.tar.gz ta-lib/

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY pyproject.toml README.md ./
COPY src ./src

# 使用 uv 安装依赖
RUN uv sync

# 运行阶段
FROM python:3.13-slim

WORKDIR /app

# 复制构建阶段的所有 Python 包
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# 创建非 root 用户
RUN useradd --system --create-home appuser \
    && chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 复制源代码
COPY src ./src

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=production

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "src/astock_assistant/app.py"] 