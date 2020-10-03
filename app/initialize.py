from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions


import chromedriver_binary
import time
import sys

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 20
# chromeのアドレスバーに「chrome://version/」を入力して、そのプロフィールパス
# USER_DATA_DIR = 'UserData'
# USER_DATA_DIR = '/Users/y.fukuda/Library/Application Support/Google/Chrome/Default/Default'

options = webdriver.chrome.options.Options()
# options.add_argument('--user-data-dir={}'.format(USER_DATA_DIR))
# options.add_argument('--headless')
# options.add_argument('--user-agent=hogehoge')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--single-process')
options.add_argument('--disable-application-cache')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized')
driver = webdriver.Chrome('C:\Workspace\driver\chromedriver_win32\chromedriver.exe', options=options)

def login(id, password):
    driver.get('https://www.bookoffonline.co.jp/common/CSfLogin.jsp')
    elmId = driver.find_element_by_name('ID')
    elmId.send_keys(id)
    elmPass = driver.find_element_by_name('PWD')
    elmPass.send_keys(password)
    loginBtn = driver.find_element_by_xpath('//input[@alt=\"ログイン\"]')
    loginBtn.click()

def star_list(start_time):
    while True:
        print('検索開始')
        # 中古在庫を50件表示で検索
        driver.switch_to.window(driver.window_handles[0])
        driver.get('https://www.bookoffonline.co.jp/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50')

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
                            time.sleep(0.1)
                    driver.switch_to.window(driver.window_handles[0])
                    if message == '選択した商品をカートに入れました\n画面右上の「カートをみる」でカートの中身が確認できます':
                        print('カートに追加')
                        return
        if (time.time() - start_time) > PROCESS_TIME:
            sys.exit(0)
        print('秒後に再表示')
        time.sleep(2)

def buy():
    print('購入開始')
    # 別ウィンドウでカートを開く
    driver.execute_script('window.open()')
    driver.switch_to.window(driver.window_handles[-1])
    driver.get('https://www.bookoffonline.co.jp/disp/CCtViewCart_001.jsp')
    errors = driver.find_elements_by_xpath('//div[@class=\"error\"]/../../../td[@class=\"check\"]/input[@type=\"checkbox\"]')
    if errors:
        for error in errors:
            error.click()
        driver.find_element_by_name('deleteSelectedButton').click()
    try_count = 0

    # ブックオフ店舗で受け取りボタンを押下
    while True:
        try:
            driver.find_element_by_xpath('//input[@alt=\"ブックオフ店舗で受け取る\"]').click()
            break
        except Exception:
            if try_count > 5:
                print('購入失敗')
                return
            try_count += 1
            time.sleep(0.5)
    # 店舗選択を確定
    try_count = 0
    while True:
        try:
            if driver.find_elements_by_xpath('//span[contains(text(), "{0}")]'.format('店舗受取できない商品を')):
                driver.find_elements_by_xpath('//span[contains(text(), "{0}")]'.format('店舗受取できない商品を'))[0].parent().click()
                return
            driver.find_element_by_xpath('//div[@class="shop-receive-btn js_receive_btn_select"]/span[contains(text(), "{0}")]'.format("選択した店舗で支払・受取をする")).click()
            break
        except Exception:
            if try_count > 5:
                print('購入失敗')
                return
            try_count += 1
            time.sleep(0.5)
    # 注文確定ボタンを押下
    try_count = 0
    while True:
        try:
            driver.find_element_by_id('tempToReal').click()
            break
        except Exception:
            if try_count > 5:
                print('購入失敗')
                try:
                    Alert(driver).accept()
                except:
                    print('アラートなし')
                return
            try_count += 1
            time.sleep(0.5)
    if (driver.find_elements_by_xpath('//div[contains(text(), "{0}")]'.format('ご注文ありがとうございました'))):
        print('購入完了')
    else:
        print('購入失敗')
    driver.close()

# ログイン
login(USER_MAIL, USER_PASS)
start_time = time.time()
while True:
    # お気に入りに登録している商品で中古の在庫があればカートに保存
    star_list(start_time)
    # 購入処理
    buy()
    if (time.time() - start_time) > PROCESS_TIME:
        sys.exit(0)
