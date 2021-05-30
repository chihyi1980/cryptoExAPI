import requests
from utils.urlparamsbuilder import UrlParamsBuilder
import json
import base64
import hashlib
import hmac

class okexAPI(object):
    
    def __init__(self):
        self.host = 'https://www.okex.com'
        #self.host = 'https://aws.okex.com'
        self.apikey = '' #OKEX api-key
        self.secretkey = '' #OKEX secret-key
        self.passphrase = '' #OKEX 自定義 passphrase

    #簽名
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
            return obj['epoch']
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
    
    #獲取所有合約信息
    def getSwapInstruments(self):
        obj = self.sendCmd(method='GET', request_path = '/api/swap/v3/instruments', params = None, isSign = False)
        return obj

    #獲取即時資金費率
    def getFundingRateNow(self, instrumentId):
        fullUrl = '/api/swap/v3/instruments/' + instrumentId + '/funding_time'
        obj = self.sendCmd(method='GET', request_path = fullUrl, params = None, isSign = False)
        return obj

    #獲取歷史資金費率
    def getFundingRateHistory(self, instrument_id, limit):
        fullUrl = '/api/swap/v3/instruments/' + instrument_id + '/historical_funding_rate'
        params = dict()
        params['instrument_id'] = instrument_id
        params['limit'] = limit
        obj = self.sendCmd(method='GET', request_path = fullUrl, params = params, isSign = False)
        return obj
    
    #獲取帳單流水
    def getLedger(self, instrument_id, limit):
        fullUrl = '/api/swap/v3/accounts/' + instrument_id + '/ledger'
        params = dict()
        params['instrument_id'] = instrument_id
        params['limit'] = limit
        params['type'] = '14'
        """
        1. 开多
        2. 开空
        3. 平多
        4. 平空
        5.转入
        6.转出
        7.清算未实现
        8.分摊
        9.剩余拨付
        10.强平多
        11.强平空
        14.资金费
        15.手动追加
        16.手动减少
        17.自动追加
        18.修改持仓模式
        19.强减多
        20.强减空
        21.用户调低杠杆追加保证金
        22.清算已实现
        """
        obj = self.sendCmd(method='GET', request_path = fullUrl, params = params, isSign = True)
        return obj

    #取得目前永續合約倉位
    def getPosition(self):
        obj = self.sendCmd(method='GET', request_path = '/api/swap/v3/position', params = None, isSign = True)
        return obj

    #取得幣幣帳戶中資訊
    def getSpotAccountInfo(self):
        obj = self.sendCmd(method='GET', request_path = '/api/spot/v3/accounts', params = None, isSign = True)
        return obj

    #获取账户资产估值
    def getAssetValuation(self, account_type, valuation_currency):
        params = dict()
        params['account_type'] = str(account_type)
        """
        获取某一个业务线资产估值。
        0.预估总资产
        1.币币账户
        3.交割账户
        5.币币杠杆
        6.资金账户
        9.永续合约
        12.期权
        15.交割usdt保证金账户
        16.永续usdt保证金账户
        默认为0，查询总资产
        """
        params['valuation_currency'] = valuation_currency
        obj = self.sendCmd(method='GET', request_path = '/api/account/v3/asset-valuation', params = params, isSign = True)
        return obj
