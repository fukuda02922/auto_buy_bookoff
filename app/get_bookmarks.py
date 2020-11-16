from auto_buy_log import Log
from datetime import datetime
import sys, os, traceback, requests, json, csv, pathlib
from threading import Thread, Lock

TH_COUNT = 100 # スレッド数
MAIN_URL = 'https://www.bookoffonline.co.jp'
LIMIT = 3000000  # 取得回数
START_MEMNO = 8000000 # 開始位置
count = 0
lock = Lock()
now = datetime.now()

filename = os.path.dirname(__file__) + '/bookmark/sedori_list.csv'

filename_over50 = os.path.dirname(__file__) + '/bookmark/over50_list.csv'

def next_memNo():
    global count
    count += 1
    return START_MEMNO + count

def run():
    while True:
        lock.acquire()
        memNo = next_memNo()
        lock.release()
        print(memNo)
        if LIMIT < count:
            return
        try:
            response = requests.get(MAIN_URL + '/spf-api2/goods_souko/bookmark/{}'.format(memNo))
            star_list_json = json.loads(response.content)
            if star_list_json['rcptList']:
                # for star in star_list_json['rcptList']:
                #     if star['used_warehouse'] == 0:
                #         lock.acquire()
                #         with open(filename, 'a') as f:
                #             w = csv.writer(f)
                #             w.writerow([star['instorecode'], 1])
                #         lock.release()
                if len(star_list_json['rcptList']) >= 50:
                    with open(filename_over50, 'a') as f:
                        w = csv.writer(f)
                        w.writerow([memNo])
                    if all([star['rcpt_flg'] == 'false' for star in star_list_json['rcptList']]):
                        with open(filename, 'a') as f:
                            w = csv.writer(f)
                            w.writerow([memNo])

        except Exception:
            pass


th_pool = [Thread(target=run) for index in range(TH_COUNT)]
for th in th_pool:
    th.start()
for th in th_pool:
    th.join()