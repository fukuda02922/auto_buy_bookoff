from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, time, pathlib
from threading import Thread, Lock

TH_COUNT = 100 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
COUNT_NUM = 10 # 指定しているカウント以上の重複登録（お気に入り）を抜き出す
lock = Lock()
writer_lock = Lock()
now = datetime.now()
count = -1
memNo_list = []

filename = os.path.dirname(__file__) + '/bookmark/sedori_list.csv'

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
        lock.acquire()
        index = next_count()
        lock.release()
        if (index + 1) > len(memNo_list):
            return
        memNo = memNo_list[index]
        try:
            response = requests.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/{}'.format(memNo))
            star_list_json = json.loads(response.content)
            if star_list_json['rcptList']:
                writer_lock.acquire()
                try:
                    with open(filename_after, 'a') as f:
                        w = csv.writer(f)
                        for star in star_list_json['rcptList']:
                            w.writerow([star['instorecode'], 1])
                except Exception:
                    pass
                writer_lock.release()
        except Exception:
            pass

with open(filename, 'r') as f:
    r = csv.reader(f)
    for line in r:
        memNo_list.append(line[0])
th_pool = [Thread(target=run) for index in range(TH_COUNT)]
for th in th_pool:
    th.start()
for th in th_pool:
    th.join()

iscd_list = {}
with open(filename_after, 'r') as f:
    r = csv.reader(f)
    iscd_list = {}
    for line in r:
        if line[0] in iscd_list.keys():
            iscd_list[line[0]] += 1
        else:
            iscd_list[line[0]] = 1
sorted_iscd_list = sorted(iscd_list.items(), key=lambda x: x[1], reverse=True)
with open(filename_after, 'w') as f2:
    w = csv.writer(f2)
    w.writerows([[item[0], item[1]] for item in sorted_iscd_list])