#取得OKEX目前可調動USDT並寫入DB，如果此值太低可能會被強制平倉

from okex.okexAPIv5 import okexAPIv5
from db.db import db
import time
from datetime import datetime

db = db('okex')
okexV5 = okexAPIv5()

def start():
    datetime_dt = datetime.today() # 獲得當地時間
    datetime_str = datetime_dt.strftime('%Y-%m-%d')  # 格式化日期

    obj = okexV5.getBalance()
    detail = obj['data'][0]['details']
    availEq = detail[0]['availEq']
    db.insertOkexAssetValue(datetime_str, availEq)

    db.closeDBConn()

start()