#!/usr/bin/env python3
"""
邮件自动转发机器人主程序
通过IMAP IDLE协议监听邮箱，实现实时邮件转发
"""

import signal
import time

from app.config import config
from app.idle_listener import MailboxIdleListener
from app.mail_fetcher import MailFetcher
from app.mail_sender import MailSender
from app.utils.logger import setup_logger


class EmailForwarderBot:
    """邮件自动转发机器人主类"""

    def __init__(self):
        """初始化邮件转发机器人"""
        # 设置日志
        self.logger = setup_logger(config.LOG_LEVEL, config.LOG_FILE)

        # 初始化各组件
        self.listener = MailboxIdleListener(self._on_new_mail)
        self.fetcher = MailFetcher()
        self.sender = MailSender()

        # 运行状态标志
        self.is_running = False

        # 注册信号处理器，用于优雅关闭
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _on_new_mail(self, uid: str):
        """
        新邮件回调函数

        Args:
            uid: 新邮件的唯一标识符
        """
        self.logger.info(f"Processing new mail with UID: {uid}")

        try:
            # 获取邮件内容
            email_info = self.fetcher.fetch_email_by_uid(uid)
            if not email_info:
                self.logger.error(f"Failed to fetch email with UID: {uid}")
                return

            # 发送邮件
            success = self.sender.send_email(email_info)
            if success:
                self.logger.info(f"Successfully forwarded email with UID: {uid}")
            else:
                self.logger.error(f"Failed to forward email with UID: {uid}")

        except Exception as e:
            self.logger.error(f"Error processing new mail with UID {uid}: {e}")

    def _signal_handler(self, signum, frame):
        """
        信号处理器，用于优雅关闭

        Args:
            signum: 信号编号
            frame: 当前堆栈帧
        """
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def start(self):
        """启动邮件转发机器人"""
        self.logger.info("Starting Email Forwarder Bot...")

        try:
            # 测试SMTP连接
            self.logger.info("Testing SMTP connection...")
            if not self.sender.test_connection():
                self.logger.error("SMTP connection test failed, exiting...")
                return

            # 启动监听器
            self.listener.start()
            self.is_running = True

            self.logger.info("Email Forwarder Bot started successfully!")
            self.logger.info("Press Ctrl+C to stop the bot")

            # 保持主线程运行
            while self.is_running:
                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error starting Email Forwarder Bot: {e}")
            self.stop()

    def stop(self):
        """停止邮件转发机器人"""
        self.logger.info("Stopping Email Forwarder Bot...")
        self.is_running = False

        # 停止监听器
        self.listener.stop()

        # 断开邮件获取器连接
        self.fetcher.disconnect()

        self.logger.info("Email Forwarder Bot stopped")


def main():
    """主函数"""
    # 创建机器人实例并启动
    bot = EmailForwarderBot()
    bot.start()


if __name__ == "__main__":
    main()
