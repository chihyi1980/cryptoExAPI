#發送每日資金費率報表並發Email給自己

from okex.okexAPI import okexAPI
from db.db import db
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from okex.okexAPIv5 import okexAPIv5

db = db('okex')
okex = okexAPI()
okexV5 = okexAPIv5()

#取得永續合約所持所有倉位
def getAllPositionId():
    lstPos = []
    temp = okexV5.getPosition()

    for item in temp['data']:
        lstPos.append(item['instId'])

    return lstPos

#取得所有交易對，近size次資金費率，依總和排序後，顯示出來
def getLastestRate(size):
    lstRateSum = dict()
    lstRateRow = dict()
    outStr = ''
    
    #取出有哪些交易對
    temp = okex.getSwapInstruments()

    #取出目前持有倉位
    aryPos = getAllPositionId()

    for item in temp:
        time.sleep(.1)
        rates = okex.getFundingRateHistory(item['instrument_id'], size)

        sum = 0.0
        strRow = ''
        for rateItem in rates:
            
            #取得資金費率顯示字串
            strRow = strRow + ' , ' + str(round(float(rateItem['realized_rate']) * 10000 , 2))

            #取得資金費率總和
            sum = sum + float(rateItem['realized_rate'])

        lstRateSum[item['instrument_id']] = sum
        lstRateRow[item['instrument_id']] = strRow


    for id in sorted(lstRateSum, key=lstRateSum.get, reverse=True):
        if(id in aryPos):
            outStr = outStr + '*' + id + ' : ' +  lstRateRow[id] + '\n'
        else:
            outStr = outStr + id + ' : ' +  lstRateRow[id] + '\n'
    
    return outStr


#取得最近三次，分別為08:00 / 00:00 / 前一天 16:00 收入流水並且排序
def get24hrFundingData():
    outStr = ''

    dtNow = datetime.now()
    endTime = dtNow.replace(hour=8, minute=0, second=0, microsecond=0)
    startTime = endTime - timedelta(hours = 16)
    objData = db.queryOkexFundingLog(startTime, endTime)
    db.closeDBConn()

    outStr = 'Daily report : \n'
    outStr = outStr + 'period : ' + str(startTime) + ' ~ ' + str(endTime) + '\n'
    outStr = outStr + '-- \n'
    sum = 0.0
    for pair in sorted(objData, key=objData.get, reverse=True):
        sum = sum + float(objData[pair])
        outStr = outStr + pair + ' : ' + str(objData[pair]) + '\n'

    outStr = outStr + '-- \n'
    outStr = outStr + 'sum : ' + str(sum) + '\n'
    return outStr

#取得通用帳戶中USDT可用餘額
def getAvailEq():
    obj = okexV5.getBalance()
    detail = obj['data'][0]['details']
    return detail[0]['availEq']


def geneOut():
    outStr = ''
    outStr = outStr + 'Available balance: ' + getAvailEq() + '\n'
    outStr = outStr + '======================= \n'
    outStr = outStr + get24hrFundingData()
    outStr = outStr + '======================= \n'
    outStr = outStr + 'Lastest 10 times funding: \n'
    outStr = outStr + getLastestRate(10)
    return outStr


def sendMail(outStr):

    datetime_dt = datetime.today() # 獲得當地時間
    datetime_str = datetime_dt.strftime('%Y/%m/%d')  # 格式化日期

    content = MIMEMultipart()  #建立MIMEMultipart物件
    content["subject"] = 'Daily Report: OKEX ' + datetime_str  #郵件標題
    content["from"] = 'chihyi1980@gmail.com'  #寄件者
    content["to"] = 'chihyi1980@gmail.com' #收件者
    content.attach(MIMEText(outStr))  #郵件內容

    with smtplib.SMTP(host='smtp.gmail.com', port='587') as smtp:  # 設定SMTP伺服器
        try:
            smtp.ehlo()  # 驗證SMTP伺服器
            smtp.starttls()  # 建立加密傳輸
            smtp.login('chihyi1980@gmail.com', '')  # 登入寄件者gmail，第二個參數是gmail api key要跟gmail申請才有
            smtp.send_message(content)  # 寄送郵件
        except Exception as e:
            print("Error message: ", e)

def start():
    sendMail(geneOut())

start()
