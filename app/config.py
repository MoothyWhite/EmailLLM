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

        # 读取环境变量
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        # 验证必要配置
        self._validate_config()

    def _validate_config(self):
        """验证必要配置项"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required but not set in environment variables")


# 创建全局配置实例
config = Config()