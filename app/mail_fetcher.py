import email
import imaplib
from email.header import decode_header
from email.message import Message
from typing import Any, Dict, Optional

from loguru import logger

from app.config import config


class MailFetcher:
    """邮件获取和解析器"""

    def __init__(self):
        """初始化邮件获取器"""
        self.imap_conn: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """建立IMAP连接"""
        import ssl

        logger.info("Connecting to IMAP server for fetching emails...")

        # 创建SSL上下文
        context = ssl.create_default_context()

        # 连接到IMAP服务器
        self.imap_conn = imaplib.IMAP4_SSL(
            config.SOURCE_IMAP_SERVER, config.SOURCE_IMAP_PORT, ssl_context=context
        )

        # 登录
        self.imap_conn.login(config.SOURCE_EMAIL, config.SOURCE_PASSWORD)
        logger.info("Successfully connected to IMAP server for fetching")

    def disconnect(self) -> None:
        """断开IMAP连接"""
        if self.imap_conn:
            try:
                self.imap_conn.close()
                self.imap_conn.logout()
                logger.info("Disconnected from IMAP server (fetcher)")
            except Exception as e:
                logger.warning(f"Error disconnecting from IMAP server: {e}")
            finally:
                self.imap_conn = None

    def fetch_email_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        根据UID获取并解析邮件

        Args:
            uid: 邮件的唯一标识符

        Returns:
            包含邮件信息的字典，如果失败则返回None
        """
        try:
            if not self.imap_conn:
                self.connect()

            # 选择收件箱
            if self.imap_conn:
                self.imap_conn.select("INBOX")
            else:
                return None

            # 根据UID获取邮件
            if not self.imap_conn:
                return None
            status, msg_data = self.imap_conn.uid("FETCH", uid, "(RFC822)")
            if status != "OK":
                logger.error(f"Failed to fetch email with UID {uid}: {status}")
                return None

            # 解析邮件
            if not msg_data or not msg_data[0]:
                logger.error(f"No data received for email with UID {uid}")
                return None

            if len(msg_data[0]) < 2:
                logger.error(f"Invalid data format for email with UID {uid}")
                return None

            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # 解析邮件信息
            email_info = self._parse_email(email_message)
            email_info["uid"] = uid

            # 标记邮件为已读
            self._mark_as_read(uid)

            logger.info(f"Successfully fetched and parsed email with UID {uid}")
            return email_info

        except Exception as e:
            logger.error(f"Error fetching email with UID {uid}: {e}")
            return None

    def _parse_email(self, email_message: Message) -> Dict[str, Any]:
        """
        解析邮件内容

        Args:
            email_message: email.message.Message对象

        Returns:
            包含邮件信息的字典
        """
        # 解析邮件头
        subject = self._decode_header(email_message.get("Subject", ""))
        sender = self._decode_header(email_message.get("From", ""))
        receiver = self._decode_header(email_message.get("To", ""))
        date = email_message.get("Date", "")

        # 初始化邮件内容
        body_text = ""
        body_html = ""
        attachments = []

        # 处理多部分邮件
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # 跳过附件（如果需要处理附件可以在这里实现）
                if "attachment" in content_disposition:
                    # 可以选择保存附件信息
                    filename = part.get_filename()
                    if filename:
                        attachments.append(
                            {
                                "filename": self._decode_header(filename),
                                "content_type": content_type,
                            }
                        )
                    continue

                # 处理文本内容
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body_text += payload.decode(charset, errors="ignore")
                    except Exception as e:
                        logger.warning(f"Error decoding plain text part: {e}")
                elif content_type == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body_html += payload.decode(charset, errors="ignore")
                    except Exception as e:
                        logger.warning(f"Error decoding HTML part: {e}")
        else:
            # 处理单部分邮件
            content_type = email_message.get_content_type()
            charset = email_message.get_content_charset() or "utf-8"

            if content_type == "text/plain":
                try:
                    payload = email_message.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body_text = payload.decode(charset, errors="ignore")
                except Exception as e:
                    logger.warning(f"Error decoding plain text: {e}")
            elif content_type == "text/html":
                try:
                    payload = email_message.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body_html = payload.decode(charset, errors="ignore")
                except Exception as e:
                    logger.warning(f"Error decoding HTML: {e}")

        return {
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "date": date,
            "body_text": body_text,
            "body_html": body_html,
            "attachments": attachments,
        }

    def _decode_header(self, header: str) -> str:
        """
        解码邮件头部信息

        Args:
            header: 编码的头部字符串

        Returns:
            解码后的字符串
        """
        if not header:
            return ""

        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors="ignore")
                    else:
                        decoded_string += part.decode("utf-8", errors="ignore")
                else:
                    decoded_string += part
            return decoded_string
        except Exception as e:
            logger.warning(f"Error decoding header '{header}': {e}")
            return header

    def _mark_as_read(self, uid: str):
        """
        标记邮件为已读

        Args:
            uid: 邮件的唯一标识符
        """
        try:
            if self.imap_conn:
                # 标记为已读
                status, _ = self.imap_conn.uid("STORE", uid, "+FLAGS", "\\Seen")
                if status == "OK":
                    logger.info(f"Marked email {uid} as read")
                else:
                    logger.warning(f"Failed to mark email {uid} as read: {status}")
        except Exception as e:
            logger.error(f"Error marking email {uid} as read: {e}")
