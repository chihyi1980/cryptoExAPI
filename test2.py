from db.db_orm import db
from datetime import datetime, timedelta
import pandas as pd
import json
from typing import List, Dict, Tuple

def calculate_24h_price_change(klines_data: str) -> List[Tuple[str, float]]:
    """計算每個24小時窗口的價格變化百分比"""
    if not klines_data:
        return []
    
    # 解析JSON數據
    klines = json.loads(klines_data)
    if not klines:
        return []
    
    # 將數據轉換為DataFrame
    df = pd.DataFrame(klines)
    df['trade_time'] = pd.to_datetime(df['time'])
    df['price'] = df['end_price'].astype(float)
    df = df.sort_values('trade_time')
    
    # 初始化結果列表
    price_changes = []
    
    # 對每個時間點
    for i in range(len(df)):
        current_time = df.iloc[i]['trade_time']
        current_price = df.iloc[i]['price']
        
        # 找出24小時前的價格點
        time_24h_ago = current_time - timedelta(hours=24)
        prev_price_data = df[df['trade_time'] >= time_24h_ago][df['trade_time'] < current_time]
        
        if not prev_price_data.empty:
            prev_price = prev_price_data.iloc[0]['price']
            price_change = (current_price - prev_price) / prev_price * 100
            price_changes.append((df.iloc[i]['time'], price_change))
    
    return price_changes

def analyze_price_changes():
    """分析所有交易對的價格變化"""
    # 創建數據庫實例
    db_instance = db('binance')
    
    try:
        # 獲取所有交易對
        pairs = json.loads(db_instance.queryBinanceKlinesPairList())
        
        # 設定時間範圍
        start_date = datetime(2024, 10, 1)
        end_date = datetime(2025, 1, 1)
        
        # 存儲每個交易對的最大漲跌幅
        volatility_data = []
        
        print(f"開始分析 {len(pairs)} 個交易對的價格變化...")
        
        for pair in pairs:
            # 查詢該交易對的K線數據
            klines = db_instance.queryBinanceKlines(pair, start_date, end_date)
            
            if klines:
                # 計算24小時價格變化
                price_changes = calculate_24h_price_change(klines)
                
                if price_changes:
                    # 找出最大漲幅和最大跌幅
                    max_increase = max(price_changes, key=lambda x: x[1])
                    max_decrease = min(price_changes, key=lambda x: x[1])
                    
                    volatility_data.append({
                        'pair': pair,
                        'max_increase': max_increase[1],
                        'max_increase_time': max_increase[0],
                        'max_decrease': max_decrease[1],
                        'max_decrease_time': max_decrease[0],
                        'abs_max_change': max(abs(max_increase[1]), abs(max_decrease[1]))
                    })
                    
                    print(f"已分析 {pair}")
        
        # 將數據轉換為DataFrame並按絕對變化幅度排序
        df_result = pd.DataFrame(volatility_data)
        df_result = df_result.sort_values('abs_max_change', ascending=False)
        
        # 輸出前20名
        print("\n24小時價格變化最大的前20個交易對：")
        print("=" * 120)
        print(f"{'交易對':<15} {'最大漲幅%':>10} {'漲幅時間':>25} {'最大跌幅%':>10} {'跌幅時間':>25}")
        print("-" * 120)
        
        for _, row in df_result.head(20).iterrows():
            print(f"{row['pair']:<15} {row['max_increase']:>10.2f} {row['max_increase_time']:>25} {row['max_decrease']:>10.2f} {row['max_decrease_time']:>25}")
    
    finally:
        db_instance.closeDBConn()

if __name__ == "__main__":
    analyze_price_changes()
