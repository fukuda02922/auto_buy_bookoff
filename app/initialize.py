from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions


import chromedriver_binary
import time
import sys
import traceback

USER_MAIL = '' #ログイン時に入力するメールアドレス
USER_PASS = ''  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 30
# chromeのアドレスバーに「chrome://version/」を入力して、そのプロフィールパス
# USER_DATA_DIR = 'UserData'
# USER_DATA_DIR = '/Users/y.fukuda/Library/Application Support/Google/Chrome/Default/Default'

options = webdriver.chrome.options.Options()
# options.add_argument('--user-data-dir={}'.format(USER_DATA_DIR))
options.add_argument('--headless')
options.add_argument('--disable-application-cache')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

STAR_LIST = 0
CART = 1
BUY = 2
NEW = 3

MAIN_URL = 'https://www.bookoffonline.co.jp'

def login(id, password):
    driver.get(MAIN_URL + '/common/CSfLogin.jsp')
    elmId = driver.find_element_by_name('ID')
    elmId.send_keys(id)
    elmPass = driver.find_element_by_name('PWD')
    elmPass.send_keys(password)
    loginBtn = driver.find_element_by_xpath('//input[@alt=\"ログイン\"]')
    loginBtn.click()

def cart_setting():
    driver.switch_to.window(driver.window_handles[NEW])
    driver.implicitly_wait(10)
    # カートにセッティング
    elements = driver.find_elements_by_xpath('//td[@class=\"table_goods_arrival_title\"]/a')
    for elm in elements:
        elm.click()
        driver.switch_to.window(driver.window_handles[-1])
        if driver.find_elements_by_class_name('shop-receive-support-img'):
            driver.find_element_by_xpath('//img[@alt=\"中古をカートに入れる\"]/..').click()
            driver.close()
            driver.implicitly_wait(0)
            return
        driver.switch_to.window(driver.window_handles[NEW])

def cart_refresh():
    driver.switch_to.window(driver.window_handles[CART])
    driver.refresh()
    while True:
        elements = driver.find_elements_by_xpath('//input[@src=\"../images/parts/pgs/b_delete110203.gif?20180803\"]')
        if elements:
            elements[0].click()
            return

def star_list(start_time):
    while True:
        print('検索開始')
        # 中古在庫を50件表示で検索
        driver.switch_to.window(driver.window_handles[STAR_LIST])
        driver.refresh()
        # 検索結果のリスト
        elements = driver.find_elements_by_xpath('//td[@class=\"buy\"]/..')
        # 検索結果が存在するか確認
        if elements:
            # 検索結果をループ
            for elm in elements:
                # カートに追加されていないか確認し、追加されていない場合に追加して終了
                if not elm.find_elements_by_class_name('incart'):
                    print('中古在庫あり')
                    link = elm.find_element_by_xpath('td[@class=\"buy\"]/dl/dd/a').get_attribute('href')
                    driver.execute_script('window.open()')
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get(link)
                    message = ""
                    while True:
                        try:
                            message = Alert(driver).text
                            Alert(driver).accept()
                            driver.close()
                            break
                        except Exception:
                            traceback.print_exc()
                            time.sleep(0.1)
                    driver.switch_to.window(driver.window_handles[STAR_LIST])
                    if message == '選択した商品をカートに入れました\n画面右上の「カートをみる」でカートの中身が確認できます':
                        print('カートに追加')
                        return
        if (time.time() - start_time) > PROCESS_TIME:
            sys.exit(0)
        print('2秒後に再表示')
        time.sleep(2)

def buy(init_process: bool, buy_confirm: bool):
    print('購入開始')
    # 別ウィンドウでカートを開く
    driver.switch_to.window(driver.window_handles[CART])
    driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
    errors = driver.find_elements_by_xpath('//div[@class=\"error\"]/../../../td[@class=\"check\"]/input[@type=\"checkbox\"]')
    if errors:
        for error in errors:
            error.click()
        driver.find_element_by_name('deleteSelectedButton').click()
    driver.implicitly_wait(10)

    # ブックオフ店舗で受け取りボタンを押下
    try:
        driver.find_element_by_xpath('//input[@alt=\"ブックオフ店舗で受け取る\"]').click()
    except Exception:
        traceback.print_exc()
        print('購入失敗')
        driver.implicitly_wait(0)
        return

    # 店舗選択を確定
    if init_process:
        try:
            driver.find_element_by_xpath('//div[@class="shop-receive-btn js_receive_btn_select"]/span[contains(text(), "{0}")]'.format("選択した店舗で支払・受取をする")).click()
        except Exception:
            print('購入失敗')
            traceback.print_exc()
            driver.implicitly_wait(0)
            if driver.find_elements_by_xpath('//span[contains(text(), "{0}")]'.format('店舗受取できない商品を')):
                driver.find_elements_by_xpath('//span[contains(text(), "{0}")]'.format('店舗受取できない商品を'))[0].parent().click()
            return

    # 注文確定ボタンを押下
    if (buy_confirm):
        driver.switch_to.window(driver.window_handles[BUY])
        driver.get(MAIN_URL + '/order/COdOrderConfirmRcptStore.jsp')
        try:
            driver.find_element_by_id('tempToReal').click()
        except Exception:
            traceback.print_exc()
            print('購入失敗')
            try:
                Alert(driver).accept()
            except:
                print('アラートなし')
            driver.implicitly_wait(0)
            return
        if (driver.find_elements_by_xpath('//div[contains(text(), "{0}")]'.format('ご注文ありがとうございました'))):
            print('購入完了')
        else:
            print('購入失敗')
    driver.implicitly_wait(0)
    driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')

def init():
    driver.switch_to.window(driver.window_handles[STAR_LIST])
    driver.get(MAIN_URL + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50')
    driver.execute_script('window.open()')
    driver.switch_to.window(driver.window_handles[CART])
    driver.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
    driver.execute_script('window.open()')
    driver.switch_to.window(driver.window_handles[BUY])
    driver.get(MAIN_URL + '/order/COdOrderConfirmRcptStore.jsp')
    driver.execute_script('window.open()')
    driver.switch_to.window(driver.window_handles[NEW])
    driver.get(MAIN_URL + '/files/special/list_arrival.html')

# ログイン
login(USER_MAIL, USER_PASS)
init()
# 注文完了画面を表示させるためにカートと店舗を設定
print('カートの設定処理開始')
cart_setting()
buy(True, False)
cart_refresh()
driver.switch_to.window(driver.window_handles[BUY])
driver.refresh()
print('カートの設定処理完了')
start_time = time.time()
while True:
    # お気に入りに登録している商品で中古の在庫があればカートに保存
    star_list(start_time)
    # 購入処理
    buy(False, True)
    if (time.time() - start_time) > PROCESS_TIME:
        sys.exit(0)
