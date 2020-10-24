from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

import chromedriver_binary
import time
from datetime import datetime
import sys
import traceback
import requests
from bs4 import BeautifulSoup
from threading import Thread, Lock
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter, INFO
import logging

now = datetime.now()

# ログの設定
logging.basicConfig(
    filename='log/test{}_{}_{}.log'.format(now.year, now.month, now.day),
    level=INFO,
    format='%(levelname)s:%(message)s'
)
logger = getLogger(__name__)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False
file_handler = FileHandler(filename='log/test{}_{}_{}.log'.format(now.year, now.month, now.day))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 60 * 2  # 処理時間
STAR_LIST_INTERNAL_TIME = 2 # お気に入りの検索時間の間隔
MAIN_URL = 'https://www.bookoffonline.co.jp'

# chromeのアドレスバーに「chrome://version/」を入力して、そのプロフィールパス
# USER_DATA_DIR = 'UserData'
# USER_DATA_DIR = '/Users/y.fukuda/Library/Application Support/Google/Chrome/Default/Default'

session = requests.session()
options = webdriver.chrome.options.Options()
options.add_argument('--headless')
options.add_argument('--disable-application-cache')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized')
options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=options)
# driver_star = webdriver.Chrome(options=options)
# driver_star2 = webdriver.Chrome(options=options)

STAR_LIST = 0
CART = 0
NEW = 1

new_count = 0
buy_count = 0
start_time = time.time()
cart_put_list = []
cartNo = ''
lock = Lock()
next_process_star = 0
wait_time = time.time()
cart_refreshing = False

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
            for cookie in driver.get_cookies():
                # driver_star.add_cookie(cookie)
                session.cookies.set(cookie["name"], cookie["value"])
            return
        except TimeoutException as e:
            logger.exception(f'{e}')
            continue

def cart_setting():
    driver.switch_to.window(driver.window_handles[NEW])
    driver.get(MAIN_URL + '/files/special/list_arrival.html')
    driver.implicitly_wait(10)
    # カートにセッティング
    elements = driver.find_elements_by_xpath('//td[@class=\"table_goods_arrival_title\"]/a')
    for elm in elements:
        elm.click()
        driver.switch_to.window(driver.window_handles[-1])
        if driver.find_elements_by_xpath('//img[@alt=\"中古をカートに入れる\"]/..') and driver.find_elements_by_xpath('//div[@class=\"htmlinclrcpt\" and @style=\"display: block;\"]'):
            driver.find_element_by_xpath('//img[@alt=\"中古をカートに入れる\"]/..').click()
            driver.close()
            driver.implicitly_wait(0)
            return
        driver.close()
        driver.switch_to.window(driver.window_handles[NEW])

def cart_refresh():
    cart_refreshing = True
    driver.switch_to.window(driver.window_handles[CART])
    while True:
        try:

            driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
            elements = driver.find_elements_by_xpath('//input[@src=\"../images/parts/pgs/b_delete110203.gif?20180803\"]')
            if elements:
                elements[0].click()
            else:
                return
        except Exception as e:
            logger.exception(f'{e}')
            continue
    cart_refreshing = False

def cart_update(cart_no_seq):
    session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
        'orderMode': '5',
        'CART1_001': cartNo,
        'CART1_002': cart_no_seq + 1,
        'CART1_VALID_GOODS': '',
        'CART1_GOODS_NM': '(unable to decode value)',
        'CART1_STOCK_TP': '1',
        'CART1_SALE_PR': '364',
        'CART1_CART_PR': '364',
        'CART1_005': '1',
        'LENGTH': '1',
        'OPCODE': 'edit_and_go',
        'SELECT_CARTNO': '',
        'SELECT_CARTSEQ': '',
        'SELECT_ISCD': '',
        'SELECT_ST': '',
        'ANCHOR': '',
        'ORDER_MODE': ''
    })

