# 使用一个基础的Python镜像
FROM python:3.9-slim


# 使用绝对路径（如/app）
WORKDIR /app

# 后续操作会自动在/app下执行
COPY . .
RUN ls -l

# 安装所需的依赖项
RUN python3 -m venv venv \
    && . venv/bin/activate \
    && pip install --no-cache-dir -r requirements.txt

RUN chmod -R 777 .

# 在每次启动时运行 Python 脚本
CMD ["python", "app.py"]