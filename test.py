from db.db_orm import db
from datetime import datetime, timedelta
import json
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
import math
import pandas as pd

class Position(Enum):
    NONE = "無倉位"
    LONG = "做多"
    SHORT = "做空"

@dataclass
class Trade:
    time: str
    price: float
    action: str
    position: Position
    size: float  # 倉位大小
    pnl: float

class TradingSimulator:
    def __init__(self, initial_capital=10000.0):
        self.position = Position.NONE
        self.entry_price = 0.0
        self.total_pnl = 0.0
        self.trades: List[Trade] = []
        self.entry_time = None
        self.min_hold_time = timedelta(hours=0)  # 最小持倉時間改為0小時
        self.last_trade_time = None
        self.min_trade_interval = timedelta(hours=0)  # 交易間隔至少0小時
        self.position_size = 0.0  # 當前倉位大小
        self.capital = initial_capital  # 初始資金
        self.max_position_value = 0.0  # 最大持倉金額
        self.daily_trades = {}  # 記錄每日交易次數
        self.max_daily_trades = 10  # 每日最大交易次數
        self.risk_per_trade = 0.05  # 每筆交易風險5%資金
        self.first_trade_time = None  # 記錄第一筆交易的時間
        self.trailing_stop = 0.0  # 追踪止損價格
        self.highest_price = 0.0  # 記錄最高價格
        self.lowest_price = float('inf')  # 記錄最低價格

    def parse_time(self, time_str: str) -> datetime:
        """统一解析时间字符串为datetime对象"""
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')

    def calculate_position_size(self, price: float, stop_loss: float) -> float:
        """計算倉位大小"""
        risk_amount = self.capital * self.risk_per_trade
        price_risk = abs(price - stop_loss)
        position_size = risk_amount / price_risk
        
        # 限制單筆交易金額不超過100
        max_position_size = 100 / price
        position_size = min(position_size, max_position_size)
        
        return position_size

    def update_daily_trades(self, time: str):
        """更新每日交易次數"""
        date = time.split('T')[0]
        self.daily_trades[date] = self.daily_trades.get(date, 0) + 1

    def can_trade_today(self, time: str) -> bool:
        """檢查是否達到每日交易上限"""
        date = time.split('T')[0]
        return self.daily_trades.get(date, 0) < self.max_daily_trades

    def calculate_volatility(self, past_records: List[Dict], window: int = 24) -> float:
        """計算價格波動率"""
        if len(past_records) < window:
            return 0.0
        
        recent_records = past_records[-window:]
        prices = [record['start_price'] for record in recent_records]
        returns = [(prices[i+1] - prices[i])/prices[i] for i in range(len(prices)-1)]
        if not returns:
            return 0.0
        return math.sqrt(sum(r*r for r in returns)/(len(returns)-1))

    def calculate_price_change(self, current_price: float, past_24h_records: List[Dict]) -> float:
        """計算當前價格相對於過去24小時平均價格的變化百分比"""
        if not past_24h_records:
            return 0.0
        avg_price = sum(record['start_price'] for record in past_24h_records) / len(past_24h_records)
        return (current_price - avg_price) / avg_price

    def calculate_volume_ratio(self, current_volume: float, past_24h_records: List[Dict]) -> float:
        """計算當前交易量相對於過去24小時平均交易量的比率"""
        if not past_24h_records:
            return 0.0
        avg_volume = sum(record['volume'] for record in past_24h_records) / len(past_24h_records)
        return current_volume / avg_volume if avg_volume > 0 else 0.0

    def confirm_trend(self, past_records: List[Dict], window: int = 24) -> str:
        """確認價格趨勢，使用24個時間點"""
        if len(past_records) < window:
            return "無趨勢"
        
        recent_records = past_records[-window:]
        price_changes = [
            (recent_records[i+1]['start_price'] - recent_records[i]['start_price']) 
            for i in range(len(recent_records)-1)
        ]
        
        up_moves = sum(1 for change in price_changes if change > 0)
        down_moves = sum(1 for change in price_changes if change < 0)
        
        if up_moves > down_moves * 2:  # 提高趨勢確認門檻
            return "上升"
        elif down_moves > up_moves * 2:
            return "下降"
        return "盤整"

    def calculate_pnl(self, current_price: float) -> float:
        """計算當前倉位的盈虧"""
        if self.position == Position.LONG:
            return (current_price - self.entry_price) * self.position_size
        elif self.position == Position.SHORT:
            return (self.entry_price - current_price) * self.position_size
        return 0.0

    def update_price_extremes(self, current_price: float):
        """更新最高價和最低價"""
        if self.position == Position.LONG:
            self.highest_price = max(self.highest_price, current_price)
        elif self.position == Position.SHORT:
            self.lowest_price = min(self.lowest_price, current_price)

    def calculate_dynamic_stop_loss(self, current_price: float, current_time: str, past_records: List[Dict]) -> float:
        """計算動態止損價格
        
        基於以下因素：
        1. 價格波動率（基礎值翻倍）
        2. 當前盈利情況
        3. 市場趨勢
        4. 持倉時間（3小時內逐漸收窄）
        """
        # 計算波動率
        volatility = self.calculate_volatility(past_records, window=24)
        
        # 計算當前盈虧比例
        pnl_percentage = self.calculate_pnl(current_price) / self.capital
        
        # 獲取市場趨勢
        trend = self.confirm_trend(past_records)
        
        # 根據盈利情況調整止損，基礎值翻倍
        if pnl_percentage > 0.1:  # 盈利超過10%
            stop_percentage = max(0.08, volatility * 2)  # 最小保留8%利潤（原本4%的兩倍）
        else:
            stop_percentage = max(0.12, volatility * 4)  # 基礎止損為波動率的4倍，最小12%（原本6%的兩倍）
            
        # 根據趨勢調整止損
        if (self.position == Position.LONG and trend == "上升") or \
           (self.position == Position.SHORT and trend == "下降"):
            stop_percentage *= 0.8  # 順勢交易收緊止損
        else:
            stop_percentage *= 1.2  # 逆勢交易放寬止損
            
        # 根據持倉時間調整止損（3小時內從2倍逐漸收窄到1倍）
        if self.entry_time:
            current_dt = self.parse_time(current_time)
            hours_held = (current_dt - self.entry_time).total_seconds() / 3600
            if hours_held <= 3:
                # 計算時間衰減因子（3小時內從2線性降至1）
                time_factor = 1 + max(0, (3 - hours_held) / 3)
                # 應用時間衰減
                stop_percentage *= time_factor
                
        return stop_percentage

    def should_close_position(self, current_time: str, current_price: float, current_volume: float, past_24h_records: List[Dict], past_records: List[Dict]) -> bool:
        """判斷是否應該平倉
        
        Returns:
            bool: 是否平倉
        """
        if not self.position:
            return False
            
        # 檢查最小持倉時間
        current_dt = self.parse_time(current_time)
        if current_dt - self.entry_time < self.min_hold_time:
            return False
            
        # 檢查單次交易虧損是否超過5%
        current_pnl = self.calculate_pnl(current_price)
        current_loss_percentage = abs(current_pnl) / self.capital if current_pnl < 0 else 0
        
        # 如果虧損超過4.5%，記錄警告
        if current_loss_percentage > 0.045:
            # 找到上一根K線的資訊
            if past_records and len(past_records) >= 2:
                prev_kline = past_records[-2]  # 取得上一根K線
                prev_close = float(prev_kline['end_price'])
                prev_pnl = self.calculate_pnl(prev_close)
                prev_loss_percentage = abs(prev_pnl) / self.capital if prev_pnl < 0 else 0
                
                print(f"\n====== 接近強制平倉的警告 ======")
                print(f"交易對: {self.symbol}")
                print(f"當前時間: {current_time}")
                print(f"上一根K線時間: {prev_kline['time']}")
                print(f"上一根K線開盤價: {prev_kline['start_price']}")
                print(f"上一根K線最高價: {prev_kline['high_price']}")
                print(f"上一根K線最低價: {prev_kline['low_price']}")
                print(f"上一根K線收盤價: {prev_kline['end_price']}")
                print(f"上一根K線成交量: {prev_kline['volume']}")
                print(f"上一根K線虧損百分比: {prev_loss_percentage*100:.2f}%")
                print(f"當前價格: {current_price}")
                print(f"當前虧損百分比: {current_loss_percentage*100:.2f}%")
                print("=====================================\n")
            else:
                print(f"\n警告：無法獲取 {self.symbol} 的上一根K線資訊")
                print(f"當前時間: {current_time}")
                print(f"當前價格: {current_price}")
                print(f"當前虧損: {current_loss_percentage*100:.2f}%")
                print(f"past_records 長度: {len(past_records) if past_records else 0}\n")
        
        # 如果虧損超過5%，強制平倉
        if current_loss_percentage > 0.05:
            return True
            
        # 更新最高價和最低價
        self.update_price_extremes(current_price)
        
        # 計算動態止損百分比
        stop_percentage = self.calculate_dynamic_stop_loss(current_price, current_time, past_records)
        
        # 根據倉位方向判斷止損
        if self.position == Position.LONG:
            # 計算從最高點回落的百分比
            drawdown = (self.highest_price - current_price) / self.highest_price
            return drawdown >= stop_percentage
            
        elif self.position == Position.SHORT:
            # 計算從最低點反彈的百分比
            pullback = (current_price - self.lowest_price) / self.lowest_price
            return pullback >= stop_percentage
            
        return False

    def calculate_hour_average_price(self, past_records: List[Dict]) -> float:
        """計算過去一小時的平均價格"""
        if not past_records:  # 檢查是否有歷史數據
            return 0.0
            
        current_time = self.parse_time(past_records[-1]['time'])
        hour_ago = current_time - timedelta(hours=1)
        
        # 篩選過去一小時的記錄
        hour_records = [
            record for record in past_records
            if self.parse_time(record['time']) >= hour_ago
        ]
        
        if not hour_records:
            return 0.0
            
        # 計算平均價格（使用 start_price 作為價格）
        total_price = sum(float(record['start_price']) for record in hour_records)
        return total_price / len(hour_records)

    def calculate_recent_volume_average(self, past_records: List[Dict], minutes: int = 15):
        """計算最近N分鐘的平均交易量"""
        if not past_records:
            return 0
        
        current_time = self.parse_time(past_records[-1]['time'])
        recent_records = [
            record for record in past_records
            if (current_time - self.parse_time(record['time'])).total_seconds() <= minutes * 60
        ]
        
        if not recent_records:
            return 0
            
        total_volume = sum(float(record['volume']) for record in recent_records)
        return total_volume / len(recent_records)

    def calculate_15min_price_change(self, current_price: float, past_records: List[Dict]) -> float:
        """計算過去15分鐘內的最大價格變化
        
        檢查15分鐘內所有價格點與當前價格的差距，返回最大的漲跌幅
        正值表示上漲，負值表示下跌
        """
        if not past_records:
            return 0
            
        current_time = self.parse_time(past_records[-1]['time'])
        records_15min = [
            record for record in past_records 
            if (current_time - self.parse_time(record['time'])).total_seconds() <= 15 * 60
        ]
        
        if not records_15min:
            return 0
            
        # 檢查所有價格點（包括開盤價、最高價、最低價、收盤價）
        max_change = 0
        for record in records_15min:
            prices = [
                float(record['start_price']),
                float(record['high_price']),
                float(record['low_price']),
                float(record['end_price'])
            ]
            
            # 計算每個價格點與當前價格的變化百分比
            for price in prices:
                change = (current_price - price) / price
                # 保存絕對值最大的變化
                if abs(change) > abs(max_change):
                    max_change = change
                    
        return max_change

    def process_price(self, time: str, current_price: float, current_volume: float, past_24h_records: List[Dict], past_records: List[Dict]):
        """處理每個價格點"""
        current_time = self.parse_time(time)

        # 檢查是否已超過第一筆交易後的30天
        if self.first_trade_time is not None:
            if current_time - self.first_trade_time > timedelta(days=30):
                return
                
        # 如果有持倉，檢查是否需要平倉
        if self.position != Position.NONE:
            if self.should_close_position(time, current_price, current_volume, past_24h_records, past_records):
                # 計算盈虧
                pnl = self.calculate_pnl(current_price)
                self.total_pnl += pnl
                
                # 更新資金
                self.capital += pnl
                
                # 記錄交易
                self.trades.append(Trade(
                    time=time,
                    price=current_price,
                    action="平倉",
                    position=self.position,
                    size=self.position_size,
                    pnl=pnl
                ))
                
                # 重置持倉相關變量
                self.position = Position.NONE
                self.position_size = 0.0
                self.entry_price = 0.0
                self.entry_time = None
                self.highest_price = 0.0
                self.lowest_price = float('inf')
                self.last_trade_time = current_time
                return

        # 如果沒有持倉，檢查是否要開倉
        else:
            # 檢查交易次數限制
            if not self.can_trade_today(time):
                return
                
            # 檢查是否已超過第一筆交易後的30天
            if self.first_trade_time is not None:
                if current_time - self.first_trade_time > timedelta(days=30):
                    return
                    
            # 計算15分钟价格变化
            price_change_15min = self.calculate_15min_price_change(current_price, past_records)
            
            # 計算交易量條件
            recent_volume_avg = self.calculate_recent_volume_average(past_records, 15)  # 計算最近15分鐘平均交易量
            h24_volume_avg = self.calculate_recent_volume_average(past_24h_records, 24)  # 計算24小時平均交易量
            
            # 避免除以零的情況
            volume_ratio = 0
            if h24_volume_avg > 0:
                volume_ratio = recent_volume_avg / h24_volume_avg  # 與24小時平均交易量比較
            
            # 开仓条件：过去15分钟上涨3%，且最近15分钟交易量是24小时平均的1.5倍以上
            if price_change_15min >= 0.03 and volume_ratio >= 1.2:  # 15分钟内上涨3%且交易量条件满足，做多
                # 更新每日交易次數
                self.update_daily_trades(time)
                
                # 計算倉位大小和止損點
                stop_loss = current_price * (1 - self.calculate_dynamic_stop_loss(current_price, time, past_records))
                position_size = self.calculate_position_size(current_price, stop_loss)
                
                # 檢查是否有足夠資金開倉
                position_value = position_size * current_price
                if position_value > self.capital:
                    return
                    
                # 記錄開倉信息
                self.position = Position.LONG
                self.position_size = position_size
                self.entry_price = current_price
                self.entry_time = current_time
                
                # 記錄交易
                self.trades.append(Trade(
                    time=time,
                    price=current_price,
                    action="開倉",
                    position=Position.LONG,
                    size=position_size,
                    pnl=0.0
                ))
                
                # 如果是第一筆交易，記錄時間
                if self.first_trade_time is None:
                    self.first_trade_time = current_time
                    
            elif price_change_15min <= -0.03 and volume_ratio >= 1.2:  # 15分钟内下跌3%且交易量条件满足，做空
                # 更新每日交易次數
                self.update_daily_trades(time)
                
                # 計算倉位大小和止損點
                stop_loss = current_price * (1 + self.calculate_dynamic_stop_loss(current_price, time, past_records))
                position_size = self.calculate_position_size(current_price, stop_loss)
                
                # 檢查是否有足夠資金開倉
                position_value = position_size * current_price
                if position_value > self.capital:
                    return
                    
                # 記錄開倉信息
                self.position = Position.SHORT
                self.position_size = position_size
                self.entry_price = current_price
                self.entry_time = current_time
                
                # 記錄交易
                self.trades.append(Trade(
                    time=time,
                    price=current_price,
                    action="開倉",
                    position=Position.SHORT,
                    size=position_size,
                    pnl=0.0
                ))

                # 如果是第一筆交易，記錄時間
                if self.first_trade_time is None:
                    self.first_trade_time = current_time

