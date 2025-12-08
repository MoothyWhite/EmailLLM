# 使用官方Python运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装uv包管理器
RUN pip install uv

# 安装项目依赖
RUN uv sync --locked

# 创建日志目录
RUN mkdir -p logs

# 暴露端口（虽然这个应用不直接监听HTTP端口，但保留以备将来扩展）
EXPOSE 8000

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 设置启动命令
CMD ["uv", "run", "python", "app/main.py"]