###
# 指定したアカウントのブックマークをCSVに変換
# 使い方：
# 1. memNoに会員番号を設定
# 2. FILE_NAMEに出力先ファイル名を設定
###
from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, time, pathlib
from threading import Thread, Lock

TH_COUNT = 100 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
lock = Lock()
writer_lock = Lock()
now = datetime.now()
count = -1
iscd_list = []
name_list = []

FILE_NAME = 'bookmark_1.csv'
memNo = '8763947'

filename = os.path.dirname(__file__) + '/bookmark/' + FILE_NAME
if os.path.exists(filename):
    os.remove(filename)
pathlib.Path(filename)

def next_count():
    global count
    count += 1
    return count

def run():
    while True:
        lock.acquire()
        index = next_count()
        lock.release()
        if (index + 1) > len(iscd_list):
            return
        iscd = iscd_list[index]
        try:
            print(index)
            response = requests.get(MAIN_URL + '/bolapi/api/goods/{}'.format(iscd))
            info = response.content.decode('utf_8_sig').lstrip('callback([').rstrip('])')
            info_json = json.loads(info)
            name_list.append(
                [
                    'now_bookmark',
                    info_json['SECTION'] if 'SECTION' in info_json else '',
                    info_json['GOODS_NAME1'] if 'GOODS_NAME1' in info_json else '',
                    info_json['GOODS_NAME2'] if 'GOODS_NAME2' in info_json else '',
                    info_json['GOODS_NAME3'] if 'GOODS_NAME3' in info_json else '',
                    '="{}"'.format(info_json['JAN']) if 'JAN' in info_json else '',
                    info_json['SALE_PR_USED'] if 'SALE_PR_USED' in info_json else '',
                    MAIN_URL + '/old/{}'.format(info_json['INSTORECODE']),
                    '="{}"'.format(info_json['INSTORECODE'])
                ]
            )
        except Exception:
            pass

response = requests.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/{}'.format(memNo))
star_list_json = json.loads(response.content)
for star in star_list_json['rcptList']:
    iscd_list.append(star['instorecode'])


th_pool = [Thread(target=run) for index in range(TH_COUNT)]
for th in th_pool:
    th.start()
for th in th_pool:
    th.join()

with open(filename, 'a', encoding='utf_8_sig') as f:
    w = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
    w.writerow(['人気度', 'カテゴリー', '商品名', '付加情報1', '付加情報2', 'JAN', '価格', 'URL', 'iscd(商品cd)'])
    w.writerows(name_list)