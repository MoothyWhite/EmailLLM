import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    设置日志记录器

    Args:
        log_level: 日志级别，默认为INFO
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    # 移除默认的日志处理器
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        enqueue=True,  # 异步写入
        backtrace=True,  # 错误跟踪
        diagnose=True,  # 诊断信息
    )

    # 如果指定了日志文件，则添加文件输出
    if log_file:
        log_path = Path(log_file)
        # 确保日志目录存在
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 添加文件输出，支持日志轮转
        logger.add(
            str(log_path),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="500 MB",  # 日志文件达到500MB时轮转
            retention="30 days",  # 保留30天的日志
            compression="zip",  # 压缩旧日志
            enqueue=True,  # 异步写入
            backtrace=True,  # 错误跟踪
            diagnose=True,  # 诊断信息
        )

    return logger


# 创建默认的日志记录器实例
default_logger = setup_logger()


__all__ = ["logger", "setup_logger", "default_logger"]
