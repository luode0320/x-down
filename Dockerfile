# 使用基础Python镜像
FROM python:3.9-slim-buster

#代码添加到文件夹
ADD . /app

# 设置工作目录
WORKDIR /app

# 安装依赖（此时文件名为main.txt）
RUN pip install --upgrade setuptools
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 验证文件复制结果（调试用）
RUN chmod 755 -R /app
RUN ls -la /app && pwd

# 设置启动命令
CMD ["python", "main.py"]