#取得幣安某個時間段每分鐘永續合約交易記錄K線

from binance.binanceAPI import binanceAPI
from db.db import db
from datetime import datetime
from datetime import timedelta
import time

db = db('binance')
binance = binanceAPI()

def geneKlines(pair, startTime, endTime):
    pair = pair
    startTime = startTime
    endTime = endTime
    interval = '5m'
    limit = 500
    obj = binance.getKlines(pair, startTime, endTime, interval, limit)
    return obj

def getAllDay(pair, date):
    aryObj = geneKlines(pair, binance.dateStr2ts(date + ' 00:00:00'), binance.dateStr2ts(date + ' 23:59:59') )
    lstData = []
    for item in aryObj:
        data = dict()
        data['time'] = binance.ts2dateStr(item[0])
        data['pair'] =  pair
        data['interval'] = '5m'
        data['start_price'] = item[1]
        data['high_price'] = item[2]
        data['low_price'] = item[3]
        data['end_price'] = item[4]
        data['volume'] = item[5]
        data['money'] = item[7]
        lstData.append(data)
    return lstData

def genDateList(startDateStr, delta):
    lstDate = []
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d')
    for i in range(0 , delta):
        dateNew = startDate + timedelta(days = i)
        lstDate.append(dateNew.strftime('%Y-%m-%d') )
    return lstDate

def start():
    lstDate = genDateList('2025-01-01', 31)
    onboardDateAfter = binance.dateStr2ts('2024-10-01 00:00:00')  #幣安合約上線日期
    lstPair = binance.getExchangeInfo(onboardDateAfter)

    print(lstPair)

    
    # for dateStr in lstDate:
    #     for pair in lstPair:
    #         data = getAllDay(pair, dateStr)
    #         print(data)
    #         db.insertBinanceKlines(data)
    #         time.sleep(0.3)
    
start()