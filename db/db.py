import mysql.connector
from mysql.connector import Error
from config import Config

class db(object):
    
    def __init__(self, dbName):
        self.dbName = dbName
        self.conn = self.connectDB()


    def connectDB(self):
        # 連接 MySQL/MariaDB 資料庫
        connection = mysql.connector.connect(
            host=Config.DB_HOST,          # 主機名稱
            #host='db-cont',          # 主機名稱
            database= self.dbName, # 資料庫名稱
            user=Config.DB_USER,        # 帳號
            password=Config.DB_PWD)  # 密碼
        return connection

    def closeDBConn(self):
        self.conn.close()

    def insertOkexFundingHistory(self, lstData):

        cursor = self.conn.cursor(buffered=True)
        try:
            for data in lstData :
                sql = 'INSERT INTO funding_history (time, pair, amount, billId) VALUES (%s, %s, %s, %s)'
                val = (data['time'], data['pair'], data['amount'], data['billId'])
                cursor.execute(sql, val)
            self.conn.commit()

        except Error as e:
            print("資料庫連接失敗：", e)

        finally:
            if (self.conn.is_connected()):
                cursor.close()

    def queryOkexFundingLog(self, startTime, endTime):

        sql = 'SELECT pair , amount FROM funding_history WHERE TIME >= %s AND TIME <= %s'
        val = (str(startTime), str(endTime))
        cursor = self.conn.cursor()
        cursor.execute(sql, val)

        objData = dict()
        for pair , amount in cursor:
            if(objData.get(pair) is None):
                objData[pair] = 0.0
            objData[pair] = objData[pair] + float(amount)
        
        return objData
    
    def queryLastestBillId(self):
        sql = 'SELECT billId FROM funding_history ORDER BY billId DESC'
        cursor = self.conn.cursor()
        cursor.execute(sql)

        data = cursor.fetchone()[0]
        cursor.fetchall()
        return data

    def queryOkexAssetValue(self, date):
        sql = 'SELECT date, value FROM asset_value WHERE date = %s'
        val = (str(date))
        cursor = self.conn.cursor()
        cursor.execute(sql, val)

        objData = dict()
        for date , value in cursor:
            objData['date'] = date
            objData['value'] = value
        
        return objData

    def insertOkexAssetValue(self, date, value):
        try:
            sql = 'INSERT INTO asset_value (date,  value) VALUES (%s, %s)'
            val = (date, value)
            cursor = self.conn.cursor()
            cursor.execute(sql, val)
            self.conn.commit()

        except Error as e:
            print("資料庫連接失敗：", e)

        finally:
            if (self.conn.is_connected()):
                cursor.close()

    def insertBinanceKlines(self, lstData):
        try:
            for data in lstData :
                sql = 'INSERT INTO klines (trade_time,  pair, intr, start_price, high_price, low_price, end_price, volume, money) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
                val = (data['time'], data['pair'], data['interval'], data['start_price'], data['high_price'], data['low_price'], data['end_price'], data['volume'], data['money'])
                cursor = self.conn.cursor()
                cursor.execute(sql, val)
            self.conn.commit()

        except Error as e:
            print('資料庫連接失敗：', e)

    def queryBinanceKlines(self, pair, startTime, endTime):
        try:
            sql = 'SELECT trade_time,  pair, intr, start_price, high_price, low_price, end_price, volume, money FROM klines WHERE pair = %s and trade_time >= %s and trade_time <= %s'
            val = (pair, startTime, endTime)
            cursor = self.conn.cursor()
            cursor.execute(sql, val)
            rows = cursor.fetchall()
            if rows is None:
                return []
            else:
                return rows
                
        except Error as e:
            print('資料庫連接失敗：', e)   

        finally:
            if (self.conn.is_connected()):
                cursor.close()    
                
    def queryBinanceKlinesPairList(self):
        try:
            sql = 'SELECT DISTINCT pair FROM klines'
            cursor = self.conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            if rows is None:
                return []
            else:
                # Extract the first element from each tuple and return as a list
                return [row[0] for row in rows]
            
        except Error as e:
            print('資料庫連接失敗：', e)
            return []

        finally:
            if (self.conn.is_connected()):
                cursor.close()