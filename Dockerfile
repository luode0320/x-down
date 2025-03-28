# 使用基础Python镜像
FROM python:3.9-slim-buster

# 安装 file 命令
RUN apt-get update && apt-get install -y file

# 代码添加到文件夹
ADD . /app

# 设置工作目录
WORKDIR /app

# 检查文件编码和 BOM
RUN file -bi /app/main.py
RUN xxd -p -l 3 /app/main.py

# 安装依赖
RUN pip install --upgrade setuptools
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 设置启动命令
CMD ["python", "main.py"]
