import os
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def get_binance_klines(symbol, interval, limit=150):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        return df
    except Exception:
        return None

def analyze_patterns_pure_math(df, confirm_bar_count=3):
    results = []
    if df is None or len(df) < 30:
        return results

    # --- SAF MATEMATİKSEL MUMPİKSEL ÖZELLİKLER ---
    # Gövde Boyutları, Yönleri ve Gölgeler
    df['body'] = (df['close'] - df['open']).abs()
    df['dir'] = 'white'
    df.loc[df['close'] < df['open'], 'dir'] = 'black'
    
    df['high_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['low_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['total_range'] = df['high'] - df['low']
    
    # Doji Tanımı: Gövde toplam hareketin %10'undan küçükse
    df['is_doji'] = df['body'] <= (df['total_range'] * 0.1)
    
    # Trend Tespiti (Saf Matematik: Son 20 mumun aritmetik ortalaması)
    df['ma20'] = df['close'].rolling(20).mean()

    # Formasyon Tarama Döngüsü
    # i: Formasyonun bittiği / sinyalin üretildiği mumun endeksi
    for i in range(5, len(df) - confirm_bar_count):
        p2 = df.iloc[i-2] # İki önceki mum
        p1 = df.iloc[i-1] # Bir önceki mum
        c  = df.iloc[i]   # Mevcut mum (Sinyal mumu)
        
        pattern_name = None
        pattern_type = None # 'Bullish' veya 'Bearish'
        target_level = 0.0
        stop_level = 0.0

        # --- 1. BULLISH HAMMER (Çekiç Boğa) [Sayfa 6] ---
        # Koşul: Düşüş trendinde, alt gölge gövdenin en az 2 katı, üst gölge çok küçük [Sayfa 16, 17].
        if c['close'] < c['ma20'] and c['low_shadow'] >= (c['body'] * 2) and c['high_shadow'] <= (c['body'] * 0.5):
            pattern_name = "Bullish Hammer (Çekiç Boğa)"
            pattern_type = "Bullish"
            target_level = max(c['open'], c['close']) # Teyit: Gövde üst sınırı [Sayfa 18]
            stop_level = c['low'] # Stop: Barın gördüğü en düşük [Sayfa 18]

        # --- 2. BULLISH BELT HOLD (Belden Tutma Boğa) [Sayfa 6] ---
        # Koşul: Açılış en düşük değere eşit (veya çok yakın), var olan düşüş trendine karşı güçlü yükseliş [Sayfa 19, 20].
        elif c['close'] < c['ma20'] and c['dir'] == 'white' and c['low_shadow'] <= (c['body'] * 0.05) and c['high_shadow'] <= (c['body'] * 0.2):
            pattern_name = "Bullish Belt Hold (Belden Tutma Boğa)"
            pattern_type = "Bullish"
            target_level = c['close'] # Teyit: Barın kapanış fiyatı [Sayfa 20]
            stop_level = c['low'] # Stop: Barın gördüğü en düşük [Sayfa 21]

        # --- 3. BULLISH ENGULFING (Yutan Boğa) [Sayfa 6] ---
        # Koşul: Önceki siyah gövdeyi tamamen içine alan büyük beyaz gövde [Sayfa 22].
        elif p1['dir'] == 'black' and c['dir'] == 'white' and c['open'] <= p1['close'] and c['close'] > p1['open']:
            pattern_name = "Bullish Engulfing (Yutan Boğa)"
            pattern_type = "Bullish"
            target_level = c['close'] # Teyit: Son barın kapanış fiyatı [Sayfa 23]
            stop_level = c['low'] # Stop: Son barın gördüğü en düşük [Sayfa 23]

        # --- 4. BULLISH HARAMI (Hamile Boğa) [Sayfa 7] ---
        # Koşul: Siyah gövdenin tamamen içinde kalan küçük beyaz gövde [Sayfa 24].
        elif p1['dir'] == 'black' and c['dir'] == 'white' and c['open'] > p1['close'] and c['close'] < p1['open'] and c['body'] < p1['body']:
            pattern_name = "Bullish Harami (Hamile Boğa)"
            pattern_type = "Bullish"
            p1_mid = p1['close'] + ((p1['open'] - p1['close']) / 2)
            target_level = max(c['close'], p1_mid) # Teyit: İkinci kapanış ile ilk gövde orta noktasından büyük olanı [Sayfa 25]
            stop_level = min(p1['low'], c['low']) # Stop: İki barın düşük değerlerinden daha düşük olanı [Sayfa 26]

        # --- 5. BEARISH HANGING MAN (Asılı Adam Ayı) [Sayfa 16] ---
        # Koşul: Yükseliş trendinde, üstte küçük gövde, altta uzun gölge [Sayfa 79].
        elif c['close'] > c['ma20'] and c['low_shadow'] >= (c['body'] * 2) and c['high_shadow'] <= (c['body'] * 0.5):
            pattern_name = "Bearish Hanging Man (Asılı Adam Ayı)"
            pattern_type = "Bearish"
            target_level = c['low'] + (c['low_shadow'] / 2) # Teyit: Asılı adamın alt gölgesinin orta noktası [Sayfa 80]
            stop_level = max(p1['high'], c['high']) # Stop: Son iki barın yüksek değerlerinden büyük olanı [Sayfa 80]

        # --- 6. BEARISH BELT HOLD (Belden Tutma Ayı) [Sayfa 16] ---
        # Koşul: Açılış değeri en yüksek seviye, trende ters sert düşüş mumu [Sayfa 81].
        elif c['close'] > c['ma20'] and c['dir'] == 'black' and c['high_shadow'] <= (c['body'] * 0.05):
            pattern_name = "Bearish Belt Hold (Belden Tutma Ayı)"
            pattern_type = "Bearish"
            target_level = c['close'] # Teyit: Barın kapanış fiyatı [Sayfa 83]
            stop_level = c['high'] # Stop: Barın gördüğü en yüksek fiyat [Sayfa 83]

        # --- 7. BEARISH ENGULFING (Yutan Ayı) [Sayfa 17] ---
        # Koşul: Beyaz gövdeyi tamamen yutan büyük siyah gövde [Sayfa 85].
        elif p1['dir'] == 'white' and c['dir'] == 'black' and c['open'] >= p1['close'] and c['close'] < p1['open']:
            pattern_name = "Bearish Engulfing (Yutan Ayı)"
            pattern_type = "Bearish"
            target_level = c['close'] # Teyit: Son barın kapanış fiyatı [Sayfa 86]
            stop_level = c['high'] # Stop: Son barın gördüğü en yüksek [Sayfa 86]

        # --- 8. BEARISH HARAMI (Hamile Ayı) [Sayfa 17] ---
        # Koşul: Beyaz gövdenin içinde kalan küçük siyah gövde [Sayfa 87].
        elif p1['dir'] == 'white' and c['dir'] == 'black' and c['open'] < p1['close'] and c['close'] > p1['open'] and c['body'] < p1['body']:
            pattern_name = "Bearish Harami (Hamile Ayı)"
            pattern_type = "Bearish"
            p1_mid = p1['open'] + ((p1['close'] - p1['open']) / 2)
            target_level = min(c['close'], p1_mid) # Teyit: İkinci kapanış ile ilk gövde orta noktasından düşük olanı [Sayfa 88]
            stop_level = max(p1['high'], c['high']) # Stop: İki barın yükseklerinden daha yüksek olanı [Sayfa 89]

        # --- 9. BEARISH SHOOTING STAR (Kayan Yıldız Ayı) [Sayfa 18] ---
        # Koşul: Uzun üst gölge, altta küçük gövde [Sayfa 96].
        elif c['close'] > c['ma20'] and c['high_shadow'] >= (c['body'] * 2) and c['low_shadow'] <= (c['body'] * 0.5):
            pattern_name = "Bearish Shooting Star (Kayan Yıldız Ayı)"
            pattern_type = "Bearish"
            target_level = min(c['open'], c['close']) # Teyit: Ters çekiç gövdesinin alt çizgisi [Sayfa 97]
            stop_level = c['high'] # Stop: Son barın gördüğü en yüksek [Sayfa 97]

        # --- MATRIKS YAŞAM DÖNGÜSÜ KONTROLÜ (CONFIRM BAR COUNT) --- [Sayfa 119 - 124]
        if pattern_name:
            status = "Not Confirmed" # Başlangıç durumu [Sayfa 124]
            
            # Belirlenen periyot kadar ileriye bakılarak teyit/stop durum kontrolü [Sayfa 123]
            for next_idx in range(i + 1, i + 1 + confirm_bar_count):
                if next_idx >= len(df):
                    break
                future_mum = df.iloc[next_idx]
                
                if pattern_type == "Bullish":
                    # Kapanış değeri teyit seviyesini yukarı aşmalı [Sayfa 124, 130]
                    if status == "Not Confirmed" and future_mum['close'] > target_level:
                        status = "Confirmed"
                    # Önce teyit alıp sonra stop seviyesinin altına sarkarsa [Sayfa 134]
                    if status == "Confirmed" and future_mum['close'] < stop_level:
                        status = "Confirmed & Fail"
                        break
                        
                elif pattern_type == "Bearish":
                    # Kapanış değeri teyit seviyesini aşağı kırmalı [Sayfa 124]
                    if status == "Not Confirmed" and future_mum['close'] < target_level:
                        status = "Confirmed"
                    # Önce teyit alıp sonra stop seviyesinin üzerine taşarsa
                    if status == "Confirmed" and future_mum['close'] > stop_level:
                        status = "Confirmed & Fail"
                        break

            results.append({
                "time": pd.to_datetime(c['open_time'], unit='ms').strftime('%Y-%m-%d %H:%M'),
                "pattern": pattern_name,
                "type": pattern_type,
                "trigger_price": c['close'],
                "status": status
            })

    # Son tespit edilenleri en yeni üste gelecek şekilde sırala
    return results[::-1][:10]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan():
    req_data = request.get_json() or {}
    symbol = req_data.get('symbol', 'BTCUSDT')
    interval = req_data.get('interval', '4h')
    
    df = get_binance_klines(symbol, interval, limit=150)
    if df is None:
        return jsonify({"success": False, "message": "Binance veri bağlantı hatası."})
        
    analysis = analyze_patterns_pure_math(df, confirm_bar_count=3)
    
    projection = "Aktif sinyal doğrulaması yok. Yatay konsolidasyon beklenebilir."
    if analysis:
        latest = analysis[0]
        if latest['status'] == "Confirmed":
            direction_str = "YUKARI (Yükseliş)" if latest['type'] == "Bullish" else "AŞAĞI (Düşüş)"
            projection = f"Son doğrulanan '{latest['pattern']}' yapısı gereği, önümüzdeki 1-2 gün boyunca fiyatın {direction_str} yönlü ilerlemesi matematiksel olarak desteklenmektedir."
        elif latest['status'] == "Confirmed & Fail":
            projection = f"Son tespit edilen {latest['pattern']} yapısı teyit edilmesine rağmen stop seviyesini ihlal ederek başarısız (Fail) olmuştur. Güçlü ters trend oluşabilir."

    return jsonify({
        "success": True,
        "symbol": symbol.upper(),
        "interval": interval,
        "patterns": analysis,
        "projection": projection
    })

if __name__ == '__main__':
    app.run(debug=True)
