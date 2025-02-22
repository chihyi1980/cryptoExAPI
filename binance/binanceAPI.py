import requests
from utils.urlparamsbuilder import UrlParamsBuilder
import json
from datetime import datetime
from config import Config

class binanceAPI(object):
    
    def __init__(self):
        self.host = Config.BINANCE_API_HOST
        self.api_key = Config.BINANCE_API_KEY #幣安api_key
        self.secret_key = Config.BINANCE_SECRET_KEY #幣安secret_key

    #timestemp 轉 '%Y-%m-%d %H:%M:%S'
    def ts2dateStr(self, ts):
        ts = ts / 1000
        return str(datetime.fromtimestamp(ts))

    #'%Y-%m-%d %H:%M:%S' 轉 timestemp 
    def dateStr2ts(self, dateStr):
        dt_obj = datetime.strptime(dateStr, '%Y-%m-%d %H:%M:%S')
        millisec = dt_obj.timestamp() * 1000
        return int(millisec)

    def getHeader(self):
        header = dict()
        header.update({"Content-Type": "application/x-www-form-urlencoded"})
        header.update({"X-MBX-APIKEY": self.api_key})
        return header


    #發送下單指令
    def sendCmd(self, type, url, params, isSign):
        urlAll = self.host + url
        builder = UrlParamsBuilder()
        if(params is not None):
            for key in params:
                builder.put_post(key, params[key])
                builder.put_url(key, params[key])
        if(type == 'GET'):
            resp = requests.get(urlAll, params = builder.build_url())
        else:
            resp = requests.post(url, params = builder.build_url(), headers = self.getHeader())

        if(resp.status_code == 200):
            obj = json.loads(resp.text)
            resp.close()
            return obj
        else:
            print(resp.status_code)
            print(resp.text)
        return None

    #獲取歷史資金費率
    def getFundingRateHistory(self, startTime, endTime, limit, symbol):
        params = dict()
        params['startTime'] = self.dateStr2ts(startTime)
        params['endTime'] = self.dateStr2ts(endTime)
        params['limit'] = limit
        if(symbol is not None):
            params['symbol'] = symbol

        obj = self.sendCmd(type='GET', url = '/fapi/v1/fundingRate', params = params, isSign = False)
        return obj

    #獲取K線歷史數據
    def getKlines(self, pair, startTime, endTime, interval, limit):
        url = self.host + '/fapi/v1/klines'

        builder = UrlParamsBuilder()
        builder.put_url("symbol", pair)
        builder.put_url("startTime", startTime)
        builder.put_url("endTime", endTime)
        builder.put_url("interval", interval)
        builder.put_url("limit", limit)

        resp = requests.get(url, params = builder.build_url())
        if(resp.status_code == 200):
            obj = json.loads(resp.text)
            resp.close()
            return obj
        else:
            print(resp.status_code)
            print(resp.text)
        return None

    #获取交易对  永續合約 交易中 USDT 上架日期大於等於 onboardDateAfter
    #依照上架日期排序，越新的越先
    def getExchangeInfo(self, onboardDateAfter):
        url = self.host + '/fapi/v1/exchangeInfo'
        resp = requests.get(url)
        if resp.status_code == 200:
            obj = json.loads(resp.text)
            pairs = [
                p['symbol'] for p in obj['symbols']
                if p['contractType'] == 'PERPETUAL'
                and p['status'] == 'TRADING'
                and p['quoteAsset'] == 'USDT'
                and p['onboardDate'] >= onboardDateAfter
            ]
            sorted_pairs = sorted(pairs, key=lambda x: next(p['onboardDate'] for p in obj['symbols'] if p['symbol'] == x), reverse=True)
            resp.close()
            return sorted_pairs
        else:
            print(resp.status_code)
            print(resp.text)
        return None