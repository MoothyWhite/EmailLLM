import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


class Config:
    def __init__(self):
        # 从.env文件加载环境变量
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f"No .env file found at {env_path}")

        self.LLM_PROMPT = os.getenv("LLM_PROMPT", "")

        # 邮件转发相关配置
        # 源邮箱配置（用于接收邮件）
        self.SOURCE_IMAP_SERVER = os.getenv("SOURCE_IMAP_SERVER", "imap.qq.com")
        self.SOURCE_IMAP_PORT = int(os.getenv("SOURCE_IMAP_PORT", "993"))
        self.SOURCE_EMAIL = os.getenv("SOURCE_EMAIL")
        self.SOURCE_PASSWORD = os.getenv("SOURCE_PASSWORD")  # IMAP授权码

        # 目标邮箱配置（用于转发邮件）
        self.TARGET_EMAIL = os.getenv("TARGET_EMAIL")

        # SMTP配置（用于发送邮件）
        self.SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
        self.SMTP_PASSWORD = os.getenv(
            "SMTP_PASSWORD"
        )  # SMTP授权码，如果未设置则使用SOURCE_PASSWORD

        # 循环检查间隔（秒）
        self.CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

        # 日志配置
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/email_forwarder.log")

        # 验证必要配置
        self._validate_config()

    def _validate_config(self):
        """验证必要配置项"""
        missing_configs = []

        if not self.SOURCE_EMAIL:
            missing_configs.append("SOURCE_EMAIL")

        if not self.SOURCE_PASSWORD:
            missing_configs.append("SOURCE_PASSWORD")

        if not self.TARGET_EMAIL:
            missing_configs.append("TARGET_EMAIL")

        if missing_configs:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_configs)}"
            )


# 创建全局配置实例
config = Config()
