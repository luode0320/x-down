# 使用基础Python镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制所有文件到容器（包括main.py）
COPY requirements.txt /app/requirements.txt
COPY main.py /app/main.py

# 安装依赖（此时文件名为main.txt）
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
# 验证文件复制结果（调试用）
RUN chmod 755 -R /app
RUN ls -la /app && pwd

# 设置启动命令
CMD python3 /app/main.py