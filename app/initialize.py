from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
from auto_buy_log import Log

import chromedriver_binary
import time
from datetime import datetime
import sys
import traceback
import requests
import json
from requests import Session
from threading import Thread, Lock, Event

now = datetime.now()
log = Log('bookoff.log', now)
log.create_log()

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 60 * 1  # 処理時間
STAR_LIST_INTERNAL_TIME = 0  # お気に入りの検索時間の間隔
TH_COUNT = 1 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
### 会員番号
# 以下の手順で設定する
# 1. ログインしてお気に入り画面を開く
# 2. F12キーなどでデベロッパーツールを表示
# 3. Networkタブを開く
# 4. 左上にあるテキストボックス(filter)に「api」と入力する
# 5. リロードする
# 6. Nameエリアに数字だけ表示されている通信があるので、それを設定する(urlはhttps://www.bookoffonline.co.jp/spf-api2/goods_souko/bookmark/.....)
memNo = '8763947'

star_session = requests.Session()
buy_session = requests.Session()

options = webdriver.chrome.options.Options()
options.add_argument('--headless')
options.add_argument('--disable-application-cache')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized')
options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=options)

STAR_LIST = 0
CART = 0
NEW = 1

new_count = 0
buy_count = 0
start_time = time.time()
buy_put_list = []
cartNo = ''
lock = Lock()
lock_buy = Lock()
next_process_star = 0
wait_time = time.time()
cart_refreshing = False
buy_processing = False
buy_event = Event()
star_event = Event()
cart_check = False

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
            set_cookie(star_session)
            set_cookie(buy_session)
            return
        except TimeoutException as e:
            log.logger.exception(f'{e}')
            continue

def set_cookie(session: Session):
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

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
    while True:
        try:
            response = buy_session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
                'CART1_001': cartNo,
                'CART1_002': new_count + 1,
                'CART1_GOODS_NM': '(unable to decode value)',
                'CART1_STOCK_TP': '1',
                'CART1_SALE_PR': '364',
                'CART1_CART_PR': '364',
                'CART1_005': '1',
                'LENGTH': '1',
                'OPCODE': 'clear',
            })
            if response.ok:
                break
        except Exception as e:
            log.logger.exception(f'{e}')
    cart_refreshing = False

def cart_update():
    buy_session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
        'CART1_001': cartNo,
        'CART1_002': new_count + 1,
        'CART1_005': '1',
        'LENGTH': '1',
        'OPCODE': 'edit_and_go'
    })
    log.logger.info('カート更新完了[cartNo:{},cartSeq:{}]'.format(cartNo, new_count + 1))

def shop_select():
    buy_session.post('https://www.bookoffonline.co.jp/disp/COdRcptStore.jsp', data={
        'submitStoreCd': '10434'
    })

def finish():
    response = buy_session.post('https://www.bookoffonline.co.jp/order/COdOrderConfirmRcptStore.jsp', data={
        'BTN_CHECK': 'TempToReal',
        'deleteBookmarkAndAlertMail': '0'
    })
    return response.ok and response.url != 'https://www.bookoffonline.co.jp/disp/CCtViewCart_001.jsp?e=ORD_NO_STOCK_ERR'

def buy(iscd):
    global new_count
    new_count += 1
    global cart_check
    cart_check = True
    buy_session.post(MAIN_URL + '/disp/CSfAddSession_001.jsp', data={'iscd': iscd, 'st' : 1})
    log.logger.info('カート追加完了[{}]'.format(iscd))

def next_process_count(index):
    global next_process_star
    if index == TH_COUNT - 1:
        next_process_star = 0
    else:
        next_process_star += 1

