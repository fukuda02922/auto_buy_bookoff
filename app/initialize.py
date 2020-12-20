from auto_buy_log import Log
import time
from datetime import datetime
import sys
import traceback
import requests
import json
import re
from requests import Session
from threading import Thread, Lock, Event

now = datetime.now()
log = Log('bookoff.log', now)
log.create_log()

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 60 * 1  # 処理時間
STAR_LIST_INTERNAL_TIME = 0.2  # お気に入りの検索時間の間隔
TH_COUNT = 4 # スレッド数
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
new_count = 0
buy_count = 0
start_time = time.time()
cartNo = ''
lock = Lock()
next_process_star = 0
wait_time = time.time()
cart_refreshing = False
buy_processing = False
star_event = Event()

def login(id, password):
    star_session.post(MAIN_URL + '/common/CSfLogin.jsp',
        params={
            'ID' : id,
            'PWD': password,
            'x' : '110',
            'y' : '25'
        })
    for cookie in star_session.cookies.items():
        buy_session.cookies.set(cookie[0], cookie[1])

def cart_refresh():
    cart_refreshing = True
    while True:
        try:
            response = buy_session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
                'CART1_001': cartNo,
                'CART1_002': new_count,
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
    response = buy_session.post('https://www.bookoffonline.co.jp/disp/CCtUpdateCart_001.jsp', data={
        'CART1_001': cartNo,
        'CART1_002': new_count,
        'CART1_005': '1',
        'LENGTH': '1',
        'OPCODE': 'edit_and_go'
    })
    if response.ok and response.url == 'https://www.bookoffonline.co.jp/order/COdPaymentInfo.jsp':
        log.logger.info('カート更新完了[cartNo:{},cartSeq:{}]'.format(cartNo, new_count))
        return True
    else:
        log.logger.info('カート更新失敗[cartNo:{},cartSeq:{}]'.format(cartNo, new_count))
        return False

def shop_select():
    buy_session.post('https://www.bookoffonline.co.jp/disp/COdRcptStore.jsp', data={
        'submitStoreCd': '20425'
    })

def finish_buy():
    response = buy_session.post('https://www.bookoffonline.co.jp/order/COdOrderConfirmRcptStore.jsp', data={
        'BTN_CHECK': 'TempToReal',
        'deleteBookmarkAndAlertMail': '0'
    })
    return response.ok and response.url == 'https://www.bookoffonline.co.jp/order/COdOrderCompleteRcptStore.jsp'

def add_cart(iscd):
    global new_count
    new_count += 1
    log.logger.info('カート追加')
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
        if (not cart_refreshing):
            # 中古在庫を20件表示で検索
            if ((next_process_star == index) and (time.time() - wait_time) > STAR_LIST_INTERNAL_TIME):
                wait_time = time.time()
                next_process_count(index)
                try:
                    response = star_session.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/' + memNo)  # エラー
                except Exception as e:
                    log.logger.exception(f'{e}')
                    continue
                star_list_json = json.loads(response.content)
                isCdList = []
                for rcpt in star_list_json['rcptList']:
                    if rcpt['rcpt_flg'] == 'true':
                        isCdList.append(rcpt['instorecode'])
                lock.acquire()
                log.logger.info('検索結果{}'.format(index))
                if isCdList and (not buy_processing):
                    buy_processing = True
                    lock.release()
                    for iscd in isCdList:
                        add_cart(iscd)
                        buy()
                    buy_processing = False
                    star_event.set()
                if lock.locked():
                    lock.release()
            elif (time.time() - wait_time) > (STAR_LIST_INTERNAL_TIME + 0.5):
                wait_time = time.time()
                next_process_count(index)
        if (time.time() - start_time) > PROCESS_TIME:
            return

def buy():
    global buy_processing
    log.logger.info('購入開始')
    if cart_update() and finish_buy():
        log.logger.info('購入完了')
        global buy_count
        buy_count += 1
    else:
        log.logger.info('購入失敗')
        cart_refresh()
    buy_processing = False

def buy_init():
    response = star_session.get(MAIN_URL + '/disp/CCtViewCart_001.jsp')
    match = re.search(r'cartNo = \"([0-9]{20})\"', response.text)
    group = match.groups()
    global cartNo
    cartNo = group[0]

try:
    # ログイン
    log.logger.info('ログイン処理[{}]'.format(memNo))
    login(USER_MAIL, USER_PASS)
    # 注文完了画面を表示させるためにカートと店舗を設定
    log.logger.info('カートの設定処理開始')
    buy_init()
    shop_select()
    log.logger.info('カートの設定処理完了')

    # お気に入り検索スレッドの定義
    th_pool_star = [Thread(target=run_thread, args=(start_time, index)) for index in range(TH_COUNT)]

    # スレッド開始
    for th in th_pool_star:
        th.start()
        time.sleep(1)

    #スレッドの完了待ち
    for th in th_pool_star:
        th.join()

    log.logger.info('new: {}, buy: {}'.format(new_count, buy_count))
except Exception as e:
    log.logger.exception(f'{e}')