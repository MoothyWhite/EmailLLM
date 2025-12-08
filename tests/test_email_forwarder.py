#!/usr/bin/env python3
"""
邮件转发机器人测试脚本
"""

import sys
from pathlib import Path

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


def test_config():
    """测试配置加载"""
    print("Testing configuration loading...")
    try:
        # 检查必要的配置项是否存在
        required_configs = ["SOURCE_EMAIL", "SOURCE_PASSWORD", "TARGET_EMAIL"]
        for conf in required_configs:
            value = getattr(config, conf, None)
            if not value:
                print(f"❌ Missing required config: {conf}")
                return False
            print(f"✅ {conf}: {'*' * len(value) if 'PASSWORD' in conf else value}")
        print("✅ Configuration test passed\n")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}\n")
        return False


def test_smtp_connection():
    """测试SMTP连接"""
    print("Testing SMTP connection...")
    try:
        sender = MailSender()
        if sender.test_connection():
            print("✅ SMTP connection test passed\n")
            return True
        else:
            print("❌ SMTP connection test failed\n")
            return False
    except Exception as e:
        print(f"❌ SMTP connection test failed: {e}\n")
        return False


def test_email_sending():
    """测试邮件发送功能"""
    print("Testing email sending...")
    try:
        sender = MailSender()

        # 创建测试邮件
        test_email = {
            "subject": "Test Email from Email Forwarder Bot",
            "sender": config.SOURCE_EMAIL,
            "receiver": config.TARGET_EMAIL,
            "body_text": "This is a test email sent from the Email Forwarder Bot.\n\n测试邮件内容。",
            "body_html": "<h1>Test Email from Email Forwarder Bot</h1><p>This is a test email sent from the Email Forwarder Bot.</p><p>测试邮件内容。</p>",
        }

        if sender.send_email(test_email):
            print("✅ Email sending test passed\n")
            return True
        else:
            print("❌ Email sending test failed\n")
            return False
    except Exception as e:
        print(f"❌ Email sending test failed: {e}\n")
        return False


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
        if test():
            passed += 1

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
