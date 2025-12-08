import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from loguru import logger

from app.config import config


class MailSender:
    """邮件发送器"""

    def __init__(self):
        """初始化邮件发送器"""
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.SOURCE_EMAIL
        self.sender_password = config.SMTP_PASSWORD or config.SOURCE_PASSWORD

    def send_email(self, email_info: Dict[str, Any]) -> bool:
        """
        发送邮件

        Args:
            email_info: 包含邮件信息的字典

        Returns:
            发送成功返回True，否则返回False
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart()

            # 设置邮件头
            # 在主题前添加转发标识
            original_subject = email_info.get("subject", "")
            forwarded_subject = f"[Forwarded] {original_subject}"
            message["Subject"] = forwarded_subject

            # 设置发件人和收件人
            message["From"] = self.sender_email
            message["To"] = config.TARGET_EMAIL

            # 添加邮件正文
            body_text = email_info.get("body_text", "")
            body_html = email_info.get("body_html", "")

            # 如果有HTML内容，优先使用HTML
            if body_html:
                # 创建HTML部分
                html_part = MIMEText(body_html, "html")
                message.attach(html_part)

                # 如果也有文本内容，添加纯文本作为备选
                if body_text:
                    text_part = MIMEText(body_text, "plain")
                    message.attach(text_part)
            elif body_text:
                # 只有文本内容
                text_part = MIMEText(body_text, "plain")
                message.attach(text_part)
            else:
                # 没有内容的情况
                text_part = MIMEText("", "plain")
                message.attach(text_part)

            # TODO: 处理附件（如果需要）
            # attachments = email_info.get('attachments', [])
            # for attachment in attachments:
            #     # 这里需要实现附件的处理逻辑
            #     pass

            # 创建安全的SSL上下文
            context = ssl.create_default_context()

            # 连接到SMTP服务器并发送邮件
            logger.info(
                f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}"
            )
            with smtplib.SMTP_SSL(
                self.smtp_server, self.smtp_port, context=context
            ) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Successfully forwarded email to {config.TARGET_EMAIL}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def test_connection(self) -> bool:
        """
        测试SMTP连接

        Returns:
            连接成功返回True，否则返回False
        """
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.smtp_server, self.smtp_port, context=context
            ) as server:
                server.login(self.sender_email, self.sender_password)

            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
