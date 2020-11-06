from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from auto_buy_log import Log
import chromedriver_binary
import time
from datetime import datetime
import traceback
import requests
import json
from requests import Session

now = datetime.now()
log = Log('bookoff.log', now)
log.create_log()

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 60 * 2  # 処理時間
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
cartNo = ''

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
    while True:
        try:
            response = star_session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
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

def cart_update():
    star_session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
        'CART1_001': cartNo,
        'CART1_002': new_count + 1,
        'CART1_005': '1',
        'LENGTH': '1',
        'OPCODE': 'edit_and_go'
    })
    log.logger.info('カート更新完了[cartNo:{},cartSeq:{}]'.format(cartNo, new_count + 1))

def shop_select():
    star_session.post('https://www.bookoffonline.co.jp/disp/COdRcptStore.jsp', data={
        'submitStoreCd': '10434'
    })

def finish():
    response = star_session.post('https://www.bookoffonline.co.jp/order/COdOrderConfirmRcptStore.jsp', data={
        'BTN_CHECK': 'TempToReal',
        'deleteBookmarkAndAlertMail': '0'
    })
    return response.ok and response.url != 'https://www.bookoffonline.co.jp/disp/CCtViewCart_001.jsp?e=ORD_NO_STOCK_ERR'

def buy(iscd):
    global new_count
    new_count += 1
    star_session.post(MAIN_URL + '/disp/CSfAddSession_001.jsp', data={'iscd': iscd, 'st' : 1})
    log.logger.info('カート追加完了[{}]'.format(iscd))

def star_list(start_time):
    global star_session
    while True:
        log.logger.info('検索開始')
        try:
            response = star_session.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/' + memNo)  # エラー
        except Exception as e:
            log.logger.exception(f'{e}')
            continue
        log.logger.info('検索完了')
        star_list_json = json.loads(response.content)
        isCdList = []
        for rcpt in star_list_json['rcptList']:
            if rcpt['rcpt_flg'] == 'true':
                isCdList.append(rcpt['instorecode'])

        if isCdList:
            for iscd in isCdList:
                buy(iscd)
                cart_update()
                if finish():
                    log.logger.info('購入完了')
                    global buy_count
                    buy_count += 1
                else:
                    log.logger.info('購入失敗')
                    cart_refresh()
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

    star_list(start_time)
    log.logger.info('new: {}, buy: {}'.format(new_count, buy_count))
except Exception as e:
    log.logger.exception(f'{e}')