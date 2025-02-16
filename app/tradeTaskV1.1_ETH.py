#一個照規則自動下單的程式
#程式的邏輯不重要，反正照這個跑下去會賠錢XD

import mysql.connector
from mysql.connector import Error
import logging
import requests
import json
import time
import sys
import base64
import hashlib
import hmac
import datetime
from urllib import parse
import urllib.parse
from utils.urlparamsbuilder import UrlParamsBuilder

global api_key
global secret_key
api_key = ''
secret_key = ''

global taskState, taskPair, taskStPrice, taskMin, taskMax, total, taskMoney, taskLeverage, quantityPrecision, pricePrecision, taskBaseTimes, lastOrderTime
taskState = 0  #任務狀態 0:未開始 1：雙向下單 2：上漲1%以上 3：下跌1%以上 
taskPair = sys.argv[1]  #交易對
taskStPrice = 0  #任務起始價格
taskMin = 99999999999  #下跌區間最低價格
taskMax = -100 #上漲區間最高價格
total = 0 #總盈虧
taskMoney = int(sys.argv[2]) #下單保證金，單位為USDT，如果為1000，則買空、買多兩者皆下單1000USDT
taskLeverage = int(sys.argv[3]) #槓桿倍率 
quantityPrecision = 0 #數量最小精度
pricePrecision = 0 #價格最小精度
taskBaseTimes = 0 #價格碰觸taskMax次數

lastOrderTime = 0 #上一次下單時間點 timestamp

def getExchangeInfo():
    logging.info('getExchangeInfo: ')
    url = host + '/fapi/v1/exchangeInfo'
    resp = requests.get(url)
    if(resp.status_code == 200):
        obj = json.loads(resp.text)
        newObj = dict()
        for p in obj['symbols']:
            newObj[p['symbol'] + '_' + 'pricePrecision'] = p['pricePrecision']
            newObj[p['symbol'] + '_' + 'quantityPrecision'] = p['quantityPrecision']
        resp.close()
        return newObj
    else:
        print(resp.status_code)
        print(resp.text)
    return None

def init():
    FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, filename= taskPair + '_trade.log', filemode='w', format=FORMAT)
    global host, quantityPrecision, pricePrecision
    #global conn
    host = 'https://fapi.binance.com'
    #conn = connectDB()
    info = getExchangeInfo()
    quantityPrecision = info[taskPair + '_quantityPrecision'] - 2 
    pricePrecision = info[taskPair + '_pricePrecision'] - 2
    if(quantityPrecision < 0):
        quantityPrecision = 0
    if(pricePrecision < 0):
        pricePrecision = 0

def get_current_timestamp():
    return int(round(time.time() * 1000))

def create_signature(secret_key, builder):
    query_string = builder.build_url()
    signature = hmac.new(secret_key.encode(), msg=query_string.encode(), digestmod=hashlib.sha256).hexdigest()
    builder.put_url("signature", signature)

def getHeader():
    header = dict()
    header.update({"Content-Type": "application/x-www-form-urlencoded"})
    header.update({"X-MBX-APIKEY": api_key})
    return header

