# 📧 EmailLLM - 邮件自动转发机器人

一个基于IMAP IDLE协议的邮件自动转发机器人，能够实时监听邮箱并在收到新邮件时自动转发到指定邮箱。

## 🎯 功能特点

- **实时监听**：使用IMAP IDLE协议实现准实时邮件监听
- **自动转发**：收到新邮件后自动转发到指定邮箱
- **Docker部署**：支持Docker容器化部署，7x24小时运行
- **日志记录**：完整的日志记录便于问题排查
- **异常处理**：具备连接断线重连机制
- **安全配置**：敏感信息通过环境变量配置

## 🏗️ 系统架构

```
用户发送邮件 → 你的专用163邮箱 → (IMAP IDLE长连接) → 邮件转发机器人 → 通过SMTP转发到目标邮箱
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd EmailLLM
```

### 2. 配置环境变量

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑配置文件，填入实际值
nano .env
```

需要配置以下关键信息：
- `SOURCE_EMAIL`: 源邮箱地址（用于接收邮件）
- `SOURCE_PASSWORD`: 源邮箱IMAP授权码
- `TARGET_EMAIL`: 目标邮箱地址（用于转发邮件）

### 3. 构建并运行

```bash
# 使用Docker Compose构建并运行
docker-compose up -d --build
```

### 4. 查看日志

```bash
# 实时查看日志
docker-compose logs -f
```

## ⚙️ 配置说明

### 邮箱配置

对于163邮箱，需要开启IMAP/SMTP服务并生成授权码：

1. 登录163邮箱网页版
2. 进入设置 → POP3/SMTP/IMAP
3. 开启IMAP/SMTP服务
4. 生成授权码用于第三方客户端登录

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SOURCE_EMAIL | 源邮箱地址 | 无 |
| SOURCE_PASSWORD | 源邮箱IMAP授权码 | 无 |
| TARGET_EMAIL | 目标邮箱地址 | 无 |
| SOURCE_IMAP_SERVER | IMAP服务器地址 | imap.163.com |
| SOURCE_IMAP_PORT | IMAP服务器端口 | 993 |
| SMTP_SERVER | SMTP服务器地址 | smtp.163.com |
| SMTP_PORT | SMTP服务器端口 | 465 |
| LOG_LEVEL | 日志级别 | INFO |
| LOG_FILE | 日志文件路径 | logs/email_forwarder.log |

## 🛠️ 开发指南

### 项目结构

```
email-forwarder-bot/
├── docker-compose.yml          # Docker Compose配置
├── Dockerfile                  # Docker镜像构建文件
├── .env                        # 敏感配置文件
├── .env.example                # 配置文件模板
├── pyproject.toml              # Python项目依赖声明
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置管理
│   ├── idle_listener.py        # IMAP IDLE监听器
│   ├── mail_fetcher.py         # 邮件获取和解析
│   ├── mail_sender.py          # 邮件发送
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # 日志配置
└── logs/                       # 日志目录
```

### 本地开发

1. 安装依赖：
```bash
# 使用uv安装依赖
uv sync
```

2. 运行应用：
```bash
# 直接运行
python app/main.py
```

## 📊 监控和维护

### 健康检查

Docker Compose配置中包含了健康检查，会定期检查日志文件的更新情况。

### 日志管理

应用会将日志写入`logs/email_forwarder.log`文件，并自动按大小轮转。

## 🔧 故障排除

### 常见问题

1. **无法连接到邮箱服务器**
   - 检查网络连接
   - 确认IMAP/SMTP服务已开启
   - 验证授权码是否正确

2. **邮件转发失败**
   - 检查目标邮箱地址是否正确
   - 查看日志了解具体错误信息

### 查看日志

```bash
# 查看最近的日志
docker-compose logs --tail=100

# 实时查看日志
docker-compose logs -f
```

## 🧪 代码质量检查

本项目集成了多种代码质量检查工具，确保代码质量和一致性。

### 工具介绍

- **Ruff**: 超快的Python linter和格式化工具
- **Mypy**: Python静态类型检查工具

### 使用方法

```bash
# 安装开发依赖（如果尚未安装）
make install-dev

# 运行所有代码质量检查
make check

# 运行Ruff linting
make ruff

# 运行Ruff自动修复
make ruff-fix

# 运行Mypy类型检查
make mypy

# 格式化代码
make format

# 清理缓存文件
make clean
```

### 配置文件

- `ruff.toml`: Ruff配置文件
- `mypy.ini`: Mypy配置文件

## 📄 许可证

本项目采用MIT许可证，详情请见[LICENSE](LICENSE)文件。