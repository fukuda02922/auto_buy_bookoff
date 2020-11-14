from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, time, pathlib
from threading import Thread, Lock

TH_COUNT = 10 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
lock = Lock()
now = datetime.now()
count = -1
memNo_list = []

filename = os.path.dirname(__file__) + '/bookmark/test.csv'

filename_after = os.path.dirname(__file__) + '/bookmark/iscd_list.csv'
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
        if (index + 1) > len(memNo_list):
            return
        memNo = memNo_list[index]
        try:
            response = requests.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/{}'.format(memNo))
            star_list_json = json.loads(response.content)
            if star_list_json['rcptList']:
                lock.acquire()
                try:
                    with open(filename_after, 'a') as f:
                        w = csv.writer(f)
                        for star in star_list_json['rcptList']:
                            w.writerow([star['instorecode'], 1])
                except Exception:
                    pass
                lock.release()
        except Exception:
            pass

with open(filename, 'r') as f:
    r = csv.reader(f)
    for line in r:
        memNo_list.append(line)
th_pool = [Thread(target=run for index in range(TH_COUNT)]
for th in th_pool:
    th.start()
for th in th_pool:
    th.join()