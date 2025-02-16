#取得OKEX上資產現值並寫入DB

from okex.okexAPI import okexAPI
from db.db import db
import time
from datetime import datetime

db = db('okex')
okex = okexAPI()

def start():
    datetime_dt = datetime.today() # 獲得當地時間
    datetime_str = datetime_dt.strftime('%Y-%m-%d')  # 格式化日期

    data = okex.getAssetValuation(0, 'USD')
    db.insertOkexAssetValue(datetime_str, data['balance'])

    db.closeDBConn()

start()