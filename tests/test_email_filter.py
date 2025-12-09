#!/usr/bin/env python3
"""
测试邮件过滤功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import EmailForwarderBot
import unittest
from unittest.mock import Mock


class TestEmailFilter(unittest.TestCase):
    """测试邮件过滤功能"""

    def setUp(self):
        """设置测试环境"""
        self.bot = EmailForwarderBot()

        # 模拟各个组件
        self.bot.fetcher = Mock()
        self.bot.sender = Mock()
        self.bot.processor = Mock()
        self.bot.poller = Mock()

    def test_email_with_emailllm_prefix_should_be_skipped(self):
        """测试以[EmailLLM]开头的邮件应该被跳过"""
        # 准备测试数据
        email_info = {"subject": "[EmailLLM] 测试邮件", "uid": "12345"}

        # 执行测试
        self.bot._handle_new_email(email_info)

        # 验证没有调用处理器和发送器
        self.bot.processor.process.assert_not_called()
        self.bot.sender.send_email.assert_not_called()

    def test_email_without_emailllm_prefix_should_be_processed(self):
        """测试不以[EmailLLM]开头的邮件应该被处理"""
        # 准备测试数据
        email_info = {"subject": "普通测试邮件", "uid": "12346"}

        # 模拟processor.process返回处理后的邮件
        processed_email = {
            "subject": "[EmailLLM] 普通测试邮件",
            "body_text": "处理后的内容",
        }
        self.bot.processor.process.return_value = processed_email

        # 模拟sender.send_email返回成功
        self.bot.sender.send_email.return_value = True

        # 执行测试
        self.bot._handle_new_email(email_info)

        # 验证调用了处理器和发送器
        self.bot.processor.process.assert_called_once_with(email_info)
        self.bot.sender.send_email.assert_called_once_with(processed_email)


if __name__ == "__main__":
    unittest.main()
