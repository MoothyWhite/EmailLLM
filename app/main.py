#!/usr/bin/env python3
"""
邮件自动转发机器人主程序
通过IMAP循环检查实现邮件转发
"""

import signal
import sys
import os
import threading

# 添加项目根目录到 Python 路径，确保能正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用相对导入
from .mail_fetcher import MailFetcher
from .mail_sender import MailSender
from .mail_processor import MailProcessor
from .mail_poller import MailPoller
from .utils.logger import default_logger as logger


class EmailForwarderBot:
    """邮件自动转发机器人主类，负责协调各组件"""

    def __init__(self):
        """初始化邮件转发机器人"""
        # 初始化各组件
        self.fetcher = MailFetcher()
        self.sender = MailSender()
        self.processor = MailProcessor()
        self.poller = MailPoller(self.fetcher)

        # 运行状态标志
        self.is_running = False
        self._stop_event = threading.Event()

        # 注册信号处理器，用于优雅关闭
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _handle_new_email(self, email_info: dict) -> None:
        """
        处理新邮件的回调函数

        Args:
            email_info: 邮件信息字典
        """
        try:
            # 检查邮件主题是否以"[EmailLLM]"开头，如果是则跳过处理
            subject = email_info.get("subject", "")
            if subject.startswith("[EmailLLM]"):
                logger.info(
                    f"Skipping email with subject '{subject}' as it starts with '[EmailLLM]'"
                )
                return

            # 使用MailProcessor处理邮件内容（包括LLM处理）
            processed_email_info = self.processor.process(email_info)

            # 发送邮件
            success = self.sender.send_email(processed_email_info)
            if success:
                logger.info(
                    f"Successfully forwarded email with UID: {email_info.get('uid', 'unknown')}"
                )
                # 邮件转发成功后，将原邮件标记为已读
                uid = email_info.get('uid')
                if uid:
                    try:
                        # 确保连接到IMAP服务器
                        self.fetcher.connect()
                        # 标记邮件为已读
                        self.fetcher._mark_as_read(int(uid))
                    except Exception as e:
                        logger.error(f"Error marking email UID {uid} as read: {e}")
            else:
                logger.error(
                    f"Failed to forward email with UID: {email_info.get('uid', 'unknown')}"
                )
        except Exception as e:
            logger.error(f"Error handling email: {e}")

    def _signal_handler(self, signum, frame):
        """
        信号处理器，用于优雅关闭

        Args:
            signum: 信号编号
            frame: 当前堆栈帧
        """
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def start(self):
        """启动邮件转发机器人"""
        logger.info("Starting Email Forwarder Bot...")

        try:
            # 测试SMTP连接
            logger.info("Testing SMTP connection...")
            if not self.sender.test_connection():
                logger.error("SMTP connection test failed, exiting...")
                return

            self.is_running = True
            self._stop_event.clear()

            logger.info("Email Forwarder Bot started successfully!")
            logger.info("Press Ctrl+C to stop the bot")

            # 开始轮询邮件
            self.poller.start_polling(self._handle_new_email)

        except Exception as e:
            logger.error(f"Error starting Email Forwarder Bot: {e}")
            self.stop()

    def stop(self):
        """停止邮件转发机器人"""
        logger.info("Stopping Email Forwarder Bot...")
        self.is_running = False
        self._stop_event.set()

        # 停止邮件轮询
        self.poller.stop_polling()

        logger.info("Email Forwarder Bot stopped")


def main():
    """主函数"""
    try:
        # 创建机器人实例并启动
        bot = EmailForwarderBot()
        bot.start()
    except Exception as e:
        print(f"Fatal error in main program: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
