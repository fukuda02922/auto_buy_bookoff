from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions


import chromedriver_binary
import time
import sys
import traceback
import requests
from threading import Thread, Event

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 60
MAIN_URL = 'https://www.bookoffonline.co.jp'

# chromeのアドレスバーに「chrome://version/」を入力して、そのプロフィールパス
# USER_DATA_DIR = 'UserData'
# USER_DATA_DIR = '/Users/y.fukuda/Library/Application Support/Google/Chrome/Default/Default'

session = requests.session()
options = webdriver.chrome.options.Options()
# options = webdriver.firefox.options.Options()
# options.add_argument('--user-data-dir={}'.format(USER_DATA_DIR))
# options.add_argument('--headless')
options.add_argument('--disable-application-cache')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)
driver_star = webdriver.Chrome(options=options)
# driver = webdriver.Firefox(options=options)

STAR_LIST = 0
CART = 0
# BUY = 2
NEW = 1

# イベント一覧
eventCart = Event()
new_count = 0
buy_count = 0

def login(id, password):
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

def cart_setting():
    driver.switch_to.window(driver.window_handles[NEW])
    driver.implicitly_wait(10)
    # カートにセッティング
    elements = driver.find_elements_by_xpath('//td[@class=\"table_goods_arrival_title\"]/a')
    for elm in elements:
        elm.click()
        driver.switch_to.window(driver.window_handles[-1])
        if not driver.find_elements_by_xpath('//li[contains(text(), "{0}")]'.format('在庫がありません')):
            driver.find_element_by_xpath('//img[@alt=\"中古をカートに入れる\"]/..').click()
            driver.close()
            driver.implicitly_wait(0)
            return
        driver.close()
        driver.switch_to.window(driver.window_handles[NEW])

def cart_refresh():
    driver.switch_to.window(driver.window_handles[CART])
    driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
    while True:
        elements = driver.find_elements_by_xpath('//input[@src=\"../images/parts/pgs/b_delete110203.gif?20180803\"]')
        if elements:
            elements[0].click()
        else:
            return

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
        print('検索開始')
        # 中古在庫を50件表示で検索
        # driver_star.switch_to.window(driver.window_handles[STAR_LIST])
        driver_star.refresh()
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
                    print('中古在庫あり')
                    link = elm.find_element_by_xpath('td[@class=\"buy\"]/dl/dd/a').get_attribute('href')
                    session.get(link)
                    eventCart.set()
                    # driver.execute_script('window.open()')
                    # driver.switch_to.window(driver.window_handles[-1])
                    # driver.get(link)
                    # message = ""
                    # while True:
                    #     try:
                    #         message = Alert(driver).text
                    #         Alert(driver).accept()
                    #         driver.close()
                    #         break
                    #     except Exception:
                    #         traceback.print_exc()
                    #         time.sleep(0.1)
                    # driver.switch_to.window(driver.window_handles[STAR_LIST])
                    # if message == '選択した商品をカートに入れました\n画面右上の「カートをみる」でカートの中身が確認できます':
                    #     print('カートに追加')
                    #     return
        if (time.time() - start_time) > PROCESS_TIME:
            eventCart.set()
            return
        print('2秒後に再表示')
        time.sleep(2)

