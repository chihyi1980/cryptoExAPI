#取得OKEX上最近一個 08:00/16:00/00:00 資金費流水寫入DB

from okex.okexAPIv5 import okexAPIv5
from db.db import db
import time
from datetime import datetime, timedelta

db = db('okex')
okexV5 = okexAPIv5()

def start():
    lastestBillId = db.queryLastestBillId()
    data = okexV5.getBills(lastestBillId)
    lstBills = []
    for item in data['data']:
        temp = dict()
        temp['billId'] = int(item['billId'])
        temp['pair'] = item['instId']
        temp['amount'] = item['pnl']
        tsNum = int(int(item['ts']) / 480000) * 480 #將timestamp整理成08:00/16:00/00:00
        temp['time'] = str(datetime.fromtimestamp(tsNum))
        lstBills.append(temp)
    db.insertOkexFundingHistory(lstBills)
    db.closeDBConn()

start()
