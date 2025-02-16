#火幣API測試

from huobi.huobiAPI import huobiAPI
import time

huobi = huobiAPI()

def start():
    temp = huobi.getSwapBatchFundingRate()

    lstRate = dict()
    for item in temp['data']:
        lstRate[item['contract_code']] = item['funding_rate']
    
    i = 0
    for w in sorted(lstRate, key=lstRate.get, reverse=True):
        if(i < 10):
            print(w, lstRate[w])
        i = i + 1


#取得最近幾次的資金費率總和
def getLastestRateSum(contract_code, size):
    temp = huobi.getHistoricalFundingRate(contract_code, size)
    sum = 0.0
    for item in temp['data']['data']:
        sum = sum + float(item['realized_rate'])
    return sum


def getLastestRateSort(size):
    lstRate = dict()
    lstRateStr = dict()
    temp = huobi.getSwapContractInfo()
    for item in temp['data']:
        time.sleep(.1)
        sum = getLastestRateSum(item['contract_code'], size) 
        time.sleep(.1)
        row = getLastestRates(item['contract_code'],10)
        lstRate[item['contract_code']] = sum
        lstRateStr[item['contract_code']] = row

    for w in sorted(lstRate, key = lstRate.get, reverse = True):
        print(w, lstRateStr[w])


#取得最近幾次的資金費率總和，並且組成字串
def getLastestRates(contract_code, size):
    temp = huobi.getHistoricalFundingRate(contract_code, size)
    ans = ''
    for item in temp['data']['data']:
        ans = ans + ' , ' +  str( round(float(item['realized_rate']) * 10000 , 2) )
    return ans


#temp = huobi.getSwapContractInfo()
getLastestRateSort(6)