def buy(init_process: bool, buy_confirm: bool):
    driver.switch_to.window(driver.window_handles[CART])
    driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
    while True:
        if buy_confirm:
            if (time.time() - start_time) > PROCESS_TIME:
                return
            eventCart.wait()
            eventCart.clear()
            driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
        if not driver.find_elements_by_id('cartempty'):
            print('購入開始')
            # 別ウィンドウでカートを開く
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
            except Exception:
                traceback.print_exc()
                print('購入失敗')
            driver.implicitly_wait(0)
            if init_process:
                print('セット完了')
                return

    # 店舗選択を確定
    # if init_process:
    #     shop_select()
        # try:
        #     driver.find_element_by_xpath('//div[@class="shop-receive-btn js_receive_btn_select"]/span[contains(text(), "{0}")]'.format("選択した店舗で支払・受取をする")).click()
        # except Exception:
        #     print('購入失敗')
        #     traceback.print_exc()
        #     driver.implicitly_wait(0)
        #     if driver.find_elements_by_xpath('//span[contains(text(), "{0}")]'.format('店舗受取できない商品を')):
        #         driver.find_elements_by_xpath('//span[contains(text(), "{0}")]'.format('店舗受取できない商品を'))[0].parent().click()
        #     return

    # 注文確定ボタンを押下
    # if (buy_confirm):
    #     finish()
        # driver.switch_to.window(driver.window_handles[BUY])
        # try:
        #     driver.find_element_by_id('tempToReal').click()
        # except Exception:
        #     traceback.print_exc()
        #     print('購入失敗')
        #     try:
        #         Alert(driver).accept()
        #     except:
        #         print('アラートなし')
        #     driver.implicitly_wait(0)
        #     return
        # if (driver.find_elements_by_xpath('//div[contains(text(), "{0}")]'.format('ご注文ありがとうございました'))):
        #     print('購入完了')
        # else:
        #     print('購入失敗')
        # driver.back()

def init():
    driver.set_page_load_timeout(20)
    while True:
        try:
            driver.switch_to.window(driver.window_handles[NEW])
            driver.get(MAIN_URL + '/files/special/list_arrival.html')
            # driver.switch_to.window(driver.window_handles[BUY])
            # driver.get(MAIN_URL + '/order/COdOrderConfirmRcptStore.jsp')
            driver.switch_to.window(driver.window_handles[CART])
            driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
            # driver.switch_to.window(driver.window_handles[STAR_LIST])
            driver_star.get(MAIN_URL + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&&row=20')
            return
        except Exception as e:
            traceback.print_exc()
    return



driver.execute_script('window.open()')
# driver.execute_script('window.open()')
# ログイン
init()
login(USER_MAIL, USER_PASS)
# 注文完了画面を表示させるためにカートと店舗を設定
print('カートの設定処理開始')
cart_setting()
buy(True, False)
shop_select()
cart_refresh()
# driver.switch_to.window(driver.window_handles[BUY])
# driver.refresh()
print('カートの設定処理完了')
start_time = time.time()
star_list_th = Thread(target=star_list, args=(start_time,))
buy_th = Thread(target=buy, args=(False, True))
# while True:
# お気に入りに登録している商品で中古の在庫があればカートに保存
star_list_th.start()
# star_list(start_time)
# 購入処理
# buy(False, True)
buy_th.start()
# print('カートの設定処理開始')
# cart_setting()
# buy(True, False)
# cart_refresh()
# driver.switch_to.window(driver.window_handles[BUY])
# driver.refresh()
# print('カートの設定処理完了')
# if (time.time() - start_time) > PROCESS_TIME:
#     sys.exit(0)
print('new: {}, buy: {}'.format(new_count, buy_count))


### 購入完了ボタン
# https://www.bookoffonline.co.jp/order/COdOrderConfirmRcptStore.jsp
# BTN_CHECK: TempToReal
# ORD_UPD_INFO: 
# TEXT_CPN_ID: 
# deleteBookmarkAndAlertMail: 1
# omi: 62690436
# x: 123
# y: 21
###

### カート
# https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp
# orderMode: 5
# CART1_001: 20201012153652785807
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

### 店舗選択
# https://www.bookoffonline.co.jp/disp/COdRcptStore.jsp
# submitStoreCd: 10434

#../disp/CSfAddSession_001.jsp?iscd=0019509466&st=1&trans_fl=1&transfer=%2Fdisp%2FBSfDispBookMarkAlertMailInfo.jsp%3Fss%3Du%26ml%3D0%26ct%3D00%26sk%3D10%26row%3D20&anchor=anchor_link_1