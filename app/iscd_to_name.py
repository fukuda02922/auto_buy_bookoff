from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, time, pathlib
from threading import Thread, Lock

TH_COUNT = 100 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
lock = Lock()
now = datetime.now()
count = 0

filename = os.path.dirname(__file__) + '/bookmark/test.csv'

filename_after = os.path.dirname(__file__) + '/bookmark/iscd_name.csv'
if os.path.exists(filename_after):
    os.remove(filename_after)
pathlib.Path(filename_after)

def next_count():
    global count
    count += 1
    return count

def run(r):
    while True:
        try:
            response = requests.get(MAIN_URL + '/bolapi/api/goods/{}'.format(memNo))
            info = json.loads(response.content)
            lock.acquire()
            try:
                with open(filename_after, 'a') as f:
                    w = csv.writer(f)
                    w.writerow([info['instorecode'], 1])
            except Exception:
                pass
            lock.release()

        except Exception:
            pass

with open(filename) as f:
    r = csv.reader(f)
    th_pool = [Thread(target=run, args=(r,)) for index in range(TH_COUNT)]
    for th in th_pool:
        th.start()
    for th in th_pool:
        th.join()