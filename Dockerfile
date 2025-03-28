# 使用基础Python镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制所有文件到容器（包括main.py）
COPY . .

# 安装依赖（此时文件名为main.txt）
RUN pip install --no-cache-dir -r requirements.txt

# 验证文件复制结果（调试用）
RUN ls -la /app && pwd

# 设置启动命令
CMD ["python", "main.py"]