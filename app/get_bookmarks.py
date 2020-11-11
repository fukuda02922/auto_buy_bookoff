from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, time, pathlib, random
from threading import Thread, Lock

TH_COUNT = 100 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
LIMIT = 100000
PROCESS_TIME = 60 * 60 * 1
count = 0
start_time = time.time()
memNo_50over = []
lock = Lock()
now = datetime.now()
random_list = list(range(8000000, 11000000))

filename = os.path.dirname(__file__) + '/bookmark/{}_{}_{}.csv'.format(now.year, now.month, now.day)
filename_over50 = os.path.dirname(__file__) + '/bookmark/{}_{}_{}.csv'.format(now.year, now.month, now.day)
if os.path.exists(filename):
    os.remove(filename)
pathlib.Path(filename)

def next_memNo():
    global count
    count += 1
    return random.choice(random_list)

def run():
    global memNo_50over
    while True:
        print(count)
        if LIMIT < count:
            return
        if (time.time() - start_time) > PROCESS_TIME:
            return
        try:
            print(memNo)
            response = requests.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/{}'.format(memNo))
            star_list_json = json.loads(response.content)
            if star_list_json['rcptList']:
                for star in star_list_json['rcptList']:
                    if star['used_warehouse'] == 0:
                        lock.acquire()
                        with open(filename, 'a') as f:
                            w = csv.writer(f)
                            w.writerow([star['instorecode'], 1])
                        lock.release()
                if star_list_json['rcptList'].length >= 50:
                    memNo_50over.append(memNo)
        except Exception:
            pass

try:
    th_pool = [Thread(target=run) for index in range(TH_COUNT)]
    for th in th_pool:
        th.start()
    for th in th_pool:
        th.join()
except KeyboardInterrupt:
    print(memNo_50over)