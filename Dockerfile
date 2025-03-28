# 使用基础Python镜像
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 复制所有文件到容器（包括main.py）
COPY requirements.txt /app/requirements.txt
# 安装依赖（此时文件名为main.txt）
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

COPY ./ /app
# 验证文件复制结果（调试用）
RUN chmod 755 -R /app
RUN ls -la /app && pwd

# 设置启动命令
CMD ["python3", "main.py"]