###
# 指定したアカウントのブックマークの中身を全て削除
# 使い方：
# 1. memNoに削除したい会員番号
# 2. USER_MAILに削除したいメールアドレス
# 3. USER_PASSに削除したいパスワード
# 4. 実行
###

from selenium import webdriver
from selenium.common.exceptions import TimeoutException

import chromedriver_binary, sys, os, traceback, requests, json
from requests import Session
from threading import Thread, Lock

USER_MAIL = 'yukiyuhkin0818@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'yuhki1212'  #ログイン時に入力するパスワード
MAIN_URL = 'https://www.bookoffonline.co.jp'
memNo = '11730214' #会員番号

session = requests.Session()

options = webdriver.chrome.options.Options()
options.add_argument('--headless')
options.add_argument('--disable-application-cache')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized')
options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=options)

iscds_list = []

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
            continue

def set_cookie(session: Session):
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

try:
    # ログイン
    login(USER_MAIL, USER_PASS)

    response = requests.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/{}'.format(memNo))
    star_list_json = json.loads(response.content)
    index = 0
    iscds = ''
    for star in star_list_json['rcptList']:
        iscds += '&iscd={}&st=1'.format(star['instorecode'])
        index += 1
        if index % 100 == 0:
            iscds_list.append(iscds)
            iscds = ''
    iscds_list.append(iscds)
    for item in iscds_list:
        session.get(MAIN_URL + '/disp/BSfDelCheckedItemsFromMyBookoff.jsp?del_type=bookmark' + item)
except Exception as e:
    traceback.print_exc()