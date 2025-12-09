#!/usr/bin/env python3
"""
邮件处理器模块
负责邮件的解析、LLM处理和格式化输出
"""

import os
import email
from email.message import Message
from typing import Any, Dict, Optional, Tuple
from loguru import logger
from agents import Agent, Runner

from app.config import config


def _get_model():
    if os.environ.get("DEEPSEEK_API_KEY"):
        return "litellm/deepseek/deepseek-chat"


class MailProcessor:
    """邮件处理器"""

    def __init__(self):
        """初始化邮件处理器"""
        self.config = config
        logger.info("MailProcessor initialized")

    def parse_raw_email(self, raw_email: bytes) -> Optional[Dict[str, Any]]:
        """
        解析原始邮件数据

        Args:
            raw_email: 原始邮件数据

        Returns:
            包含邮件信息的字典，如果解析失败则返回None
        """
        try:
            # 将原始邮件数据解析为email.message.Message对象
            email_message = email.message_from_bytes(raw_email)

            # 提取基本信息
            subject = self._decode_header(email_message.get("Subject", ""))
            sender = self._decode_header(email_message.get("From", ""))
            receiver = self._decode_header(email_message.get("To", ""))
            date = email_message.get("Date", "")

            # 解析邮件正文
            body_text, body_html = self._extract_body(email_message)

            # 解析附件信息
            attachments = self._extract_attachments(email_message)

            # 构建邮件信息字典
            email_info = {
                "subject": subject,
                "sender": sender,
                "receiver": receiver,
                "date": date,
                "body_text": body_text,
                "body_html": body_html,
                "attachments": attachments,
            }

            logger.info(f"Successfully parsed email: {subject}")
            return email_info

        except Exception as e:
            logger.error(f"Error parsing raw email: {e}")
            return None

    def process(self, email_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理邮件内容（包括LLM处理）

        Args:
            email_info: 解析后的邮件信息

        Returns:
            处理后的邮件信息
        """
        # 调用LLM处理逻辑
        processed_result = self.process_with_llm(email_info)

        # 如果LLM处理成功，替换邮件正文
        if processed_result is not None:
            # 使用LLM处理结果替换原始正文
            email_info["body_text"] = processed_result

        # 返回处理后的邮件信息
        return email_info

    def process_with_llm(self, email_info: Dict[str, Any]) -> Optional[str]:
        """
        使用LLM处理邮件内容（具体实现由用户完成）

        Args:
            email_info: 解析后的邮件信息

        Returns:
            经过LLM处理后的结果，如果处理失败则返回None
        """
        body_text = email_info["body_text"]

        logger.info(f"body_text: {body_text}")

        model = _get_model()
        agent = Agent(
            name="Assistant", model=model, instructions=os.environ.get("LLM_PROMPT", "")
        )
        result = Runner.run_sync(agent, body_text)
        final_output = result.final_output

        return final_output

    def _decode_header(self, header: str) -> str:
        """
        解码邮件头部信息

        Args:
            header: 编码的头部字符串

        Returns:
            解码后的字符串
        """
        from email.header import decode_header

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

    def _extract_body(self, email_message: Message) -> Tuple[str, str]:
        """
        提取邮件正文内容

        Args:
            email_message: email.message.Message对象

        Returns:
            (纯文本正文, HTML正文)的元组
        """
        body_text = ""
        body_html = ""

        try:
            if email_message.is_multipart():
                # 处理多部分邮件
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    # 跳过附件
                    if "attachment" in content_disposition:
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

        except Exception as e:
            logger.error(f"Error extracting email body: {e}")

        return body_text, body_html

    def _extract_attachments(self, email_message: Message) -> list:
        """
        提取附件信息

        Args:
            email_message: email.message.Message对象

        Returns:
            附件信息列表
        """
        attachments = []

        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_disposition = str(part.get("Content-Disposition", ""))

                    # 检查是否为附件
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            attachments.append(
                                {
                                    "filename": self._decode_header(filename),
                                    "content_type": part.get_content_type(),
                                }
                            )

        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")

        return attachments
