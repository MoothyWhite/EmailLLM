# 💝 EmailLLM - 情感分析邮件助手

一个专门用于接收聊天记录邮件并提供情感分析帮助的智能助手。通过IMAP协议定期检查邮箱，对接收到的聊天记录进行情感分析，并给出专业的恋爱建议和沟通策略。

## 🎯 项目目的

EmailLLM旨在帮助用户更好地理解和处理人际关系中的情感问题。当您将聊天记录通过邮件发送给自己时，该系统会自动分析聊天内容，识别潜在的情感问题，并提供针对性的建议，就像一位专业的情感军师一样为您提供帮助。

## 🌟 核心功能

- **自动邮件接收**：通过IMAP协议定期检查邮箱，自动接收包含聊天记录的邮件
- **智能情感分析**：利用大语言模型（LLM）深度分析聊天内容和情感状态
- **专业恋爱建议**：根据分析结果提供个性化的情感策略和沟通建议
- **自动化处理**：无需人工干预，全自动处理邮件并返回分析结果
- **Docker部署**：支持容器化部署，7x24小时稳定运行
- **安全配置**：敏感信息通过环境变量配置，保障账户安全

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

需要配置的关键信息：

- `SOURCE_EMAIL`: 您用来接收聊天记录邮件的邮箱地址
- `SOURCE_PASSWORD`: 源邮箱IMAP授权码
- `TARGET_EMAIL`: 您希望接收分析结果的邮箱地址
- `DEEPSEEK_API_KEY`: DeepSeek API密钥（用于LLM分析）
- `LLM_PROMPT`: LLM提示词（已预设为情感分析专用提示词）

### 3. 构建并运行

```bash
# 使用Docker Compose构建并运行
docker-compose up -d --build
```

### 4. 使用方法

1. 将您的聊天记录整理成文本格式并通过邮件发送到您配置的`SOURCE_EMAIL`邮箱
2. 系统会自动接收邮件并进行情感分析
3. 分析结果将以邮件形式发送到您配置的`TARGET_EMAIL`邮箱
4. 根据提供的建议调整您的沟通策略

## ⚙️ 配置说明

### 邮箱配置

对于QQ邮箱，需要开启IMAP/SMTP服务并生成授权码：

1. 登录QQ邮箱网页版
2. 进入设置 → 账户
3. 开启IMAP/SMTP服务
4. 生成授权码用于第三方客户端登录

### 环境变量详解

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SOURCE_EMAIL | 源邮箱地址（用于接收聊天记录邮件） | 无 |
| SOURCE_PASSWORD | 源邮箱IMAP授权码 | 无 |
| TARGET_EMAIL | 目标邮箱地址（用于接收分析结果） | 无 |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | 无 |
| LLM_PROMPT | LLM提示词（情感分析专用） | 预设值 |
| SOURCE_IMAP_SERVER | IMAP服务器地址 | imap.qq.com |
| SOURCE_IMAP_PORT | IMAP服务器端口 | 993 |
| SMTP_SERVER | SMTP服务器地址 | smtp.qq.com |
| SMTP_PORT | SMTP服务器端口 | 465 |
| CHECK_INTERVAL | 检查间隔（秒） | 60 |
