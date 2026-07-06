import os
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify

# Vercel Serverless mimarisi için templates klasörünün yerini kesinleştiriyoruz
current_dir = os.path.dirname(__file__)
template_dir = os.path.abspath(os.path.join(current_dir, '..', 'templates'))

app = Flask(__name__, template_folder=template_dir)

def get_binance_live_klines(symbol, interval, limit=200):
    sym = symbol.upper().strip()
    # Kullanıcı sadece 'btc' veya 'eth' yazarsa sonuna otomatik USDT ekle
    if not sym.endswith("USDT") and not sym.endswith("BTC") and not sym.endswith("TRY") and not sym.endswith("BUSD"):
        sym = f"{sym}USDT"
        
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": sym, "interval": interval, "limit": limit}
    
    try:
        # Sunucu tabanlı engellemeleri aşmak için timeout ve standart tarayıcı header'ı ekledik
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, params=params, headers=headers, timeout=7)
        
        if response.status_code != 200:
            return None, sym
            
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
            
        return df, sym
    except Exception:
        return None, sym

def process_matriks_math_rules(df, confirm_bar_count=3):
    results = []
    if df is None or len(df) < 35:
        return results

    # -[span_0](start_span)-- PDF'TEKİ GEOMETRİK ORANLARIN SAF MATEMATİKSEL İZDÜŞÜMÜ ---[span_0](end_span)
    df['body'] = (df['close'] - df['open']).abs()
    df['dir'] = 'white'
    df.loc[df['close'] < df['open'], 'dir'] = 'black'
    
    df['high_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['low_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['total_range'] = df['high'] - df['low']
    
    # [span_1](start_span)[span_2](start_span)Doji Filtresi: Gövde boyutu toplam aralığın %10'u veya altındaysa[span_1](end_span)[span_2](end_span)
    df['is_doji'] = df['body'] <= (df['total_range'] * 0.1)
    
    # Matriks Trend Algoritması: 20 periyotluk Basit Hareketli Ortalama
    df['ma20'] = df['close'].rolling(20).mean()

    # [span_3](start_span)[span_4](start_span)Formasyon tarama döngüsü (En son mumlardaki teyit durumlarını kaçırmamak için koruma payı ile)[span_3](end_span)[span_4](end_span)
    for i in range(5, len(df) - confirm_bar_count):
        p3 = df.iloc[i-3]
        p2 = df.iloc[i-2]
        p1 = df.iloc[i-1]
        [span_5](start_span)c  = df.iloc[i]   # Formasyonun tetiklendiği sinyal mumu[span_5](end_span)
        
        pattern_name = None
        pattern_type = None 
        target_level = 0.0
        stop_level = 0.0

        # ----------------------------------------------------
        # [span_6](start_span)BULLISH (YÜKSELİŞ) FORMASYONLARI - [Sayfa 5, 6, 7, 8, 12][span_6](end_span)
        # ----------------------------------------------------
        
        # 1. [span_7](start_span)[span_8](start_span)Bullish Hammer (Çekiç Boğa) - [Sayfa 6, 16][span_7](end_span)[span_8](end_span)
        if c['close'] < c['ma20'] and c['low_shadow'] >= (c['body'] * 2) and c['high_shadow'] <= (c['body'] * 0.5):
            [span_9](start_span)[span_10](start_span)pattern_name = "Bullish Hammer (Çekiç Boğa)"[span_9](end_span)[span_10](end_span)
            [span_11](start_span)[span_12](start_span)pattern_type = "Bullish"[span_11](end_span)[span_12](end_span)
            [span_13](start_span)target_level = max(c['open'], c['close']) # Teyit: Gövde üst sınırı[span_13](end_span)
            [span_14](start_span)stop_level = c['low'] # Stop: En düşük fiyat seviyesi[span_14](end_span)

        # 2. [span_15](start_span)[span_16](start_span)Bullish Belt Hold (Belden Tutma Boğa) - [Sayfa 6, 19][span_15](end_span)[span_16](end_span)
        elif c['close'] < c['ma20'] and c['dir'] == 'white' and c['low_shadow'] <= (c['body'] * 0.05) and c['high_shadow'] <= (c['body'] * 0.3):
            [span_17](start_span)[span_18](start_span)pattern_name = "Bullish Belt Hold (Belden Tutma Boğa)"[span_17](end_span)[span_18](end_span)
            [span_19](start_span)[span_20](start_span)pattern_type = "Bullish"[span_19](end_span)[span_20](end_span)
            [span_21](start_span)target_level = c['close'] # Teyit: Barın kapanış fiyatı[span_21](end_span)
            [span_22](start_span)stop_level = c['low'] # Stop: Barın gördüğü en düşük seviye[span_22](end_span)

        # 3. [span_23](start_span)[span_24](start_span)Bullish Engulfing (Yutan Boğa) - [Sayfa 6, 22][span_23](end_span)[span_24](end_span)
        elif p1['dir'] == 'black' and c['dir'] == 'white' and c['open'] <= p1['close'] and c['close'] > p1['open']:
            [span_25](start_span)[span_26](start_span)pattern_name = "Bullish Engulfing (Yutan Boğa)"[span_25](end_span)[span_26](end_span)
            [span_27](start_span)[span_28](start_span)pattern_type = "Bullish"[span_27](end_span)[span_28](end_span)
            [span_29](start_span)target_level = c['close'] # Teyit: Son barın kapanışı[span_29](end_span)
            [span_30](start_span)stop_level = min(p1['low'], c['low']) # Stop: Görülen en düşük fiyat seviyesi[span_30](end_span)

        # 4. [span_31](start_span)[span_32](start_span)Bullish Harami (Hamile Boğa) - [Sayfa 7, 24][span_31](end_span)[span_32](end_span)
        elif p1['dir'] == 'black' and c['dir'] == 'white' and c['open'] > p1['close'] and c['close'] < p1['open'] and c['body'] < p1['body']:
            [span_33](start_span)[span_34](start_span)pattern_name = "Bullish Harami (Hamile Boğa)"[span_33](end_span)[span_34](end_span)
            [span_35](start_span)[span_36](start_span)pattern_type = "Bullish"[span_35](end_span)[span_36](end_span)
            p1_mid = p1['close'] + (p1['body'] / 2)
            [span_37](start_span)target_level = max(c['close'], p1_mid) # Teyit mekanizması[span_37](end_span)
            [span_38](start_span)stop_level = min(p1['low'], c['low']) # Stop mekanizması[span_38](end_span)

        # 5. [span_39](start_span)[span_40](start_span)Bullish Piercing Line (Delen Mumlar Boğa) - [Sayfa 8, 35][span_39](end_span)[span_40](end_span)
        elif p1['dir'] == 'black' and c['dir'] == 'white' and c['open'] < p1['low'] and c['close'] >= (p1['close'] + (p1['body'] * 0.5)) and c['close'] < p1['open']:
            [span_41](start_span)[span_42](start_span)pattern_name = "Bullish Piercing Line (Delen Mumlar Boğa)"[span_41](end_span)[span_42](end_span)
            [span_43](start_span)[span_44](start_span)pattern_type = "Bullish"[span_43](end_span)[span_44](end_span)
            [span_45](start_span)target_level = c['close'][span_45](end_span)
            [span_46](start_span)stop_level = c['low'][span_46](end_span)

        # 6. [span_47](start_span)[span_48](start_span)Bullish Morning Star (Sabah Yıldızı Boğa) - [Sayfa 12, 54][span_47](end_span)[span_48](end_span)
        elif p2['dir'] == 'black' and p1['body'] < p2['body'] and c['dir'] == 'white' and c['close'] > (p2['close'] + (p2['body'] * 0.5)):
            [span_49](start_span)[span_50](start_span)pattern_name = "Bullish Morning Star (Sabah Yıldızı Boğa)"[span_49](end_span)[span_50](end_span)
            [span_51](start_span)[span_52](start_span)pattern_type = "Bullish"[span_51](end_span)[span_52](end_span)
            [span_53](start_span)target_level = c['close'][span_53](end_span)
            [span_54](start_span)stop_level = min(p2['low'], p1['low'], c['low'])[span_54](end_span)

        # 7. [span_55](start_span)[span_56](start_span)Bullish Matching Low (Çakışan Dip Boğa) - [Sayfa 10, 46][span_55](end_span)[span_56](end_span)
        elif p1['dir'] == 'black' and c['dir'] == 'black' and abs(c['close'] - p1['close']) <= (c['close'] * 0.001):
            [span_57](start_span)[span_58](start_span)pattern_name = "Bullish Matching Low (Çakışan Dip Boğa)"[span_57](end_span)[span_58](end_span)
            [span_59](start_span)[span_60](start_span)pattern_type = "Bullish"[span_59](end_span)[span_60](end_span)
            [span_61](start_span)target_level = p1['close'] + (p1['body'] / 2)[span_61](end_span)
            [span_62](start_span)stop_level = min(p1['low'], c['low'])[span_62](end_span)

        # ----------------------------------------------------
        # [span_63](start_span)[span_64](start_span)BEARISH (DÜŞÜŞ) FORMASYONLARI - [Sayfa 5, 6, 16, 17, 18, 19][span_63](end_span)[span_64](end_span)
        # ----------------------------------------------------
        
        # 8. [span_65](start_span)[span_66](start_span)Bearish Hanging Man (Asılı Adam Ayı) - [Sayfa 16, 79][span_65](end_span)[span_66](end_span)
        elif c['close'] > c['ma20'] and c['low_shadow'] >= (c['body'] * 2) and c['high_shadow'] <= (c['body'] * 0.5):
            [span_67](start_span)[span_68](start_span)pattern_name = "Bearish Hanging Man (Asılı Adam Ayı)"[span_67](end_span)[span_68](end_span)
            [span_69](start_span)[span_70](start_span)pattern_type = "Bearish"[span_69](end_span)[span_70](end_span)
            [span_71](start_span)target_level = c['low'] + (c['low_shadow'] / 2)[span_71](end_span)
            [span_72](start_span)stop_level = max(p1['high'], c['high'])[span_72](end_span)

        # 9. [span_73](start_span)[span_74](start_span)Bearish Belt Hold (Belden Tutma Ayı) - [Sayfa 16, 81][span_73](end_span)[span_74](end_span)
        elif c['close'] > c['ma20'] and c['dir'] == 'black' and c['high_shadow'] <= (c['body'] * 0.05):
            [span_75](start_span)[span_76](start_span)pattern_name = "Bearish Belt Hold (Belden Tutma Ayı)"[span_75](end_span)[span_76](end_span)
            [span_77](start_span)[span_78](start_span)pattern_type = "Bearish"[span_77](end_span)[span_78](end_span)
            [span_79](start_span)target_level = c['close'][span_79](end_span)
            [span_80](start_span)stop_level = c['high'][span_80](end_span)

        # 10. [span_81](start_span)[span_82](start_span)Bearish Engulfing (Yutan Ayı) - [Sayfa 17, 85][span_81](end_span)[span_82](end_span)
        elif p1['dir'] == 'white' and c['dir'] == 'black' and c['open'] >= p1['close'] and c['close'] < p1['open']:
            [span_83](start_span)[span_84](start_span)pattern_name = "Bearish Engulfing (Yutan Ayı)"[span_83](end_span)[span_84](end_span)
            [span_85](start_span)[span_86](start_span)pattern_type = "Bearish"[span_85](end_span)[span_86](end_span)
            [span_87](start_span)target_level = c['close'][span_87](end_span)
            [span_88](start_span)stop_level = max(p1['high'], c['high'])[span_88](end_span)

        # 11. [span_89](start_span)[span_90](start_span)Bearish Harami (Hamile Ayı) - [Sayfa 17, 87][span_89](end_span)[span_90](end_span)
        elif p1['dir'] == 'white' and c['dir'] == 'black' and c['open'] < p1['close'] and c['close'] > p1['open'] and c['body'] < p1['body']:
            [span_91](start_span)[span_92](start_span)pattern_name = "Bearish Harami (Hamile Ayı)"[span_91](end_span)[span_92](end_span)
            [span_93](start_span)[span_94](start_span)pattern_type = "Bearish"[span_93](end_span)[span_94](end_span)
            p1_mid = p1['open'] + (p1['body'] / 2)
            [span_95](start_span)target_level = min(c['close'], p1_mid)[span_95](end_span)
            [span_96](start_span)stop_level = max(p1['high'], c['high'])[span_96](end_span)

        # 12. [span_97](start_span)[span_98](start_span)Bearish Shooting Star (Kayan Yıldız Ayı) - [Sayfa 18, 96][span_97](end_span)[span_98](end_span)
        elif c['close'] > c['ma20'] and c['high_shadow'] >= (c['body'] * 2) and c['low_shadow'] <= (c['body'] * 0.5):
            [span_99](start_span)[span_100](start_span)pattern_name = "Bearish Shooting Star (Kayan Yıldız Ayı)"[span_99](end_span)[span_100](end_span)
            [span_101](start_span)[span_102](start_span)pattern_type = "Bearish"[span_101](end_span)[span_102](end_span)
            [span_103](start_span)target_level = min(c['open'], c['close'])[span_103](end_span)
            [span_104](start_span)stop_level = c['high'][span_104](end_span)

        # 13. [span_105](start_span)[span_106](start_span)Bearish Dark Cloud Cover (Kara Bulut Ayı) - [Sayfa 19, 99][span_105](end_span)[span_106](end_span)
        elif p1['dir'] == 'white' and c['dir'] == 'black' and c['open'] > p1['high'] and c['close'] <= (p1['open'] + (p1['body'] * 0.5)) and c['close'] > p1['open']:
            [span_107](start_span)[span_108](start_span)pattern_name = "Bearish Dark Cloud Cover (Kara Bulut Ayı)"[span_107](end_span)[span_108](end_span)
            [span_109](start_span)[span_110](start_span)pattern_type = "Bearish"[span_109](end_span)[span_110](end_span)
            [span_111](start_span)target_level = c['close'][span_111](end_span)
            [span_112](start_span)stop_level = c['high'][span_112](end_span)

        # -[span_113](start_span)-- MATRIKS YAŞAM DÖNGÜSÜ DENETİMİ (LIFE CYCLE) ---[span_113](end_span)
        if pattern_name:
            [span_114](start_span)[span_115](start_span)status = "Not Confirmed"[span_114](end_span)[span_115](end_span)
            
            [span_116](start_span)for next_idx in range(i + 1, i + 1 + confirm_bar_count):[span_116](end_span)
                if next_idx >= len(df):
                    break
                [span_117](start_span)f_mum = df.iloc[next_idx][span_117](end_span)
                
                [span_118](start_span)if pattern_type == "Bullish":[span_118](end_span)
                    [span_119](start_span)[span_120](start_span)if status == "Not Confirmed" and f_mum['close'] > target_level:[span_119](end_span)[span_120](end_span)
                        [span_121](start_span)[span_122](start_span)status = "Confirmed"[span_121](end_span)[span_122](end_span)
                    [span_123](start_span)[span_124](start_span)if status == "Confirmed" and f_mum['close'] < stop_level:[span_123](end_span)[span_124](end_span)
                        [span_125](start_span)[span_126](start_span)status = "Confirmed & Fail"[span_125](end_span)[span_126](end_span)
                        break
                        
                [span_127](start_span)elif pattern_type == "Bearish":[span_127](end_span)
                    [span_128](start_span)[span_129](start_span)if status == "Not Confirmed" and f_mum['close'] < target_level:[span_128](end_span)[span_129](end_span)
                        [span_130](start_span)[span_131](start_span)status = "Confirmed"[span_130](end_span)[span_131](end_span)
                    [span_132](start_span)[span_133](start_span)if status == "Confirmed" and f_mum['close'] > stop_level:[span_132](end_span)[span_133](end_span)
                        [span_134](start_span)[span_135](start_span)status = "Confirmed & Fail"[span_134](end_span)[span_135](end_span)
                        break

            results.append({
                "time": int(c['open_time']),
                "time_str": pd.to_datetime(c['open_time'], unit='ms').strftime('%Y-%m-%d %H:%M'),
                "pattern": pattern_name,
                "type": pattern_type,
                "trigger_price": c['close'],
                "target_level": target_level,
                "stop_level": stop_level,
                "status": status
            })

    return results[::-1][:12]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan():
    req_data = request.get_json() or {}
    symbol = req_data.get('symbol', 'BTCUSDT')
    interval = req_data.get('interval', '4h')
    
    df, corrected_symbol = get_binance_live_klines(symbol, interval, limit=180)
    if df is None:
        return jsonify({"success": False, "message": "Geçersiz altcoin sembolü veya API hatası."})
        
    analysis = process_matriks_math_engine(df, confirm_bar_count=3)
    
    projection = "Mevcut periyotta aktif kırılım veya onaylanmış yön sinyali bulunmuyor. Piyasa yatay."
    if analysis:
        latest = analysis[0]
        if latest['status'] == "Confirmed":
            direction = "YUKARI yönlü yükseliş dalgası" if latest['type'] == "Bullish" else "AŞAĞI yönlü satış baskısı"
            projection = f"Son doğrulanan '{latest['pattern']}' geometrik yapısına göre, önümüzdeki 1-2 gün boyunca fiyat hareketinin {direction} şeklinde ilerlemesi beklenmektedir."
        elif latest['status'] == "Confirmed & Fail":
            projection = f"En son saptanan {latest['pattern']} formasyonu onay aldıktan sonra stop seviyesini kırarak başarısız olmuştur (Fail). Trend tersine dönebilir."

    # TradingView grafik entegrasyonu için ham mum verilerini parse ediyoruz
    candles_raw = []
    for _, row in df.iterrows():
        candles_raw.append({
            "time": int(row['open_time'] / 1000),
            "open": row['open'],
            "high": row['high'],
            "low": row['low'],
            "close": row['close']
        })

    return jsonify({
        "success": True,
        "symbol": corrected_symbol,
        "interval": interval,
        "patterns": analysis,
        "projection": projection,
        "candles": candles_raw
    })
