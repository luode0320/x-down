# 使用一个基础的Python镜像
FROM python:3.10-slim


# 使用绝对路径（如/app）
WORKDIR /app

# 复制文件（注意第一个.是宿主机当前目录，第二个.是容器的/app）
COPY . .
# 权限
RUN chmod -R 777 /app
# 验证文件是否复制成功
RUN ls -la /app
# 验证当前工作目录
RUN pwd

# 直接全局安装依赖（容器本身就是隔离环境）
RUN pip install --no-cache-dir -r requirements.txt

# 在每次启动时运行 Python 脚本
CMD ["python", "main.py"]