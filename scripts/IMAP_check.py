import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置
from app.config import config

from imapclient import IMAPClient  # type: ignore
import smtplib
import ssl


def main():
    ssl_ctx = ssl.create_default_context()

    # 1. IMAP 连接（读取邮件）
    with IMAPClient(
        config.SOURCE_IMAP_SERVER,
        port=config.SOURCE_IMAP_PORT,
        ssl=True,
        ssl_context=ssl_ctx,
    ) as client:
        print("连接并登录 IMAP…")
        client.login(config.SOURCE_EMAIL, config.SOURCE_PASSWORD)

        client.select_folder("INBOX")
        uids = client.search("UNSEEN")
        print("未读邮件：", uids)

        # 2. SMTP 连接（发送转发邮件）
        smtp = smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT)
        smtp.login(config.SOURCE_EMAIL, config.SMTP_PASSWORD or config.SOURCE_PASSWORD)

        for uid in uids:
            # 取得原始 RFC822（字节流）
            raw_message = client.fetch([uid], ["RFC822"])[uid][b"RFC822"]

            smtp.sendmail(config.SOURCE_EMAIL, config.TARGET_EMAIL, raw_message)

            print(f"已转发 UID {uid}")

            # 标记已读
            client.add_flags([uid], [b"\\Seen"])

        smtp.quit()


if __name__ == "__main__":
    main()
