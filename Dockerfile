# 使用官方 Python 镜像
FROM python:3.10-slim as builder

# 安装系统依赖（按需添加）
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# 创建虚拟环境（使用 /venv 绝对路径）
RUN python -m venv /venv

# 设置工作目录
WORKDIR /app

# 先单独复制 requirements.txt 以利用 Docker 缓存
COPY requirements.txt .

# 安装依赖到虚拟环境
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# ----------------------------
# 运行时阶段（多阶段构建）
FROM python:3.10-slim

# 创建非 root 用户
RUN useradd -m appuser && \
    mkdir -p /app && \
    chown appuser:appuser /app

# 从构建阶段复制虚拟环境
COPY --from=builder /venv /venv

# 设置工作目录
WORKDIR /app

# 复制应用代码（保持正确的文件权限）
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 验证文件存在
RUN ls -la && \
    /venv/bin/python -c "import os; assert os.path.exists('main.py'), 'ERROR: main.py not found!'"

# 设置环境变量
ENV PATH="/venv/bin:$PATH" \
    PYTHONPATH="/app"

# 启动命令
CMD ["python", "main.py"]