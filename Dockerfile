FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 先单独复制requirements.txt（利用Docker缓存）
COPY requirements.txt .

# 安装依赖（无需虚拟环境）
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（保持原始权限）
COPY . .

# 验证文件存在
RUN ls -la /app/main.py || { echo "Error: main.py not found!"; exit 1; }

# 设置安全权限
RUN find /app -type d -exec chmod 755 {} \; \
    && find /app -type f -exec chmod 644 {} \;

# 直接运行（确保使用绝对路径）
CMD ["/usr/local/bin/python", "/app/main.py"]