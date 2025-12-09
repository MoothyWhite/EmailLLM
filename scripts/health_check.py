from imapclient import IMAPClient  # type: ignore
import smtplib
import ssl

IMAP_HOST = "imap.qq.com"
IMAP_PORT = 993

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465

SOURCE_EMAIL = "sss"
SOURCE_PASSWORD = "xxx"
DEST_EMAIL = "xxx"


def main():
    ssl_ctx = ssl.create_default_context()

    # 1. IMAP 连接（读取邮件）
    with IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True, ssl_context=ssl_ctx) as client:
        print("连接并登录 IMAP…")
        client.login(SOURCE_EMAIL, SOURCE_PASSWORD)

        client.select_folder("INBOX")
        uids = client.search("UNSEEN")
        print("未读邮件：", uids)

        # 2. SMTP 连接（发送转发邮件）
        smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        smtp.login(SOURCE_EMAIL, SOURCE_PASSWORD)

        for uid in uids:
            # 取得原始 RFC822（字节流）
            raw_message = client.fetch([uid], ["RFC822"])[uid][b"RFC822"]

            smtp.sendmail(SOURCE_EMAIL, DEST_EMAIL, raw_message)

            print(f"已转发 UID {uid}")

            # 标记已读
            client.add_flags([uid], [b"\\Seen"])

        smtp.quit()


if __name__ == "__main__":
    main()
