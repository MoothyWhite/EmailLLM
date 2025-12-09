import ssl
from typing import Any, Dict, List, Optional, Union
from email.message import Message
from email.header import decode_header
import email

from loguru import logger
from imapclient import IMAPClient  # type: ignore

from app.config import config


class MailFetcher:
    """使用 IMAPClient 的邮件获取器"""

    def __init__(self):
        self.imap_conn: Optional[IMAPClient] = None

    def connect(self) -> None:
        """建立 IMAP 连接"""
        if self.imap_conn:
            return
        context = ssl.create_default_context()
        self.imap_conn = IMAPClient(
            config.SOURCE_IMAP_SERVER,
            port=config.SOURCE_IMAP_PORT,
            ssl=True,
            ssl_context=context,
        )
        self.imap_conn.login(config.SOURCE_EMAIL, config.SOURCE_PASSWORD)
        # logger.info("IMAP connection established") # 减少无效日志

    def disconnect(self) -> None:
        """断开 IMAP 连接"""
        if self.imap_conn:
            try:
                self.imap_conn.logout()
                # logger.info("IMAP connection closed") # 减少无效日志
            except Exception as e:
                logger.warning(f"Error disconnecting IMAP: {e}")
            finally:
                self.imap_conn = None

    def search_unseen_emails(self) -> List[int]:
        """返回未读邮件的 UID 列表"""
        try:
            if not self.imap_conn:
                self.connect()
            assert self.imap_conn is not None  # 类型检查需要
            self.imap_conn.select_folder("INBOX")
            uids = self.imap_conn.search(["UNSEEN"])
            return uids
        except Exception as e:
            logger.error(f"Error searching unseen emails: {e}")
            return []

    def fetch_emails_by_uids(
        self, uids: List[Union[int, bytes, str]]
    ) -> Dict[int, bytes]:
        """批量获取原始邮件数据"""
        if not uids:
            return {}

        try:
            if not self.imap_conn:
                self.connect()
            assert self.imap_conn is not None  # 类型检查需要
            self.imap_conn.select_folder("INBOX")

            # 转成 int
            uid_list = [
                int(uid.decode() if isinstance(uid, bytes) else uid) for uid in uids
            ]

            response = self.imap_conn.fetch(uid_list, ["RFC822"])
            emails = {
                uid: response[uid][b"RFC822"] for uid in uid_list if uid in response
            }

            logger.info(f"Fetched {len(emails)} emails in batch")
            return emails
        except Exception as e:
            logger.error(f"Error fetching emails by UIDs: {e}")
            return {}

    def fetch_email_by_uid(
        self, uid: Union[int, str, bytes]
    ) -> Optional[Dict[str, Any]]:
        """根据 UID 获取并解析单封邮件"""
        try:
            if not self.imap_conn:
                self.connect()
            assert self.imap_conn is not None  # 类型检查需要
            self.imap_conn.select_folder("INBOX")

            uid_int = int(uid.decode() if isinstance(uid, bytes) else uid)
            response = self.imap_conn.fetch([uid_int], ["RFC822"])
            if uid_int not in response:
                logger.error(f"No data for email UID {uid!r}")
                return None

            raw_email = response[uid_int][b"RFC822"]
            email_message = email.message_from_bytes(raw_email)
            email_info = self._parse_email(email_message)
            email_info["uid"] = str(uid_int)

            # 标记已读
            self._mark_as_read(uid_int)

            return email_info
        except Exception as e:
            logger.error(f"Error fetching email UID {uid!r}: {e}")
            return None

    def _parse_email(self, email_message: Message) -> Dict[str, Any]:
        """解析邮件内容"""

        def decode_header_str(header: str) -> str:
            if not header:
                return ""
            decoded = decode_header(header)
            return "".join(
                [
                    part.decode(enc or "utf-8", errors="ignore")
                    if isinstance(part, bytes)
                    else part
                    for part, enc in decoded
                ]
            )

        subject = decode_header_str(email_message.get("Subject", ""))
        sender = decode_header_str(email_message.get("From", ""))
        receiver = decode_header_str(email_message.get("To", ""))
        date = email_message.get("Date", "")

        body_text = ""
        body_html = ""  # 不再处理HTML内容
        attachments = []

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append(
                            {
                                "filename": decode_header_str(filename),
                                "content_type": content_type,
                            }
                        )
                    continue

                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                # 只处理纯文本内容，忽略HTML
                try:
                    charset = part.get_content_charset() or "utf-8"
                    if content_type == "text/plain" and isinstance(payload, bytes):
                        body_text += payload.decode(charset, errors="ignore")
                except Exception as e:
                    logger.warning(f"Error decoding part: {e}")
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                try:
                    charset = email_message.get_content_charset() or "utf-8"
                    # 只处理纯文本内容，忽略HTML
                    if email_message.get_content_type() == "text/plain" and isinstance(
                        payload, bytes
                    ):
                        body_text = payload.decode(charset, errors="ignore")
                except Exception as e:
                    logger.warning(f"Error decoding payload: {e}")

        return {
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "date": date,
            "body_text": body_text,
            "body_html": body_html,  # 保持字段但始终为空
            "attachments": attachments,
        }

    def parse_raw_email(self, raw_email: bytes) -> Dict[str, Any]:
        """解析原始邮件数据"""
        try:
            msg = email.message_from_bytes(raw_email)
            return self._parse_email(msg)
        except Exception as e:
            logger.error(f"Error parsing raw email: {e}")
            return {}

    def _mark_as_read(self, uid: int) -> None:
        """标记邮件为已读"""
        try:
            if self.imap_conn:
                self.imap_conn.add_flags([uid], [b"\\Seen"])
                logger.info(f"Marked email UID {uid} as read")
        except Exception as e:
            logger.error(f"Error marking UID {uid} as read: {e}")
