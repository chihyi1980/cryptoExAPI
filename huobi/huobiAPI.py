import requests
from utils.urlparamsbuilder import UrlParamsBuilder
import json

class huobiAPI(object):
    
    def __init__(self):
        self.host = 'https://api.hbdm.com'

    def getHeader(self):
        header = dict()
        header.update({"Content-Type": "application/x-www-form-urlencoded"})
        return header


    def sendCmd(self, type, url, params, isSign):
        urlAll = self.host + url
        builder = UrlParamsBuilder()
        if(params is not None):
            for key in params:
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

    #獲取合約信息
    def getSwapContractInfo(self):
        obj = self.sendCmd(type='GET', url = '/linear-swap-api/v1/swap_contract_info', params = None, isSign = False)
        return obj

    #批量獲取當前資金費率
    def getSwapBatchFundingRate(self):
        obj = self.sendCmd(type='GET', url = '/linear-swap-api/v1/swap_batch_funding_rate', params = None, isSign = False)
        return obj

    #獲取歷史資金費率
    def getHistoricalFundingRate(self, contract_code, size):
        params = dict()
        params['contract_code'] = contract_code
        params['page_size'] = size
        obj = self.sendCmd(type='GET', url = '/linear-swap-api/v1/swap_historical_funding_rate', params = params, isSign = False)
        return obj