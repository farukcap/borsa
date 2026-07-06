import os
import requests
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Binance'den Mum Verisi Çekme Fonksiyonu
def get_binance_klines(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        # Sayısal değerlere dönüştürme
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df
    except Exception as e:
        return None

# Matematiksel Formasyon Analiz Motoru
def analyze_patterns(df, confirm_bars=3):
    results = []
    if df is None or len(df) < 20:
        return results

    # Mum özelliklerini hesapla
    df['body'] = (df['close'] - df['open']).abs()
    df['direction'] = np.where(df['close'] >= df['open'], 'white', 'black')
    df['high_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['low_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['total_range'] = df['high'] - df['low']
    df['is_doji'] = df['body'] <= (df['total_range'] * 0.1)

    # Trend bulma (Basit hareketli ortalama üstü/altı)
    df['ma20'] = df['close'].rolling(20).mean()

    # Son mumları incele (En son tamamlanan mum endeksi: i)
    # Son mum henüz kapanmadığı için i = len(df) - 1 - confirm_bars noktasından formasyon arayıp sonraki barları kontrol edeceğiz
    for i in range(15, len(df) - confirm_bars):
        pattern_name = None
        pattern_type = None  # Bullish / Bearish
        trigger_idx = i
        
        # O anki mumlar
        c1 = df.iloc[i]     # Formasyonun ana veya son mumu
        p1 = df.iloc[i-1]   # Bir önceki mum
        
        # 1. BULLISH HAMMER (Çekiç Boğa) - [Doküman Sayfa 6]
        if c1['low_shadow'] > (c1['body'] * 2) and c1['high_shadow'] < (c1['body'] * 0.5) and c1['close'] < c1['ma20']:
            pattern_name = "Bullish Hammer (Çekiç Boğa)"
            pattern_type = "Bullish"
            [span_6](start_span)target_level = max(c1['open'], c1['close']) # Teyit: Gövde üst sınırı[span_6](end_span)
            [span_7](start_span)stop_level = c1['low'] # Stop: En düşük seviye[span_7](end_span)

        # 2. BEARISH HANGING MAN (Asılı Adam Ayı) - [Doküman Sayfa 16]
        elif c1['low_shadow'] > (c1['body'] * 2) and c1['high_shadow'] < (c1['body'] * 0.5) and c1['close'] > c1['ma20']:
            pattern_name = "Bearish Hanging Man (Asılı Adam Ayı)"
            pattern_type = "Bearish"
            [span_8](start_span)target_level = c1['low'] - (c1['low_shadow'] / 2) # Teyit: Alt gölge orta noktası[span_8](end_span)
            [span_9](start_span)stop_level = max(p1['high'], c1['high']) # Stop: Son iki barın en yükseği[span_9](end_span)

        # 3. BULLISH ENGULFING (Yutan Boğa) - [Doküman Sayfa 6]
        elif p1['direction'] == 'black' and c1['direction'] == 'white' and c1['open'] <= p1['close'] and c1['close'] > p1['open']:
            pattern_name = "Bullish Engulfing (Yutan Boğa)"
            pattern_type = "Bullish"
            [span_10](start_span)target_level = c1['close'] # Teyit: Son bar kapanışı[span_10](end_span)
            [span_11](start_span)stop_level = c1['low'] # Stop: Son barın en düşüğü[span_11](end_span)

        # 4. BEARISH ENGULFING (Yutan Ayı) - [Doküman Sayfa 17]
        elif p1['direction'] == 'white' and c1['direction'] == 'black' and c1['open'] >= p1['close'] and c1['close'] < p1['open']:
            pattern_name = "Bearish Engulfing (Yutan Ayı)"
            pattern_type = "Bearish"
            [span_12](start_span)target_level = c1['close'] # Teyit: Son bar kapanışı[span_12](end_span)
            [span_13](start_span)stop_level = c1['high'] # Stop: Son barın en yükseği[span_13](end_span)

        # 5. BULLISH HARAMI (Hamile Boğa) - [Doküman Sayfa 7]
        elif p1['direction'] == 'black' and c1['direction'] == 'white' and c1['open'] > p1['close'] and c1['close'] < p1['open'] and c1['body'] < p1['body']:
            pattern_name = "Bullish Harami (Hamile Boğa)"
            pattern_type = "Bullish"
            p1_mid = p1['close'] + (p1['body'] / 2)
            [span_14](start_span)target_level = max(c1['close'], p1_mid) # Teyit algoritması[span_14](end_span)
            [span_15](start_span)stop_level = min(p1['low'], c1['low']) # Stop algoritması[span_15](end_span)

        # [span_16](start_span)Eğer bir formasyon tespit edildiyse, durumunu (Life Cycle) kontrol et[span_16](end_span)
        if pattern_name:
            [span_17](start_span)status = "Not Confirmed" # Varsayılan[span_17](end_span)
            confirmed_at_bar = None
            
            # [span_18](start_span)Sonraki barları tara (Confirm Bar Count mantığı)[span_18](end_span)
            for check_idx in range(trigger_idx + 1, trigger_idx + 1 + confirm_bars):
                if check_idx >= len(df):
                    break
                future_bar = df.iloc[check_idx]
                
                if pattern_type == "Bullish":
                    # [span_19](start_span)Boğa için: Kapanış teyit seviyesini yukarı kırmalı[span_19](end_span)
                    if status == "Not Confirmed" and future_bar['close'] > target_level:
                        [span_20](start_span)status = "Confirmed"[span_20](end_span)
                        confirmed_at_bar = check_idx
                    # [span_21](start_span)Onaylandıktan sonra stop patladı mı?[span_21](end_span)
                    if status == "Confirmed" and future_bar['close'] < stop_level:
                        [span_22](start_span)status = "Confirmed & Fail"[span_22](end_span)
                        break
                        
                elif pattern_type == "Bearish":
                    # [span_23](start_span)Ayı için: Kapanış teyit seviyesini aşağı kırmalı[span_23](end_span)
                    if status == "Not Confirmed" and future_bar['close'] < target_level:
                        status = "Confirmed"
                        confirmed_at_bar = check_idx
                    # Onaylandıktan sonra stop patladı mı?
                    if status == "Confirmed" and future_bar['close'] > stop_level:
                        status = "Confirmed & Fail"
                        break

            # Sadece listelenebilir anlamlı durumları ekle (Web arayüzü kalabalık olmasın diye en son durumları alıyoruz)
            results.append({
                "pattern": pattern_name,
                "type": pattern_type,
                "time": pd.to_datetime(c1['open_time'], unit='ms').strftime('%Y-%m-%d %H:%M'),
                "status": status,
                "trigger_price": c1['close']
            })

    # Son tespit edilenleri ters kronolojik sırada gönder
    return results[::-1][:10]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', pd_methods=['POST'])
def scan():
    req_data = request.get_json()
    symbol = req_data.get('symbol', 'BTCUSDT')
    interval = req_data.get('interval', '15m')
    
    df = get_binance_klines(symbol, interval, limit=150)
    if df is None:
        return jsonify({"success": False, "message": "Veri çekilemedi. Sembolü kontrol edin."})
        
    analysis = analyze_patterns(df)
    
    # Projeksiyon yorumu (1-2 Günlük tahmin metni oluşturma)
    projection = "Yeterli formasyon onayı bulunmuyor. Yatay seyir beklenebilir."
    if analysis:
        latest = analysis[0]
        if latest['status'] == "Confirmed":
            if latest['type'] == "Bullish":
                projection = f"Son doğrulanan {latest['pattern']} formasyonuna göre önümüzdeki 1-2 gün boyunca YUKARI yönlü hareket olasılığı yüksektir."
            else:
                projection = f"Son doğrulanan {latest['pattern']} formasyonuna göre önümüzdeki 1-2 gün boyunca AŞAĞI yönlü baskı olasılığı yüksektir."
        elif latest['status'] == "Confirmed & Fail":
            projection = "Son formasyon onaylandıktan sonra başarısızlığa (Stop-loss) uğramış. [span_24](start_span)Piyasa yön değiştirebilir."[span_24](end_span)

    return jsonify({
        "success": True,
        "symbol": symbol.upper(),
        "interval": interval,
        "patterns": analysis,
        "projection": projection
    })

if __name__ == '__main__':
    app.run(debug=True)
