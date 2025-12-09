import threading
from typing import Callable, Any
from loguru import logger

from app.config import config
from .mail_fetcher import MailFetcher


class MailPoller:
    """邮件轮询器，负责定期检查和获取新邮件"""

    def __init__(self, fetcher: MailFetcher):
        """初始化邮件轮询器

        Args:
            fetcher: 邮件获取器实例
        """
        self.fetcher = fetcher
        self.is_polling = False
        self.check_interval = config.CHECK_INTERVAL
        self._stop_event = threading.Event()

    def start_polling(self, callback: Callable[[dict], Any]) -> None:
        """
        开始轮询邮件

        Args:
            callback: 处理新邮件的回调函数，接收邮件信息字典作为参数
        """
        self.is_polling = True
        self._stop_event.clear()
        logger.info("Starting mail polling...")

        try:
            while self.is_polling and not self._stop_event.is_set():
                self._check_new_emails(callback)
                # 等待下次检查或收到停止信号
                if self.is_polling and not self._stop_event.wait(self.check_interval):
                    continue
        except Exception as e:
            logger.error(f"Error during mail polling: {e}")
        finally:
            self.fetcher.disconnect()

    def stop_polling(self) -> None:
        """停止轮询"""
        logger.info("Stopping mail polling...")
        self.is_polling = False
        self._stop_event.set()

    def _check_new_emails(self, callback: Callable[[dict], Any]) -> None:
        """
        检查新邮件并处理

        Args:
            callback: 处理新邮件的回调函数
        """
        try:
            # 搜索未读邮件
            uids = self.fetcher.search_unseen_emails()
            logger.info(f"Found {len(uids)} unread emails")

            if not uids:
                return

            # 批量获取邮件
            raw_emails = self.fetcher.fetch_emails_by_uids(list(uids))

            # 处理每封邮件
            for uid, raw_email in raw_emails.items():
                try:
                    logger.info(f"Processing new mail with UID: {uid}")

                    # 解析邮件内容
                    email_info = self.fetcher.parse_raw_email(raw_email)
                    email_info["uid"] = uid

                    # 调用回调函数处理邮件
                    callback(email_info)

                except Exception as e:
                    logger.error(f"Error processing mail with UID {uid}: {e}")

        except Exception as e:
            logger.error(f"Error checking emails: {e}")
        finally:
            # 断开IMAP连接
            self.fetcher.disconnect()
