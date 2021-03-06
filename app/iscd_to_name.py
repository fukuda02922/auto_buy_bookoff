###
# 商品コードから商品情報リストのCSVに変換
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

filename = os.path.dirname(__file__) + '/bookmark/iscd_list.csv'

filename_after = os.path.dirname(__file__) + '/bookmark/infos.csv'
if os.path.exists(filename_after):
    os.remove(filename_after)
pathlib.Path(filename_after)

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
        iscd = iscd_list[index][0]
        duplicate_count = iscd_list[index][1]
        try:
            print(index)
            response = requests.get(MAIN_URL + '/bolapi/api/goods/{}'.format(iscd))
            info = response.content.decode('utf_8_sig').lstrip('callback([').rstrip('])')
            info_json = json.loads(info)
            name_list.append(
                [
                    int(duplicate_count),
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

with open(filename, 'r') as f:
    r = csv.reader(f)
    for line in r:
        iscd_list.append(line)
th_pool = [Thread(target=run) for index in range(TH_COUNT)]
for th in th_pool:
    th.start()
for th in th_pool:
    th.join()

sorted_count_list = sorted(name_list, key=lambda x: (x[1], x[0]), reverse=True)

with open(filename_after, 'a', encoding='utf_8_sig') as f:
    w = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
    w.writerow(['人気度', 'カテゴリー', '商品名', '付加情報1', '付加情報2', 'JAN', '価格', 'URL', 'iscd(商品cd)'])
    w.writerows(sorted_count_list)