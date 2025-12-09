#!/usr/bin/env python3
"""
邮件自动转发机器人主程序
通过IMAP循环检查实现邮件转发
"""

import signal
import time
import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用相对导入
from .config import config
from .mail_fetcher import MailFetcher
from .mail_sender import MailSender
from .mail_processor import MailProcessor
from .utils.logger import default_logger as logger

# 导入IMAPClient
import ssl
from imapclient import IMAPClient  # type: ignore


class EmailForwarderBot:
    """邮件自动转发机器人主类"""

    def __init__(self):
        """初始化邮件转发机器人"""

        # 初始化各组件
        self.fetcher = MailFetcher()
        self.sender = MailSender()
        self.processor = MailProcessor()

        # 运行状态标志
        self.is_running = False

        # 循环检查间隔（秒）
        self.check_interval = config.CHECK_INTERVAL

        # 注册信号处理器，用于优雅关闭
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _check_and_process_mails(self):
        """
        检查并处理未读邮件
        """
        try:
            # 建立IMAP连接
            ssl_context = ssl.create_default_context()
            with IMAPClient(
                config.SOURCE_IMAP_SERVER,
                port=config.SOURCE_IMAP_PORT,
                ssl=True,
                ssl_context=ssl_context,
            ) as client:
                client.login(config.SOURCE_EMAIL, config.SOURCE_PASSWORD)

                # 选择收件箱
                client.select_folder("INBOX")

                # 搜索未读邮件
                uids = client.search("UNSEEN")
                logger.info(f"Found {len(uids)} unread emails")

                # 处理每个未读邮件
                for uid in uids:
                    try:
                        logger.info(f"Processing new mail with UID: {uid}")

                        # 获取邮件内容（使用IMAPClient直接获取原始邮件数据）
                        response = client.fetch([uid], ["RFC822"])
                        if not response or uid not in response:
                            logger.error(
                                f"Failed to fetch raw email with UID: {uid}"
                            )
                            continue

                        raw_email = response[uid][b"RFC822"]

                        # 使用MailProcessor解析原始邮件数据
                        email_info = self.processor.parse_raw_email(raw_email)
                        if not email_info:
                            logger.error(f"Failed to parse email with UID: {uid}")
                            continue

                        # 使用MailProcessor处理邮件内容（包括LLM处理）
                        processed_email_info = self.processor.process(email_info)

                        # 发送邮件
                        success = self.sender.send_email(processed_email_info)
                        if success:
                            logger.info(
                                f"Successfully forwarded email with UID: {uid}"
                            )
                        else:
                            logger.error(
                                f"Failed to forward email with UID: {uid}"
                            )

                        # 标记邮件为已读
                        client.add_flags([uid], [b"\\Seen"])

                    except Exception as e:
                        logger.error(f"Error processing mail with UID {uid}: {e}")

        except Exception as e:
            logger.error(f"Error checking emails: {e}")

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

            logger.info("Email Forwarder Bot started successfully!")
            logger.info("Press Ctrl+C to stop the bot")

            # 循环检查邮件
            while self.is_running:
                self._check_and_process_mails()
                # 等待下次检查
                for _ in range(self.check_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)

        except Exception as e:
            logger.error(f"Error starting Email Forwarder Bot: {e}")
            self.stop()

    def stop(self):
        """停止邮件转发机器人"""
        logger.info("Stopping Email Forwarder Bot...")
        self.is_running = False

        # 断开邮件获取器连接
        self.fetcher.disconnect()

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
