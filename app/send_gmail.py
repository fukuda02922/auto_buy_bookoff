import os, os.path
import glob
import zipfile, tempfile
from smtplib import SMTP
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from auto_buy_log import Log

def sendGmailAttach():
    now = datetime.now()
    # パスワードは「https://www.gocca.work/python-mailerror/」の二段階認証手順で取得したパスワードを設定
    sender, password = "hogehoge@gmail.com", "pass" # 送信元メールアドレスとgmailへのログイン情報 
    to = 'yuki.mirai029@gmail.com'  # 送信先メールアドレス
    sub = 'ブックオフオンラインのログ{}_{}_{}'.format(now.year, now.month, now.day) #メール件名
    body = 'ログを添付しています。'  # メール本文
    host, port = 'smtp.gmail.com', 587

    # メールヘッダー
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = sender
    msg['To'] = to

    # メール本文
    body = MIMEText(body)
    msg.attach(body)

    # 添付ファイルの設定
    log = Log('bookoff.log', now)
    fetch_from_dir = glob.glob(log.log_dir_name + '*')
    temp = tempfile.TemporaryFile()
    attachment = MIMEBase('application', 'zip')
    with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for target_list in fetch_from_dir:
            zip_file.write(target_list, arcname= os.path.basename(target_list))
        temp.seek(0)
        attachment.set_payload(temp.read())
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename='result.zip')
    msg.attach(attachment)

    # gmailへ接続(SMTPサーバーとして使用)
    gmail = SMTP("smtp.gmail.com", 587)
    gmail.starttls() # SMTP通信のコマンドを暗号化し、サーバーアクセスの認証を通す
    gmail.login(sender, password)
    gmail.send_message(msg)
    gmail.close()
    print('メールが送信されました')


if __name__ == '__main__':
    sendGmailAttach()