def run_thread(start_time, index):
    global next_process_star
    global wait_time
    global buy_processing
    global star_session
    global buy_session
    while True:
        if buy_processing:
            star_event.wait()
            star_event.clear()
            if cart_check:
                check_cart()
                continue
        if (not cart_refreshing):
            # 中古在庫を20件表示で検索
            if ((next_process_star == index) and (time.time() - wait_time) > STAR_LIST_INTERNAL_TIME):
                wait_time = time.time()
                next_process_count(index)
                log.logger.info('検索開始{}'.format(index))
                try:
                    response = star_session.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/' + memNo)  # エラー
                except Exception as e:
                    log.logger.exception(f'{e}')
                    continue
                log.logger.info('検索結果{}'.format(index))
                star_list_json = json.loads(response.content)
                isCdList = []
                for rcpt in star_list_json['rcptList']:
                    if rcpt['rcpt_flg'] == 'true':
                        isCdList.append(rcpt['instorecode'])
                lock.acquire()
                if isCdList and (not buy_processing):
                    buy_processing = True
                    lock.release()
                    for iscd in isCdList:
                        buy_event.set()
                        buy(iscd)
                        star_event.wait()
                        star_event.clear()
                    buy_processing = False
                    star_event.set()
                if lock.locked():
                    lock.release()
            elif (time.time() - wait_time) > (STAR_LIST_INTERNAL_TIME + 3):
                wait_time = time.time()
                next_process_count(index)
        if (time.time() - start_time) > PROCESS_TIME:
            return

def check_cart(start_time):
    global cart_check
    while True:
        response = star_session.get(MAIN_URL + '/spf-api2/goods_souko/cart/{}/{}'.format(cartNo, memNo))
        carts = json.loads(response.content)
        if 'rcptList' in carts:
            cart_check = False
            log.logger.info('カート追加確認')
            return
        elif not cart_check:
            return
        elif (time.time() - start_time) > PROCESS_TIME:
            return

# 購入処理（カート更新 -> 確定）
def main_buy(start_time, index):
    while True:
        buy_event.wait()
        buy_event.clear()
        check_cart(start_time)
        lock_buy.acquire()
        if not (new_count in buy_put_list):
            buy_put_list.append(new_count)
            lock_buy.release()
            log.logger.info('購入開始{}'.format(index))
            cart_update()
            if finish():
                log.logger.info('購入完了')
                global buy_count
                buy_count += 1
            else:
                log.logger.info('購入失敗')
                cart_refresh()
            star_event.set()
        if lock_buy.locked():
            lock_buy.release()
        if (time.time() - start_time) > PROCESS_TIME:
            return

def buy_init():
    while True:
        log.logger.info('セット開始')
        driver.switch_to.window(driver.window_handles[CART])
        while True:
            try:
                driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
                break
            except TimeoutException as e:
                log.logger.exception(f'{e}')
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
            log.logger.info('セット完了')
            driver.implicitly_wait(0)
            return
        except Exception as e:
            log.logger.exception(f'{e}')
            log.logger.info('セット失敗')

driver.execute_script('window.open()')
try:
    # ログイン
    log.logger.info('ログイン処理')
    login(USER_MAIL, USER_PASS)
    # 注文完了画面を表示させるためにカートと店舗を設定
    log.logger.info('カートの設定処理開始')
    cart_setting()
    buy_init()
    shop_select()
    cart_refresh()
    log.logger.info('カートの設定処理完了')

    # お気に入り検索スレッドの定義
    th_pool_star = [Thread(target=run_thread, args=(start_time, index)) for index in range(TH_COUNT)]

    # 購入スレッドの定義
    th_pool_buy = [Thread(target=main_buy, args=(start_time, index)) for index in range(1)]

    # スレッド開始
    for th in th_pool_star:
        th.start()
        time.sleep(1)

    # スレッド開始
    for th in th_pool_buy:
        th.start()
        time.sleep(1)

    #スレッドの完了待ち
    for th in th_pool_star:
        th.join()

    #スレッドの完了待ち
    for th in th_pool_buy:
        th.join()
    log.logger.info('new: {}, buy: {}'.format(new_count, buy_count))
except Exception as e:
    log.logger.exception(f'{e}')