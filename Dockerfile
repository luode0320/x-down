# 使用一个基础的Python镜像
FROM python:3.9-slim


# 设置工作目录为 /app
WORKDIR /app

# 复制当前目录下的所有文件到 /app 目录下
COPY . /app

# 安装所需的依赖项
RUN python3 -m venv venv \
    && . venv/bin/activate \
    && pip install --no-cache-dir -r requirements.txt

RUN chmod -R 777 .
RUN chmod -R 777 /app

# 在每次启动时运行 Python 脚本
CMD ["python", "app.py"]