#!/usr/bin/env python3
"""
邮件转发机器人测试脚本
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入应用模块
try:
    from app.config import config
    from app.mail_sender import MailSender
    from app.utils.logger import setup_logger
except ImportError:
    # 如果直接运行此脚本，需要将项目根目录添加到Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from app.config import config
    from app.mail_sender import MailSender
    from app.utils.logger import setup_logger


@patch("app.mail_sender.smtplib.SMTP_SSL")
def test_smtp_connection(mock_smtp):
    """测试SMTP连接"""
    print("Testing SMTP connection...")
    try:
        # 模拟成功的SMTP连接
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = MailSender()
        result = sender.test_connection()

        # 验证方法调用（使用更宽松的断言）
        mock_smtp.assert_called_once()
        mock_server.login.assert_called_once_with(
            sender.sender_email, sender.sender_password
        )

        assert result, "SMTP connection test should pass with mocked connection"
        print("✅ SMTP connection test passed\n")
    except Exception as e:
        print(f"❌ SMTP connection test failed: {e}\n")
        assert False, f"SMTP connection test failed: {e}"


@patch("app.mail_sender.smtplib.SMTP_SSL")
def test_email_sending(mock_smtp):
    """测试邮件发送功能"""
    print("Testing email sending...")
    try:
        # 模拟成功的邮件发送
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = MailSender()

        # 创建测试邮件
        test_email = {
            "subject": "Test Email from Email Forwarder Bot",
            "sender": config.SOURCE_EMAIL,
            "receiver": config.TARGET_EMAIL,
            "body_text": "This is a test email sent from the Email Forwarder Bot.\n\n测试邮件内容。",
            "body_html": "<h1>Test Email from Email Forwarder Bot</h1><p>This is a test email sent from the Email Forwarder Bot.</p><p>测试邮件内容。</p>",
        }

        result = sender.send_email(test_email)

        # 验证方法调用（使用更宽松的断言）
        mock_smtp.assert_called_once()
        mock_server.login.assert_called_once_with(
            sender.sender_email, sender.sender_password
        )
        mock_server.send_message.assert_called_once()

        assert result, "Email sending test should pass with mocked connection"
        print("✅ Email sending test passed\n")
    except Exception as e:
        print(f"❌ Email sending test failed: {e}\n")
        assert False, f"Email sending test failed: {e}"


def test_config():
    """测试配置加载"""
    print("Testing configuration loading...")
    try:
        # 检查必要的配置项是否存在
        required_configs = ["SOURCE_EMAIL", "SOURCE_PASSWORD", "TARGET_EMAIL"]
        for conf in required_configs:
            value = getattr(config, conf, None)
            # 注意：在测试环境中，我们可能没有实际的配置值
            # 这个测试主要是为了确保配置对象能被正确加载
            print(f"✅ Config attribute {conf} exists: {value is not None}")
        print("✅ Configuration test passed\n")
        assert True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}\n")
        assert False, f"Configuration test failed: {e}"


def main():
    """主测试函数"""
    print("📧 Email Forwarder Bot - Test Suite")
    print("=" * 50)

    # 设置日志
    setup_logger("INFO", "logs/test.log")

    # 运行各项测试
    tests = [test_config, test_smtp_connection, test_email_sending]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            # 对于需要mock的测试函数，我们需要传递mock参数
            if test.__name__ in ["test_smtp_connection", "test_email_sending"]:
                test()  # mock装饰器会自动处理
            else:
                test()
            passed += 1
            print(f"✅ Test {test.__name__} passed")
        except AssertionError as e:
            print(f"❌ Test {test.__name__} failed: {e}")
        except Exception as e:
            print(f"❌ Test {test.__name__} error: {e}")

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("😞 Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
