import requests
from utils.urlparamsbuilder import UrlParamsBuilder
import json
import base64
import hashlib
import hmac

class okexAPIv5(object):
    
    def __init__(self):
        self.host = 'https://www.okex.com'
        #self.host = 'https://aws.okex.com'
        self.apikey = '' #OKEX api-key
        self.secretkey = '' #OKEX secret-key
        self.passphrase = '' #OKEX 自定義 passphrase


    def signature(self, timestamp, method, request_path, body):
        if str(body) == '{}' or str(body) == 'None':
            body = ''
        message = str(timestamp) + str.upper(method) + request_path + str(body)
        mac = hmac.new(bytes(self.secretkey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)


    def getHeader(self, method, request_path, body):

        ts = self.getTimeStamp()

        header = dict()
        header.update({'OK-ACCESS-KEY': self.apikey})
        header.update({'OK-ACCESS-SIGN': self.signature(ts, method, request_path, body)})
        header.update({'OK-ACCESS-TIMESTAMP': ts})
        header.update({'OK-ACCESS-PASSPHRASE': self.passphrase})
        return header

    def getTimeStamp(self):
        urlAll = self.host + '/api/general/v3/time'
        resp = requests.get(urlAll)
        if(resp.status_code == 200):
            obj = json.loads(resp.text)
            resp.close()
            return obj['iso']
        else:
            print(resp.status_code)
            print(resp.text)
        return None


    def sendCmd(self, method, request_path, params, isSign):
        urlAll = self.host + request_path
        builder = UrlParamsBuilder()
        header = None
        if(params is not None):
            for key in params:
                builder.put_url(key, params[key])

        if(isSign == True):
            if(params is None):
                header = self.getHeader(method, request_path , None)
            else:
                header = self.getHeader(method, request_path + '?' + builder.build_url() , None)

        if(method == 'GET'):
            resp = requests.get(urlAll, params = builder.build_url(), headers = header)
        else:
            resp = requests.post(urlAll, params = builder.build_url(), headers = header)

        if(resp.status_code == 200):
            obj = json.loads(resp.text)
            resp.close()
            return obj
        else:
            print(resp.status_code)
            print(resp.text)
        return None
    
    #取得最近資金費率流水, 請求此bill id 之後的值，從db中取出上次最新的值
    def getBills(self, beforeBillId):
        fullUrl = '/api/v5/account/bills'
        params = dict()
        params['instType'] = 'SWAP'
        params['type'] = '8' #資金費
        params['before'] = beforeBillId
        obj = self.sendCmd(method='GET', request_path = fullUrl, params = params, isSign = True)
        return obj

    #取得目前永續合約倉位
    def getPosition(self):
        params = dict()
        params['instType'] = 'SWAP'
        obj = self.sendCmd(method='GET', request_path = '/api/v5/account/positions', params = params, isSign = True)
        return obj

    def getBalance(self):
        params = dict()
        params['ccy'] = 'USDT'
        obj = self.sendCmd(method='GET', request_path = '/api/v5/account/balance', params = params, isSign = True)
        return obj