def shop_select():
    session.post('https://www.bookoffonline.co.jp/disp/COdRcptStore.jsp', data={
        'submitStoreCd': '10434'
    })

def finish():
    response = session.post('https://www.bookoffonline.co.jp/order/COdOrderConfirmRcptStore.jsp', data={
        'BTN_CHECK': 'TempToReal',
        'ORD_UPD_INFO': '',
        'TEXT_CPN_ID': '',
        'deleteBookmarkAndAlertMail': '0',
        'omi': '62690436',
        'x': '123',
        'y': '21'
    })
    return response.ok

def buy(link):
    lock.acquire()
    cart_no_seq = 0
    if not (link in cart_put_list):
        cart_put_list.append(link)
        global new_count
        new_count += 1
        cart_no_seq = new_count
        session.get(MAIN_URL + link.replace('..', ''))
    lock.release()
    return cart_no_seq

def next_process_count(index):
    global next_process_star
    if index == 8:
        next_process_star = 0
    else:
        next_process_star += 1

def star_list(start_time, index):
    global next_process_star
    global wait_time
    while True:
        if not cart_refreshing:
            # 中古在庫を20件表示で検索
            if ((next_process_star == index) and (time.time() - wait_time) > STAR_LIST_INTERNAL_TIME):
                wait_time = time.time()
                next_process_count(index)
                logger.info('検索開始{}'.format(index))
                response = session.get(MAIN_URL + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&&row=20') # エラー
                soup = BeautifulSoup(response.content, 'html.parser')
                olds = soup.find_all("img", alt="中古をカートに入れる")
                for old in olds:
                    link = old.parent['href']
                    cart_no_seq = buy(link)
                    if not cart_no_seq == 0:
                        logger.info('購入開始{}'.format(index))
                        cart_update(cart_no_seq)
                        if finish():
                            logger.info('購入完了')
                            global buy_count
                            buy_count += 1
                        else:
                            logger.info('購入失敗')
                            cart_refresh()
            elif (time.time() - wait_time) > (STAR_LIST_INTERNAL_TIME + 3):
                wait_time = time.time()
                next_process_count(index)
        if (time.time() - start_time) > PROCESS_TIME:
            return

def buy_init():
    while True:
        logger.info('セット開始')
        driver.switch_to.window(driver.window_handles[CART])
        while True:
            try:
                driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
                break
            except TimeoutException as e:
                logger.exception(f'{e}')
        errors = driver.find_elements_by_xpath('//div[@class=\"error\"]/../../../td[@class=\"check\"]/input[@type=\"checkbox\"]')
        if errors:
            for error in errors:
                error.click()
            driver.find_element_by_name('deleteSelectedButton').click()
            continue

        # ブックオフ店舗で受け取りボタンを押下
        try:
            global cartNo
            driver.implicitly_wait(10)
            cartNo = driver.find_element_by_name('CART1_001').get_attribute('value')
            # driver.find_element_by_xpath('//input[@alt=\"ブックオフ店舗で受け取る\"]').click()
            logger.info('セット完了')
            driver.implicitly_wait(0)
            return
        except Exception as e:
            logger.exception(f'{e}')
            logger.info('セット失敗')

driver.execute_script('window.open()')
try:
    # ログイン
    logger.info('ログイン処理')
    login(USER_MAIL, USER_PASS)
    # 注文完了画面を表示させるためにカートと店舗を設定
    logger.info('カートの設定処理開始')
    cart_setting()
    buy_init()
    shop_select()
    cart_refresh()
    logger.info('カートの設定処理完了')

    # スレッドの定義
    th_pool = [Thread(target=star_list, args=(start_time, index)) for index in range(9)]

    # スレッド開始
    for th in th_pool:
        th.start()
        time.sleep(1)

    #スレッドの完了待ち
    for th in th_pool:
        th.join()
    logger.info('new: {}, buy: {}'.format(new_count, buy_count))
except Exception as e:
    logger.exception(f'{e}')