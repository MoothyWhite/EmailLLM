FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# 设置作者信息
LABEL maintainer="wwq"

# 配置 Debian 软件源使用阿里云镜像
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 更新包列表并安装常用工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 编辑/查看文件工具
    vim \
    nano \
    less \
    # 网络排查工具
    curl \
    wget \
    # 进程/系统状态工具
    procps \
    lsof \
    htop \
    && rm -rf /var/lib/apt/lists/*


# 设置工作目录
WORKDIR /email-llm

# 利用缓存加速构建
RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-install-project --index-url "http://mirrors.aliyun.com/pypi/simple/"

# 复制项目文件
COPY app ./app
COPY uv.lock .
COPY pyproject.toml .

RUN  uv sync --locked --index-url "http://mirrors.aliyun.com/pypi/simple/"

# 设置启动命令
CMD ["uv", "run", "-m", "app.main"]