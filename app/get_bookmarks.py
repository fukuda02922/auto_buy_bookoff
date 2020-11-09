from auto_buy_log import Log

import time
from datetime import datetime
import sys
import traceback
import requests
import json
import csv
from threading import Thread, Lock

TH_COUNT = 10 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
LIMIT = 100
PROCESS_TIME = 60 * 60 * 1
session = requests.Session()
count = 0
start_time = time.time()
iscd_list = {}
lock = Lock()


def next_memNo():
    global count
    count += 1
    return 8000000 + count

def run():
    global iscd_list
    while True:
        memNo = next_memNo()
        if LIMIT < count or start_time <:
            return
        if (time.time() - start_time) > PROCESS_TIME:
            return
        try:
            response = session.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/' + memNo)
        except Exception:
            pass
        star_list_json = json.loads(response.content)
        if star_list_json:
            lock.acquire()
            for star in star_list_json['rcptList']:
                if not (star['instorecode'] in iscd_list.keys()):
                    iscd_list[star['instorecode']] = 1
                else:
                    iscd_list[star['instorecode']] += 1
            lock.release()

th_pool = [Thread(target=run) for index in range(TH_COUNT)]

for th in th_pool:
    th.start()

for th in th_pool:
    th.join()

filename = os.path.dirname(__file__) + '/bookmark/{}_{}_{}.csv'.format(now.year, now.month, now.day)
if not os.path.exists(self.filename):
    pathlib.Path(self.filename)

with open(filename, 'w') as f:
    w = csv.DictWriter(f, iscd_list.keys())
    w.writerow(iscd_list)