FROM python:3.10

# 设置工作目录
WORKDIR /app

# 复制文件（分阶段复制优化构建缓存）
COPY requirements.txt .
COPY . .

# 创建并激活虚拟环境（使用绝对路径）
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# 设置安全权限（替代危险的777）
RUN find /app -type d -exec chmod 755 {} \; && \
    find /app -type f -exec chmod 644 {} \;

# 使用虚拟环境的Python解释器执行
CMD ["/venv/bin/python", "main.py"]