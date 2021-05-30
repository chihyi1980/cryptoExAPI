#OKEX API測試

from okex.okexAPI import okexAPI
import time
from okex.okexAPIv5 import okexAPIv5
from datetime import datetime, timedelta

okex = okexAPI()
okexV5 = okexAPIv5()

#取得目前市場最新穩定費率，由高到低排序
def getNewRates():
    temp = okex.getSwapInstruments()
    lstRate = dict()

    for item in temp:
        id = item['instrument_id']
        obj = okex.getFundingRateNow(id)
        lstRate[item['contract_val_currency']] = obj['funding_rate']
        time.sleep(.1)
    
    i = 0
    for w in sorted(lstRate, key=lstRate.get, reverse=True):
        if(i < 100):
            print(w, lstRate[w])
        i= i + 1

#取得目前最新的預測資金費率x10000，如果是目前持有倉位加上*號
def getEstimatedRate():
    temp = okex.getSwapInstruments()
    aryPos = getAllPositionId()
    lstRate = dict()

    for item in temp:
        id = item['instrument_id']
        obj = okex.getFundingRateNow(id)
        lstRate[id] = float(obj['estimated_rate']) * 10000
        time.sleep(.1)
 
    for id in sorted(lstRate, key=lstRate.get, reverse=True):
        if(id in aryPos ):
            print('*' + id , lstRate[id])
        else:
            print(id , lstRate[id])
 

#取得最近幾次的資金費率總和
def getLastestRateSum(instrument_id, limit):
    temp = okex.getFundingRateHistory(instrument_id, limit)
    sum = 0.0
    for item in temp:
        sum = sum + float(item['realized_rate'])
    return sum

#取得最近size次數平均值並且排序
def getLastestAvgRate(size):
    lstRate = dict()
    temp = okex.getSwapInstruments()
    for item in temp:
        time.sleep(.1)
        avg = getLastestRateSum(item['instrument_id'], size) / size
        lstRate[item['contract_val_currency']] = avg * 10000

    i = 0
    for w in sorted(lstRate, key=lstRate.get, reverse=True):
        if(i < 10):
            print(w, lstRate[w])
        i = i + 1

#取得所有交易對，近size次資金費率，依總和排序後，顯示出來
def getLastestRate(size):
    lstRateSum = dict()
    lstRateRow = dict()
    
    #取出有哪些交易對
    temp = okex.getSwapInstruments()

    for item in temp:
        time.sleep(.1)
        rates = okex.getFundingRateHistory(item['instrument_id'], size)

        sum = 0.0
        strRow = item['instrument_id'] 
        for rateItem in rates:
            
            #取得資金費率顯示字串
            strRow = strRow + ' , ' + str(round(float(rateItem['realized_rate']) * 10000 , 2))

            #取得資金費率總和
            sum = sum + float(rateItem['realized_rate'])

        lstRateSum[item['instrument_id']] = sum
        lstRateRow[item['instrument_id']] = strRow


    for w in sorted(lstRateSum, key=lstRateSum.get, reverse=True):
        print(lstRateRow[w])


#取得永續合約所持所有倉位
def getAllPositionId():
    lstPos = []
    temp = okexV5.getPosition()

    for item in temp['data']:
        lstPos.append(item['instId'])

    return lstPos

#當前持倉instrument_id最近n次的合約實際流水總和
def getSumFunding(instrument_id, limit):
    sum = 0.0
    temp = okex.getLedger( instrument_id, limit)
    for item in temp:
        sum = sum + float(item['amount'])
    return sum

def start():
    lstSum = dict()
    aryPos = getAllPositionId()
    for item in aryPos:
        obj = getSumFunding(item, 2
        )
        lstSum[item] = obj
        time.sleep(2)

    sum = 0.0
    for w in sorted(lstSum, key=lstSum.get, reverse=True):
        sum = sum + float(lstSum[w])
        print(w, lstSum[w])

    print('Total:' , sum)

    return lstSum

def getAssetValuation():
    print(okex.getAssetValuation(0, 'USD'))


def getBills():
    data = okexV5.getBills(296674901012922368)
    lstBills = []
    for item in data['data']:
        temp = dict()
        temp['billId'] = item['billId']
        temp['pair'] = item['instId']
        temp['amount'] = item['pnl']
        tsNum = int(int(item['ts']) / 480000) * 480 #將timestamp整理成08:00/16:00/00:00
        temp['time'] = str(datetime.fromtimestamp(tsNum))
        lstBills.append(temp)
    return lstBills

#取得通用帳戶中USDT可用餘額
def getAvailEq():
    obj = okexV5.getBalance()
    detail = obj['data'][0]['details']
    return detail[0]['availEq']

print(getLastestRate(5))