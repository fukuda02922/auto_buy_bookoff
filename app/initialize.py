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
from threading import Thread, Event
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter, INFO
import logging

now = datetime.now()

# ログの設定
logging.basicConfig(
    filename='test{}_{}_{}.log'.format(now.year, now.month, now.day),
    level=INFO,
    format='%(levelname)s:%(message)s'
)
logger = getLogger(__name__)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False
file_handler = FileHandler(filename='test{}_{}_{}.log'.format(now.year, now.month, now.day))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 60
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
driver_star = webdriver.Chrome(options=options)
# driver_star2 = webdriver.Chrome(options=options)

STAR_LIST = 0
CART = 0
NEW = 1

# イベント一覧
eventCart = Event()
new_count = 0
buy_count = 0
start_time = time.time()
cart_put_list = []

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
                driver_star.add_cookie(cookie)
                session.cookies.set(cookie["name"], cookie["value"])
            return
        except TimeoutException as e:
            logger.exception(f'{e}')
            continue

def cart_setting():
    driver.switch_to.window(driver.window_handles[NEW])
    driver.implicitly_wait(10)
    # カートにセッティング
    elements = driver.find_elements_by_xpath('//td[@class=\"table_goods_arrival_title\"]/a')
    for elm in elements:
        elm.click()
        driver.switch_to.window(driver.window_handles[-1])
        if driver.find_elements_by_xpath('//img[@alt=\"中古をカートに入れる\"]/..'):
            driver.find_element_by_xpath('//img[@alt=\"中古をカートに入れる\"]/..').click()
            driver.close()
            driver.implicitly_wait(0)
            return
        driver.close()
        driver.switch_to.window(driver.window_handles[NEW])

def cart_refresh():
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

def shop_select():
    session.post('https://www.bookoffonline.co.jp/disp/COdRcptStore.jsp', data={
        'submitStoreCd': '10434'
    })

def finish():
    session.post('https://www.bookoffonline.co.jp/order/COdOrderConfirmRcptStore.jsp', data={
        'BTN_CHECK': 'TempToReal',
        'ORD_UPD_INFO': '',
        'TEXT_CPN_ID': '',
        'deleteBookmarkAndAlertMail': '1',
        'omi': '62690436',
        'x': '123',
        'y': '21'
    })
    global buy_count
    buy_count += 1

def star_list(start_time):
    while True:
        logger.info('検索開始')
        # 中古在庫を50件表示で検索
        driver_star.get(MAIN_URL + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&&row=20')
        # 検索結果のリスト
        elements = driver_star.find_elements_by_xpath('//td[@class=\"buy\"]/..')
        # 検索結果が存在するか確認
        if elements:
            # 検索結果をループ
            for elm in elements:
                # カートに追加されていないか確認し、追加されていない場合に追加して終了
                if not elm.find_elements_by_class_name('incart'):
                    global new_count
                    new_count += 1
                    logger.info('在庫あり')
                    link = elm.find_element_by_xpath('td[@class=\"buy\"]/dl/dd/a').get_attribute('href')
                    try:
                        session.get(link)
                    except Exception as e:
                        logger.exception(f'{e}')
                    eventCart.set()
        if (time.time() - start_time) > PROCESS_TIME:
            eventCart.set()
            return
        time.sleep(0.1)

def buy(init_process: bool, buy_confirm: bool):
    driver.switch_to.window(driver.window_handles[CART])
    while True:
        try:
            driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
            break
        except TimeoutException as e:
            logger.exception(f'{e}')
    while True:
        if buy_confirm:
            if (time.time() - start_time) > PROCESS_TIME:
                return
            eventCart.wait()
            eventCart.clear()
            driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
        if not driver.find_elements_by_id('cartempty'):
            logger.info('購入開始')
            errors = driver.find_elements_by_xpath('//div[@class=\"error\"]/../../../td[@class=\"check\"]/input[@type=\"checkbox\"]')
            if errors:
                for error in errors:
                    error.click()
                driver.find_element_by_name('deleteSelectedButton').click()
                continue

            # ブックオフ店舗で受け取りボタンを押下
            try:
                driver.implicitly_wait(10)
                driver.find_element_by_xpath('//input[@alt=\"ブックオフ店舗で受け取る\"]').click()
                if buy_confirm:
                    driver.find_element_by_id('account')
                    finish()
                logger.info('購入完了')
            except Exception as e:
                logger.exception(f'{e}')
                logger.info('購入失敗')
            driver.implicitly_wait(0)
            if init_process:
                logger.info('セット完了')
                return

def init():
    driver.set_page_load_timeout(10)
    success_count = 0
    while True:
        try:
            if success_count == 0:
                driver.switch_to.window(driver.window_handles[NEW])
                driver.get(MAIN_URL + '/files/special/list_arrival.html')
                success_count += 1
            if success_count == 1:
                driver.switch_to.window(driver.window_handles[CART])
                driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
                success_count += 1
            driver_star.get(MAIN_URL + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&&row=20')
            return
        except TimeoutException as e:
            logger.exception(f'{e}')
        except Exception as e:
            logger.error(f'{e}')

driver.execute_script('window.open()')
# ログイン
logger.info('初期表示')
init()
logger.info('ログイン処理')
login(USER_MAIL, USER_PASS)
# 注文完了画面を表示させるためにカートと店舗を設定
logger.info('カートの設定処理開始')
cart_setting()
buy(True, False)
shop_select()
cart_refresh()
logger.info('カートの設定処理完了')

star_list_th = Thread(target=star_list, args=(start_time,))
buy_th = Thread(target=buy, args=(False, True))
# お気に入りに登録している商品で中古の在庫があればカートに保存
star_list_th.start()
buy_th.start()
star_list_th.join()
buy_th.join()
logger.info('new: {}, buy: {}'.format(new_count, buy_count))

###
# https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp
# orderMode: 5
# CART1_001: 20201015142336509489
# CART1_002: 1
# CART1_VALID_GOODS: 
# CART1_GOODS_NM: (unable to decode value)
# CART1_STOCK_TP: 1
# CART1_SALE_PR: 364
# CART1_CART_PR: 364
# CART1_005: 1
# LENGTH: 1
# OPCODE: edit_and_go
# SELECT_CARTNO: 
# SELECT_CARTSEQ: 
# SELECT_ISCD: 
# SELECT_ST: 
# ANCHOR: 
# ORDER_MODE: 
###