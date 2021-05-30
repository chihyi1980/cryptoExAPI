#幣安API測試

from binance.binanceAPI import binanceAPI

def start():
    binance = binanceAPI()
    startTime = '2021-05-26 16:00:00'
    endTime = '2021-05-28 00:00:00'
    temp = binance.getFundingRateHistory(startTime, endTime, 1000, None)

    lstRate = dict()
    lstRateStr = dict()
    for item in temp:
        if(lstRate.get(item['symbol']) is None):
            lstRate[item['symbol']] = 0.0
            lstRateStr[item['symbol']] = ''

        lstRate[item['symbol']] = lstRate[item['symbol']] + float(item['fundingRate'])
        lstRateStr[item['symbol']] = lstRateStr[item['symbol']] + ' , ' + str(round(float(item['fundingRate']) * 10000,2))
    
    for w in sorted(lstRate, key=lstRate.get, reverse=True):
            print(w, lstRateStr[w])

start()