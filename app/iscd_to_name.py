from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, time, pathlib
from threading import Thread, Lock

TH_COUNT = 10 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
lock = Lock()
now = datetime.now()
count = -1
iscd_list = []

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
        index = next_count()
        if (index + 1) > len(iscd_list):
            return
        iscd = iscd_list[index]
        try:
            response = requests.get(MAIN_URL + '/bolapi/api/goods/{}'.format(iscd))
            info = response.content.lstrip('callback([').rstrip('])')
            info_json = json.loads(info)
            lock.acquire()
            try:
                with open(filename_after, 'a') as f:
                    w = csv.writer(f)
                    w.writerow([info_json['GOODS_NAME1'], info_json['GOODS_NAME3'], info_json['JAN'], info_json['SALE_PR_USED']])
            except Exception:
                pass
            lock.release()
        except Exception:
            pass

with open(filename, 'r') as f:
    r = csv.reader(f)
    for line in r:
        iscd_list.append(line)
th_pool = [Thread(target=run for index in range(TH_COUNT)]
for th in th_pool:
    th.start()
for th in th_pool:
    th.join()