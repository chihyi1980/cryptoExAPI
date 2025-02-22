from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import json
from config import Config

Base = declarative_base()

class FundingHistory(Base):
    __tablename__ = 'funding_history'
    
    time = Column(DateTime, primary_key=True)
    pair = Column(String(50), primary_key=True)
    amount = Column(Float)
    billId = Column(String(50))

    def to_dict(self):
        return {
            'time': self.time.isoformat() if self.time else None,
            'pair': self.pair,
            'amount': float(self.amount) if self.amount else 0.0,
            'billId': self.billId
        }

class AssetValue(Base):
    __tablename__ = 'asset_value'
    
    date = Column(DateTime, primary_key=True)
    value = Column(Float)

    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'value': float(self.value) if self.value else 0.0
        }

class Klines(Base):
    __tablename__ = 'klines'
    
    trade_time = Column(DateTime, primary_key=True)
    pair = Column(String(50), primary_key=True)
    intr = Column(String(20))
    start_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    end_price = Column(Float)
    volume = Column(Float)
    money = Column(Float)

    def to_dict(self):
        return {
            'time': self.trade_time.isoformat() if self.trade_time else None,
            'pair': self.pair,
            'interval': self.intr,
            'start_price': float(self.start_price) if self.start_price else 0.0,
            'high_price': float(self.high_price) if self.high_price else 0.0,
            'low_price': float(self.low_price) if self.low_price else 0.0,
            'end_price': float(self.end_price) if self.end_price else 0.0,
            'volume': float(self.volume) if self.volume else 0.0,
            'money': float(self.money) if self.money else 0.0
        }

class db:
    def __init__(self, dbName):
        self.dbName = dbName
        self.engine = self.connectDB()
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def connectDB(self):
        connection_string = f'mysql+mysqlconnector://{Config.DB_USER}:{Config.DB_PWD}@{Config.DB_HOST}/{self.dbName}'
        return create_engine(connection_string)

    def closeDBConn(self):
        self.engine.dispose()

    def insertOkexFundingHistory(self, lstData):
        session = self.Session()
        try:
            for data in lstData:
                funding = FundingHistory(
                    time=data['time'],
                    pair=data['pair'],
                    amount=data['amount'],
                    billId=data['billId']
                )
                session.add(funding)
            session.commit()
            return json.dumps({'status': 'success'})
        except Exception as e:
            session.rollback()
            return json.dumps({'status': 'error', 'message': str(e)})
        finally:
            session.close()

    def queryOkexFundingLog(self, startTime, endTime):
        session = self.Session()
        try:
            results = session.query(
                FundingHistory.pair,
                func.sum(FundingHistory.amount).label('total_amount')
            ).filter(
                FundingHistory.time >= startTime,
                FundingHistory.time <= endTime
            ).group_by(FundingHistory.pair).all()
            
            return json.dumps({pair: float(amount) for pair, amount in results})
        finally:
            session.close()

    def queryLastestBillId(self):
        session = self.Session()
        try:
            result = session.query(FundingHistory.billId).order_by(
                FundingHistory.time.desc()
            ).first()
            return json.dumps({'billId': result[0] if result else None})
        finally:
            session.close()

    def queryOkexAssetValue(self, date):
        session = self.Session()
        try:
            result = session.query(AssetValue).filter(
                AssetValue.date == date
            ).first()
            return json.dumps(result.to_dict() if result else {})
        finally:
            session.close()

    def insertOkexAssetValue(self, date, value):
        session = self.Session()
        try:
            asset_value = AssetValue(date=date, value=value)
            session.add(asset_value)
            session.commit()
            return json.dumps({'status': 'success'})
        except Exception as e:
            session.rollback()
            return json.dumps({'status': 'error', 'message': str(e)})
        finally:
            session.close()

    def insertBinanceKlines(self, lstData):
        session = self.Session()
        try:
            for data in lstData:
                kline = Klines(
                    trade_time=data['time'],
                    pair=data['pair'],
                    intr=data['interval'],
                    start_price=data['start_price'],
                    high_price=data['high_price'],
                    low_price=data['low_price'],
                    end_price=data['end_price'],
                    volume=data['volume'],
                    money=data['money']
                )
                session.add(kline)
            session.commit()
            return json.dumps({'status': 'success'})
        except Exception as e:
            session.rollback()
            return json.dumps({'status': 'error', 'message': str(e)})
        finally:
            session.close()

    def queryBinanceKlines(self, pair, startTime, endTime):
        session = self.Session()
        try:
            results = session.query(Klines).filter(
                Klines.pair == pair,
                Klines.trade_time >= startTime,
                Klines.trade_time <= endTime
            ).all()
            return json.dumps([kline.to_dict() for kline in results])
        finally:
            session.close()

    def queryBinanceKlinesPairList(self):
        session = self.Session()
        try:
            results = session.query(distinct(Klines.pair)).all()
            return json.dumps([pair[0] for pair in results])
        finally:
            session.close()