def main():
    # 連接數據庫
    db_conn = db('binance')
    
    # 獲取指定時間範圍的數據
    start_date = '2024-10-01'
    end_date = '2025-02-01'
    
    # 要分析的交易對
    # pairs = ['SHELLUSDT', 'GPSUSDT', 'IPUSDT', 'B3USDT', 'HEIUSDT', 'LAYERUSDT', 'TSTUSDT', 'BERAUSDT', 'VVVUSDT', 'PIPPINUSDT', 'VINEUSDT', 'ANIMEUSDT', 'VTHOUSDT', 'MELANIAUSDT', 'TRUMPUSDT', 'AVAAIUSDT', 'ARCUSDT', 'SOLVUSDT', 'SUSDT', 'PROMUSDT', 'DUSDT', 'SONICUSDT', 'SWARMSUSDT', 'ALCHUSDT', 'COOKIEUSDT', 'BIOUSDT', 'ZEREBROUSDT', 'AI16ZUSDT', 'GRIFFAINUSDT', 'DFUSDT', 'PHAUSDT', 'DEXEUSDT', 'HIVEUSDT', 'CGPTUSDT', 'KMNOUSDT', 'FARTCOINUSDT', 'AIXBTUSDT', 'USUALUSDT', 'LUMIAUSDT', 'PENGUUSDT', 'VANAUSDT', 'MOCAUSDT', 'VELODROMEUSDT', 'DEGOUSDT', 'AVAUSDT', 'MEUSDT', 'SPXUSDT', 'VIRTUALUSDT', 'KOMAUSDT', 'RAYSOLUSDT', 'MOVEUSDT', 'ACXUSDT', 'ORCAUSDT', 'AEROUSDT', 'KAIAUSDT', 'CHILLGUYUSDT', 'MORPHOUSDT', 'THEUSDT', '1000CHEEMSUSDT', '1000WHYUSDT', 'SLERFUSDT', 'SCRTUSDT', 'BANUSDT', 'AKTUSDT', 'DEGENUSDT', 'HIPPOUSDT', '1000XUSDT', 'ACTUSDT', 'PNUTUSDT', 'DRIFTUSDT', 'SWELLUSDT', 'GRASSUSDT', '1000000MOGUSDT', 'CETUSUSDT', 'COWUSDT', 'PONKEUSDT', 'TROYUSDT', 'SANTOSUSDT', 'SAFEUSDT', 'MOODENGUSDT', 'GOATUSDT', 'SCRUSDT', '1000CATUSDT', 'DIAUSDT', 'EIGENUSDT']
    pairs = ['MOCAUSDT']
    
    # 開啟輸出文件
    with open('out.txt', 'w', encoding='utf-8') as f:
        # 寫入標題
        f.write("\n交易模擬結果匯總：\n")
        f.write("=" * 100 + "\n")
        f.write(f"{'交易對':<12} {'總交易次數':>10} {'總盈虧':>12} {'最終資金':>12} {'收益率':>10} {'勝率':>10} {'平均盈虧':>12}\n")
        f.write("-" * 100 + "\n")
        
        for pair in pairs:
            # 查詢數據
            data = db_conn.queryBinanceKlines(pair, start_date, end_date)
            records = json.loads(data)
            
            # 檢查數據結構
            if records:
                print("數據結構示例：")
                print(json.dumps(records[0], indent=2, ensure_ascii=False))
                
            # 將數據按時間排序
            sorted_records = sorted(records, key=lambda x: x['time'])
            
            # 創建交易模擬器
            simulator = TradingSimulator()
            
            # 模擬交易
            for i, current in enumerate(sorted_records):
                current_time = current['time']
                current_price = float(current['end_price'])
                current_volume = float(current['volume'])
                current_dt = simulator.parse_time(current_time)
                
                # 獲取前24小時的記錄（包括當前K線）
                past_24h_records = []
                for j in range(i, -1, -1):  # 從當前位置向前搜索
                    record = sorted_records[j]
                    record_dt = simulator.parse_time(record['time'])
                    if current_dt - record_dt > timedelta(hours=24):
                        break
                    past_24h_records.insert(0, record)  # 保持時間順序
                
                # 獲取用於趨勢分析的記錄（保持原有邏輯）
                past_records = sorted_records[:i]
                
                # 處理當前價格
                simulator.process_price(current_time, current_price, current_volume, past_24h_records, past_records)
            
            # 計算統計數據
            total_trades = len(simulator.trades)
            profitable_trades = len([t for t in simulator.trades if t.pnl > 0])
            win_rate = profitable_trades / total_trades * 100 if total_trades > 0 else 0
            avg_pnl = simulator.total_pnl / total_trades if total_trades > 0 else 0
            
            # 寫入交易統計
            f.write(f"{pair:<12} {total_trades:>10} {simulator.total_pnl:>12.2f} {simulator.capital:>12.2f} "
                   f"{(simulator.capital - 10000) / 100:>9.2f}% {win_rate:>9.2f}% {avg_pnl:>11.2f}\n")
            
            # 寫入詳細交易記錄
            f.write(f"\n{pair} 詳細交易記錄：\n")
            f.write("-" * 100 + "\n")
            f.write(f"總交易次數: {total_trades}\n")
            f.write(f"盈利交易數: {profitable_trades}\n")
            f.write(f"勝率: {win_rate:.2f}%\n")
            f.write(f"平均每筆盈虧: {avg_pnl:.2f}\n")
            f.write(f"最終資金: {simulator.capital:.2f}\n")
            f.write(f"總收益率: {(simulator.capital - 10000) / 100:.2f}%\n\n")
            
            # 寫入所有交易
            f.write("交易記錄：\n")
            f.write("-" * 100 + "\n")
            for trade in simulator.trades:
                f.write(f"時間: {trade.time:<25} | 價格: {trade.price:>8.4f} | "
                       f"操作: {trade.action:<4} | 倉位: {trade.position.value:<4} | "
                       f"倉位大小: {trade.size:>10.4f} | 當次盈虧: {trade.pnl:>10.4f}\n")
            
            f.write("\n" + "=" * 100 + "\n\n")
        
        f.write("\n完成時間: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    
    print("交易結果已輸出到 out.txt")

if __name__ == "__main__":
    main()