def sendCancelAllOrder(pair):
    logging.info('sendCancelAllOrder: ')
    url = host + '/fapi/v1/allOpenOrders'

    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    create_signature(secret_key, builder)

    resp = requests.delete(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None


def getUserData():
    logging.info('getUserData: ')
    url = host + '/fapi/v2/account'

    builder = UrlParamsBuilder()
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))

    create_signature(secret_key, builder)

    resp = requests.get(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        #logging.info(resp.text)
        obj = json.loads(resp.text)
        newObj = dict()
        for p in obj['positions']:
            newObj[p['symbol'] + '_' + p['positionSide']] = p['positionAmt']
        resp.close()
        return newObj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None

def sendSellLong(pair, amount):
    logging.info('sendSellLong: ' + pair + ' ' + str(amount))
    url = host + '/fapi/v1/order'
    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url('side', 'SELL') #SELL, BUY
    builder.put_url('positionSide', 'LONG')  #LONG 或 SHORT
    builder.put_url('type', 'MARKET')  #订单类型 LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
    builder.put_url('quantity', amount) #數量
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    create_signature(secret_key, builder)
    resp = requests.post(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None

def sendBuyShort(pair, amount):
    logging.info('sendBuyShort: ' + pair + ' ' + str(amount))
    url = host + '/fapi/v1/order'
    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url('side', 'BUY') #SELL, BUY
    builder.put_url('positionSide', 'SHORT')  #LONG 或 SHORT
    builder.put_url('type', 'MARKET')  #订单类型 LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
    builder.put_url('quantity', amount) #數量  
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    create_signature(secret_key, builder)
    resp = requests.post(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None


def sendBuyLong(pair, amount):
    logging.info('sendBuyLong: ' + pair + ' ' + str(amount))
    url = host + '/fapi/v1/order'
    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url('side', 'BUY') #SELL, BUY
    builder.put_url('positionSide', 'LONG')  #LONG 或 SHORT
    builder.put_url('type', 'MARKET')  #订单类型 LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
    builder.put_url('quantity', amount) #數量
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    create_signature(secret_key, builder)
    resp = requests.post(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None

def sendSellShort(pair, amount):
    logging.info('sendSellShort: ' + pair + ' '+ str(amount))
    url = host + '/fapi/v1/order'
    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url('side', 'SELL') #SELL, BUY
    builder.put_url('positionSide', 'SHORT')  #LONG 或 SHORT
    builder.put_url('type', 'MARKET')  #订单类型 LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
    builder.put_url('quantity', amount) #數量
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    create_signature(secret_key, builder)
    resp = requests.post(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None

def closeAllPos(pair):
    pairAmounts = getUserData()
    if(pairAmounts is None):
        logging.info('get user data postion ERROR!')
        return None
    pos_long = abs(float(pairAmounts[pair + '_LONG']))
    pos_short = abs(float(pairAmounts[pair + '_SHORT']))
    if(pos_long != 0):
        logging.info('a')
        sendSellLong(pair, pos_long)
    if(pos_short != 0):
        logging.info('b')
        sendBuyShort(pair, pos_short)


def sendSellLongStop(pair, amount, stopPrice):
    logging.info('sendSellLongStop: ' + pair + ' ' + str(amount) + ' ' + str(stopPrice))
    url = host + '/fapi/v1/order'
    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url('side', 'SELL') #SELL, BUY
    builder.put_url('positionSide', 'LONG')  #LONG 或 SHORT
    builder.put_url('type', 'STOP_MARKET')  #订单类型 LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
    builder.put_url('quantity', amount) #數量
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    builder.put_url('workingType', 'MARK_PRICE')  #MARK_PRICE(标记价格), CONTRACT_PRICE(合约最新价)
    builder.put_url('stopPrice', stopPrice)  
    create_signature(secret_key, builder)
    resp = requests.post(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None

def sendBuyShortStop(pair, amount, stopPrice):
    logging.info('sendBuyShortStop: ' + pair + ' ' + str(amount) + ' ' + str(stopPrice))
    url = host + '/fapi/v1/order'
    builder = UrlParamsBuilder()
    builder.put_url('symbol', pair)
    builder.put_url('side', 'BUY') #SELL, BUY
    builder.put_url('positionSide', 'SHORT')  #LONG 或 SHORT
    builder.put_url('type', 'STOP_MARKET')  #订单类型 LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
    builder.put_url('quantity', amount) #數量
    builder.put_url("timestamp", str(get_current_timestamp() - 1000))
    builder.put_url('workingType', 'MARK_PRICE')  #MARK_PRICE(标记价格), CONTRACT_PRICE(合约最新价)
    builder.put_url('stopPrice', stopPrice)  
    create_signature(secret_key, builder)
    resp = requests.post(url, params = builder.build_url(), headers=getHeader())
    if(resp.status_code == 200):
        logging.info(resp.text)
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp.text)
    return None


def clearTask():
    #平艙
    closeAllPos(taskPair)
    #取消所有掛單
    sendCancelAllOrder(taskPair)

    global taskState, taskStPrice, taskMin, taskMax, taskBaseTimes
    taskState = 0
    taskStPrice = 0
    taskMin = 99999999999
    taskMax = -100
    taskBaseTimes = 0

#檢查艙位 Long 是否存在
#return true or false
def isPosLongExist():
    pairAmounts = getUserData()
    if(pairAmounts is None):
        logging.info('get user data postion ERROR!')
    pos_long = abs(float(pairAmounts[taskPair + '_LONG']))
    if(pos_long == 0):
        return False
    return True

#檢查艙位 Short 是否存在
#return true or false
def isPosShortExist():
    pairAmounts = getUserData()
    if(pairAmounts is None):
        logging.info('get user data postion ERROR!')
    pos_short = abs(float(pairAmounts[taskPair + '_SHORT']))    
    if(pos_short == 0):
        return False
    return True

#計算倉位數量
def getAmount(curPrice):
    amount = taskMoney * taskLeverage / curPrice
    return round(amount, quantityPrecision)

def startTask(curPrice):
    global taskState, taskPair, taskStPrice, taskMin, taskMax, taskBaseTimes, lastOrderTime

    if(taskState == 0):
        #紀錄 taskStPrice 為現價
        taskStPrice = curPrice
        taskState = 1
        taskMin = curPrice
        taskMax = curPrice
    elif (taskState == 1):
        if(curPrice > taskMax ):
            taskMax = curPrice
        if(curPrice < taskMin ):
            taskMin = curPrice

        #如果現在時間比上一次下單時間低於0.5小時，則跳過
        
        if(get_current_timestamp() - lastOrderTime < 30 * 60 * 1000):
            return 
        
        
        if(curPrice >= taskMin * 1.01):
            #下多單
            sendBuyLong(taskPair, getAmount(curPrice))
            sendSellLongStop(taskPair, getAmount(curPrice), round(curPrice * 0.99, pricePrecision))
            taskState = 2
            taskStPrice = curPrice
            lastOrderTime = get_current_timestamp()
            taskMin = 99999999999
            taskMax = -100
        elif (curPrice < taskMax * 0.99):
            #下空單
            sendSellShort(taskPair, getAmount(curPrice))
            sendBuyShortStop(taskPair, getAmount(curPrice), round(curPrice * 1.01, pricePrecision))
            taskState = 3
            taskStPrice = curPrice
            lastOrderTime = get_current_timestamp()
            taskMin = 99999999999
            taskMax = -100

    elif (taskState == 2):

        adv = (curPrice - taskStPrice) / taskStPrice

        #直接砍掉
        if(curPrice <= taskStPrice * 0.995):
            out('AA: ' + str(adv))
            logging.info(str(taskStPrice) + ' => ' + str(curPrice))
            clearTask()
            return

        #檢查艙位多單是否存在，如果不是clearTask 同時return
        """
        if(isPosLongExist() == False):
            clearTask()
            return
        """
        #以下內容下單超過十分鐘才檢查
        if(get_current_timestamp() - lastOrderTime > 10 * 60 * 1000):
            if(curPrice < taskStPrice):
                if(taskBaseTimes >= 0):
                    out('A: ' + str(adv))
                    logging.info(str(taskStPrice) + ' => ' + str(curPrice))
                    #sum(adv * 2000 * 10)
                    #平艙
                    clearTask()
                    return
                taskBaseTimes = taskBaseTimes + 1
            elif (taskMax > 0 and curPrice <= (taskStPrice + (taskMax - taskStPrice) /2)):
                out('B: ' + str(adv))
                logging.info(str(taskStPrice) + ' => ' + str(curPrice))
                #sum(adv * 2000 * 10)
                #平艙
                clearTask()
                return
            elif (taskMax > 0 and curPrice <= (taskMax * 0.995)):
                out('C: ' + str(adv))
                logging.info(str(taskStPrice) + ' => ' + str(curPrice))
                #sum(adv * 2000 * 10)
                #平艙
                clearTask()
                return
        if(curPrice > taskMax ):
            taskMax = curPrice
    elif (taskState == 3):

        adv = (curPrice - taskStPrice) / taskStPrice

        #直接砍掉
        if(curPrice >= taskStPrice * 1.005):
            out('DD: ' + str(adv))
            logging.info(str(taskStPrice) + ' => ' + str(curPrice))
            clearTask()
            return

        #檢查艙位空單是否存在，如果不是clearTask 同時return
        #改為每十秒一次 不檢查艙位了
        """
        if(isPosShortExist() == False):
            clearTask()
            return
        adv = (taskStPrice - curPrice) / taskStPrice
        """
        #以下內容下單超過十分鐘才檢查
        if(get_current_timestamp() - lastOrderTime > 10 * 60 * 1000):
            if(curPrice > taskStPrice):
                if(taskBaseTimes >= 0):
                    out('D: ' + str(adv))
                    logging.info(str(taskStPrice) + ' => ' + str(curPrice))
                    #sum(adv * 2000 * 10)
                    #平艙
                    clearTask()
                    return
                    #startTask(curPrice)
                taskBaseTimes = taskBaseTimes + 1
            elif (taskMin < 99999999999 and curPrice >= (taskStPrice * 0.99 - (taskStPrice * 0.99 - taskMin) /2)):
                out('E: ' + str(adv))
                logging.info(str(taskStPrice) + ' => ' + str(curPrice))
                #sum(adv * 2000 * 10)
                #平艙
                clearTask()
                return
                #startTask(curPrice)
            elif (taskMin < 99999999999 and curPrice >= (taskMin * 1.005)):
                out('F: ' + str(adv))
                logging.info(str(taskStPrice) + ' => ' + str(curPrice))
                #sum(adv * 2000 * 10)
                #平艙
                clearTask()
                return
                #startTask(curPrice)
        if(curPrice  < taskMin ):
            taskMin = curPrice
    #logging.info(curPrice)
    #logging.info(taskState)

def out(msg):
    logging.info(msg)

"""
def sum(val):
    global total
    total = total + val
    total = total - 1.2 #手續費
    logging.info('total:' + str(total))
"""

def getLastestPrice():
    url = host + '/fapi/v1/ticker/price'
    my_params = {
        'symbol': taskPair
        }
    resp = requests.get(url, params = my_params)
    if(resp.status_code == 200):
        obj = json.loads(resp.text)
        resp.close()
        return obj
    else:
        logging.info(resp.status_code)
        logging.info(resp)
    return None

def start():
    logging.info('GO!')
    logging.info('pair: ' + taskPair)
    logging.info('money: ' + str(taskMoney))
    clearTask()
    while(True):
        """
        if(taskState == 0 or taskState == 1):
            time.sleep(10)

        if(taskState == 2 or taskState == 3):
            time.sleep(600)
        """
        obj = getLastestPrice()
        if(obj is None):
            continue
        curPrice = float(obj['price'])
        logging.info(curPrice)
        logging.info(taskState)
        startTask(curPrice)
        if(taskState == 0):
            startTask(curPrice)
        
        time.sleep(10)
        #等待十秒
init()
start()
