###
# 指定したアカウントのブックマークに商品リストを追加する
# 使い方：
# 1. FILE_NAMEに追加したい商品リストのcsvファイル名
# 2. USER_MAILに削除したいメールアドレス
# 3. USER_PASSに削除したいパスワード
# 4. 実行
#
# 備考：
# アカウントごとに商品リストのCSVファイルを作成していた方が後で管理しやすいです。
###


from selenium import webdriver
from selenium.common.exceptions import TimeoutException

import chromedriver_binary, sys, os, traceback, requests, csv
from requests import Session
from threading import Thread, Lock

USER_MAIL = '...@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = '...'  #ログイン時に入力するパスワード
TH_COUNT = 100 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
FILE_NAME = 'bookmark_1.csv'

session = requests.Session()

options = webdriver.chrome.options.Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

filename = os.path.dirname(__file__) + '/bookmark/' + FILE_NAME
if not os.path.exists(filename):
    print('ブックマークに追加するリストがありません')
    sys.exit(0)

iscd_list = []
iscds = ''
count = 0
lock = Lock()

def login(id, password):
    while True:
        try:
            driver.get(MAIN_URL + '/common/CSfLogin.jsp')
            elmId = driver.find_element_by_name('ID')
            elmId.send_keys(id)
            elmPass = driver.find_element_by_name('PWD')
            elmPass.send_keys(password)
            loginBtn = driver.find_element_by_xpath('//input[@alt=\"ログイン\"]')
            loginBtn.click()
            set_cookie(session)
            return
        except TimeoutException as e:
            log.logger.exception(f'{e}')
            continue

def set_cookie(session: Session):
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])


def next_count():
    global count
    count += 1
    return count

def run_thread():
    while True:
        lock.acquire()
        index = next_count()
        lock.release()
        if (index + 1) > len(iscd_list):
            return
        try:
            print(index)
            session.get(MAIN_URL + '/member/BPmAddBookMark.jsp?iscd={}&st=1'.format(iscd_list[index]))  # エラー
        except Exception as e:
            log.logger.exception(f'{e}')
            continue

try:
    # ログイン
    login(USER_MAIL, USER_PASS)

    with open(filename, 'r') as f:
        r = csv.reader(f)
        for line in r:
            iscd_list.append(line[8].replace('"', '').replace('=', ''))

    # お気に入り登録スレッドの定義
    th_pool = [Thread(target=run_thread) for index in range(TH_COUNT)]

    # スレッド開始
    for th in th_pool:
        th.start()
        time.sleep(1)

    #スレッドの完了待ち
    for th in th_pool_star:
        th.join()
    # os.remove(filename_after)
except Exception as e:
    pass