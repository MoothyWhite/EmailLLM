import imaplib
import ssl
import time
import threading
from typing import Callable, Optional
from loguru import logger
from app.config import config


class MailboxIdleListener:
    """IMAP IDLE监听器，用于监听邮箱中的新邮件"""

    def __init__(self, on_new_mail_callback: Callable[[str], None]):
        """
        初始化监听器

        Args:
            on_new_mail_callback: 当有新邮件时调用的回调函数，参数为邮件UID
        """
        self.on_new_mail_callback = on_new_mail_callback
        self.imap_conn: Optional[imaplib.IMAP4_SSL] = None
        self.is_running = False
        self.listener_thread: Optional[threading.Thread] = None
        self.reconnect_delay = 5  # 重连延迟（秒）

    def _connect(self) -> None:
        """建立IMAP连接并登录"""
        logger.info("Connecting to IMAP server...")

        # 创建SSL上下文
        context = ssl.create_default_context()

        # 连接到IMAP服务器
        self.imap_conn = imaplib.IMAP4_SSL(
            config.SOURCE_IMAP_SERVER, config.SOURCE_IMAP_PORT, ssl_context=context
        )

        # 登录
        self.imap_conn.login(config.SOURCE_EMAIL, config.SOURCE_PASSWORD)
        logger.info("Successfully connected to IMAP server and logged in")

        # 选择收件箱
        self.imap_conn.select("INBOX")
        logger.info("Selected INBOX")

    def _disconnect(self) -> None:
        """断开IMAP连接"""
        if self.imap_conn:
            try:
                self.imap_conn.close()
                self.imap_conn.logout()
                logger.info("Disconnected from IMAP server")
            except Exception as e:
                logger.warning(f"Error disconnecting from IMAP server: {e}")
            finally:
                self.imap_conn = None

    def _idle_loop(self) -> None:
        """IDLE循环监听新邮件"""
        while self.is_running:
            try:
                # 确保连接有效
                if not self.imap_conn:
                    self._connect()

                if not self.imap_conn:
                    raise imaplib.IMAP4.abort("Failed to establish IMAP connection")

                # 进入IDLE模式
                logger.info("Entering IDLE mode...")
                self.imap_conn.send(b"DONE\r\n")  # 确保之前的IDLE已结束
                tag = self.imap_conn._new_tag().encode()
                self.imap_conn.send(tag + b" IDLE\r\n")

                # 等待服务器响应
                response = self.imap_conn.readline()
                if not response.startswith(b"+ "):
                    logger.error(f"Unexpected IDLE response: {response!r}")
                    raise imaplib.IMAP4.abort("Failed to enter IDLE mode")

                logger.info("IDLE mode established, waiting for new mails...")

                # 等待新邮件通知或超时
                # 使用较短的超时时间以便定期检查运行状态
                timeout = 29 * 60  # 29分钟，IDLE通常最多30分钟
                start_time = time.time()

                while self.is_running and (time.time() - start_time) < timeout:
                    # 检查是否有数据可读
                    try:
                        # 使用非阻塞方式检查数据
                        import select
                        import socket

                        # 获取套接字
                        if not self.imap_conn:
                            break
                        sock = self.imap_conn.sock
                        ready = select.select([sock], [], [], 1.0)  # 1秒超时

                        if ready[0]:
                            # 读取响应
                            response = self.imap_conn.readline().strip()
                            logger.debug(f"IMAP response: {response!r}")

                            # 检查是否存在新邮件的通知
                            if (
                                isinstance(response, bytes)
                                and b"EXISTS" in response.upper()
                            ):
                                logger.info("New mail detected!")
                                # 触发回调函数处理新邮件
                                self._handle_new_mail()
                                break  # 处理完新邮件后重新进入IDLE模式

                    except (socket.timeout, imaplib.IMAP4.abort) as e:
                        logger.warning(f"IMAP connection error: {e}")
                        # 连接可能已断开，需要重新连接
                        self._disconnect()
                        break
                    except Exception as e:
                        logger.error(f"Error in IDLE loop: {e}")
                        self._disconnect()
                        break

            except imaplib.IMAP4.error as e:
                logger.error(f"IMAP error: {e}")
                self._disconnect()
                if self.is_running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected error in IDLE loop: {e}")
                self._disconnect()
                if self.is_running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)

    def _handle_new_mail(self) -> None:
        """处理新邮件"""
        try:
            # 退出IDLE模式
            if not self.imap_conn:
                return
            self.imap_conn.send(b"DONE\r\n")
            self.imap_conn.readline()  # 读取DONE的响应

            # 搜索最新的未读邮件
            status, messages = self.imap_conn.search(None, "UNSEEN")
            if status == "OK" and messages[0]:
                # 获取邮件UID列表
                email_ids = messages[0].split()
                if email_ids:
                    # 获取最新邮件的UID
                    latest_email_id = email_ids[-1]
                    # 获取邮件UID
                    status, uid_data = self.imap_conn.fetch(latest_email_id, "(UID)")
                    if status == "OK" and uid_data:
                        # 解析UID
                        if uid_data and len(uid_data) > 0 and uid_data[0]:
                            # 检查第一个元素是否是元组
                            first_element = uid_data[0]
                            if (
                                isinstance(first_element, tuple)
                                and len(first_element) > 1
                            ):
                                uid_bytes = first_element[0]
                                if isinstance(uid_bytes, bytes):
                                    uid_str = uid_bytes.decode("utf-8", errors="ignore")
                                else:
                                    uid_str = str(uid_bytes)
                            elif isinstance(first_element, bytes):
                                uid_str = first_element.decode("utf-8", errors="ignore")
                            else:
                                uid_str = str(first_element)

                            # 提取UID数字
                            import re

                            uid_match = re.search(r"UID (\d+)", uid_str)
                            if uid_match:
                                uid = uid_match.group(1)
                                logger.info(f"Processing new mail with UID: {uid}")
                                # 调用回调函数处理邮件
                                self.on_new_mail_callback(uid)
                            else:
                                logger.warning(f"Could not parse UID from: {uid_str}")
                        else:
                            logger.error(
                                f"Invalid UID data for email {latest_email_id}"
                            )
                    else:
                        logger.error(f"Failed to fetch UID for email {latest_email_id}")
                else:
                    logger.warning("No unread emails found")
            else:
                logger.info("No unread emails")

        except Exception as e:
            logger.error(f"Error handling new mail: {e}")

    def start(self) -> None:
        """启动监听器"""
        logger.info("Starting mailbox listener...")
        self.is_running = True
        self.listener_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self.listener_thread.start()
        logger.info("Mailbox listener started")

    def stop(self) -> None:
        """停止监听器"""
        logger.info("Stopping mailbox listener...")
        self.is_running = False
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=5)
        self._disconnect()
        logger.info("Mailbox listener stopped")
