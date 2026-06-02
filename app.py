import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime

# --- 1. SİSTEM VE SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Alpha Terminal v53.0 | Wall Street Karar Motoru", initial_sidebar_state="expanded")

# CSS: DOM Sıçramalarını Engelleyen Kararlı Tasarım
st.markdown("""
    <style>
        .stApp { background-color: #020617; color: #f8fafc; }
        .block-container { padding: 1rem 1.5rem !important; }
        .matrix-card { 
            border: 1px solid #1e293b; 
            border-radius: 8px; 
            padding: 16px; 
            background: #0f172a; 
            margin-bottom: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .section-title { 
            font-size: 18px; 
            font-weight: bold; 
            color: #3b82f6; 
            border-bottom: 2px solid #1e293b; 
            padding-bottom: 6px; 
            margin-bottom: 14px; 
            text-transform: uppercase;
        }
        .metric-title { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { font-size: 20px; font-weight: bold; color: #f8fafc; margin-top: 4px; }
        .trend-up { color: #22c55e; font-weight: bold; }
        .trend-down { color: #f43f5e; font-weight: bold; }
        .stRadio > div { background-color: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #1e293b; }
        .stDataFrame { border: 1px solid #1e293b; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BELLEK KATMANI ---
if "ogrenilen_hatalar" not in st.session_state:
    st.session_state["ogrenilen_hatalar"] = {}
if "tarama_sayisi" not in st.session_state:
    st.session_state["tarama_sayisi"] = 0
if "islem_gecmisi" not in st.session_state:
    st.session_state["islem_gecmisi"] = []

def sistem_ogrenme_kaydi(hisse_kodu, hata_mesaji):
    st.session_state["ogrenilen_hatalar"][hisse_kodu] = {
        "Hata Zamanı": datetime.now().strftime("%H:%M:%S"),
        "Hata Detayı": str(hata_mesaji),
        "Uygulanan Çözüm": "Güvenli Varsayılan Değer Atandı"
    }

# --- 3. CANLI MAKRO VERİ MOTORU ---
@st.cache_data(ttl=60)
def kurumsal_makro_veri_oku():
    gostergeler = {
        "S&P 500 Vadeli": "ES=F", "Nasdaq Vadeli": "NQ=F", "Dow Jones Vadeli": "YM=F",
        "Korku Endeksi (VIX)": "^VIX", "ABD 10 Yıllık Tahvil": "^TNX", "ABD 2 Yıllık Tahvil": "2Y=F",
        "Dolar Endeksi (DXY)": "DX-Y.NYB", "Ons Altın Vadeli": "GC=F", "Ham Petrol WTI": "CL=F", "Bitcoin": "BTC-USD"
    }
    sonuclar = {}
    for etiket, sembol in gostergeler.items():
        try:
            veri = yf.Ticker(sembol).history(period="2d")
            if len(veri) >= 2:
                kapanis = veri['Close'].iloc[-1]
                onceki = veri['Close'].iloc[-2]
                degisim = ((kapanis - onceki) / onceki) * 100
                sonuclar[etiket] = {"fiyat": kapanis, "degisim": degisim}
            else:
                sonuclar[etiket] = {"fiyat": 0.0, "degisim": 0.0}
        except Exception:
            sonuclar[etiket] = {"fiyat": 0.0, "degisim": 0.0}
    return sonuclar

makro_sozluk = kurumsal_makro_veri_oku()

# Üst Bilgi Alanı
st.markdown("### 🌎 Küresel Vadeli İşlemler Canlı Takip Paneli")
ust_sutunlar = st.columns(5)
makro_listesi = list(makro_sozluk.items())

for i, (anahtar, deger) in enumerate(makro_listesi[:5]):
    with ust_sutunlar[i]:
        renk_kodu = "#22c55e" if deger["degisim"] >= 0 else "#f43f5e"
        renk_sinifi = "trend-up" if deger["degisim"] >= 0 else "trend-down"
        isaret = "+" if deger["degisim"] >= 0 else ""
        
        kart_html = f"""
            <div class="matrix-card" style="padding: 10px; border-top: 3px solid {renk_kodu};">
                <div class="metric-title">{anahtar}</div>
                <div class="metric-value" style="font-size:15px;">
                    {deger['fiyat']:,.2f} <span class="{renk_sinifi}" style="font-size:12px;">({isaret}{deger['degisim']:.2f}%)</span>
                </div>
            </div>
        """
        st.markdown(kart_html, unsafe_allow_html=True)

st.divider()

# --- 4. WALL STREET ANALİTİK KARAR MOTORU ---
def wall_street_karar_mekanizmasi(fiyat, rsi, sma50, buyume_orani, marj_orani):
    puan = 50  
    if rsi < 40: puan += 15  
    elif rsi > 70: puan -= 15 
    if fiyat > sma50: puan += 10 
    else: puan -= 10
        
    if buyume_orani != "Veri Kısıtlı":
        try:
            b_val = float(buyume_orani.replace("%", ""))
            if b_val >= 25: puan += 15
            elif b_val > 10: puan += 5
            elif b_val < 0: puan -= 10
        except: pass
        
    if marj_orani != "Veri Kısıtlı":
        try:
            m_val = float(marj_orani.replace("%", ""))
            if m_val >= 60: puan += 10  
            elif m_val < 30: puan -= 10
        except: pass

    if puan >= 75:
        return puan, "🟢 MÜKEMMEL ALIM (STRONG BUY)", "Kurumsal fon girişleri yoğun, temel çarpanlar teknik iskontoyu destekliyor."
    elif puan >= 55:
        return puan, "🔵 KADEMELİ TOPLAMA (BUY)", "Yüksek oynaklık stratejisine uygun, parça parça biriktirilebilir yapı."
    elif puan >= 40:
        return puan, "🟡 SABİT TUT / İZLE (HOLD)", "Mevcut risk dengeli, yeni pozisyon açmak için katalizör beklenmeli."
    else:
        return puan, "🔴 AZALT / RİSKTEN KAÇ (REDUCE)", "Marj daralması veya aşırı fiyatlama riski mevcut, nakit oranını artır."

# --- 5. EVRENSEL HİSSE ALGORİTMİK DENETİM MOTORU ---
@st.cache_data(ttl=120)
def kurumsal_hisse_tarayici(hisse_kodu):
    try:
        hisse = yf.Ticker(hisse_kodu)
        gecmis = hisse.history(period="1y")
        if gecmis.empty: 
            sistem_ogrenme_kaydi(hisse_kodu, "Geçmiş fiyat verisi boş döndü.")
            return None
        
        # Pandas_ta entegrasyonu güvenli hale getirildi
        gecmis.ta.rsi(length=14, append=True)
        gecmis.ta.sma(length=50, append=True)
        gecmis.ta.bbands(length=20, std=2, append=True)
        
        # Sütun isimleri tam olarak kontrol ediliyor
        rsi_col = [c for c in gecmis.columns if 'RSI' in c]
        sma_col = [c for c in gecmis.columns if 'SMA' in c]
        bbl_col = [c for c in gecmis.columns if 'BBL' in c]
        bbu_col = [c for c in gecmis.columns if 'BBU' in c]

        son = gecmis.iloc[-1]
        fiyat = son['Close']
        
        rsi = round(son[rsi_col[0]]) if rsi_col and not pd.isna(son[rsi_col[0]]) else 50
        sma50_deger = son[sma_col[0]] if sma_col and not pd.isna(son[sma_col[0]]) else fiyat
        destek = son[bbl_col[0]] if bbl_col and not pd.isna(son[bbl_col[0]]) else fiyat * 0.95
        direnc = son[bbu_col[0]] if bbu_col and not pd.isna(son[bbu_col[0]]) else fiyat * 1.05
        
        buyume, marj, fk, borc, abone = "Veri Kısıtlı", "Veri Kısıtlı", "Zarar", "Düşük", "Belirlenemedi"
        try:
            bilgi = hisse.info
            if bilgi:
                if bilgi.get('revenueGrowth') is not None:
