# 构建阶段
FROM python:3.13 as builder

# 编译安装 ta-lib
WORKDIR /build
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xvzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install

# 安装 Python 依赖
RUN pip install uv
WORKDIR /app
COPY pyproject.toml ./
# 先编译依赖，再安装
RUN uv pip compile pyproject.toml > requirements.txt && \
    uv pip install --system -r requirements.txt

# 运行阶段
FROM python:3.13-slim
# 复制编译好的 ta-lib 库
COPY --from=builder /usr/lib/libta_lib* /usr/lib/
# 复制 Python 包
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/

WORKDIR /app
COPY ./src /app/src

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    ENV=production

EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "src/astock_assistant/app.py"] 
