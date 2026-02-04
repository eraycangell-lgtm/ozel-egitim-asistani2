import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
from gtts import gTTS
from io import BytesIO
import os
import time
import re # Düzenli ifadeler (Regex) kütüphanesi - Temizlik için şart

# --------------------------------------------------------------------------
# 1. AYARLAR VE API
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ADÜ - Özel Eğitim Asistanı", 
    page_icon="🇹🇷", 
    layout="wide"
)

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model_ai = genai.GenerativeModel('gemini-flash-latest') 
    except Exception as e:
        st.error(f"Sistem Hatası: API anahtarı doğrulanamadı. ({e})")
        st.stop()
else:
    st.error("⚠️ Sistem Hatası: API Anahtarı eksik.")
    st.stop()

# Session State Tanımları
if 'asama' not in st.session_state: st.session_state.asama = 0
if 'sorular' not in st.session_state: st.session_state.sorular = ""
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'konu' not in st.session_state: st.session_state.konu = ""

# --------------------------------------------------------------------------
# 2. GÜÇLENDİRİLMİŞ FONKSİYONLAR 🛠️
# --------------------------------------------------------------------------

def super_temizlik(metin):
    """
    Bu fonksiyon metni PDF için güvenli hale getirir.
    Latin-1 hatasına sebep olabilecek HER ŞEYİ temizler.
    """
    if not metin: return ""
    
    # 1. Önce bilinen Türkçe karakterleri değiştir
    degisimler = {
        "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
        "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
        "…": "...", "“": '"', "”": '"', "’": "'", "●": "*", "–": "-", "—": "-"
    }
    for eski, yeni in degisimler.items():
        metin = metin.replace(eski, yeni)
    
    # 2. Bilinmeyen tüm garip sembolleri (Emoji vb.) sil at (Regex)
    # Sadece harfler, sayılar ve temel noktalama işaretleri kalsın.
    metin = re.sub(r'[^\x00-\x7F]+', '', metin)
    
    return metin

def yapay_zeka_istegi(prompt, resim=None):
    """
    Hız sınırına takılırsa 3 kere dener, pes etmez.
    """
    max_deneme = 3
    for i in range(max_deneme):
        try:
            if resim:
                response = model_ai.generate_content([prompt, resim])
            else:
                response = model_ai.generate_content(prompt)
            return response.text
        except Exception as e:
            hata = str(e).lower()
            if "429" in hata or "quota" in hata:
                # Kota dolduysa bekle
                bekleme = (i + 1) * 5 # 5, 10, 15 saniye artarak bekle
                st.toast(f"🚦 Sistem yoğun, sıranız bekleniyor... ({bekleme} sn)")
                time.sleep(bekleme)
                continue
            else:
                # Başka hataysa bildir
                return f"Hata oluştu: {str(e)}"
    return "⚠️ Sistem şu an çok yoğun. Lütfen 1 dakika sonra tekrar deneyiniz."

def soru_uret(konu, sinif, model_tipi, resim=None):
    prompt = f"""
    ROL: Sen MEB mevzuatına hakim bir özel eğitim uzmanısın.
    GÖREV: {sinif}. sınıf seviyesindeki özel yetenekli öğrenci için, '{konu}' konusunda, 
    '{model_tipi}' modeline uygun 3 adet üst düzey soru hazırla.
    """
    return yapay_zeka_istegi(prompt, resim)

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    prompt = f"""
    GÖREV: Öğrenci cevaplarını analiz et ve resmi rapor diliyle yaz.
    SORULAR: {sorular}
    CEVAPLAR: {cevaplar}
    MODEL: {model_tipi}
    ÇIKTI FORMATI:
    1. PERFORMANS DÜZEYİ
    2. KAZANIMLAR
    3. GELİŞİM ALANLARI
    4. PROJE ÖNERİSİ
    """
    return yapay_zeka_istegi(prompt)

def create_pdf(text, ogrenci_adi, konu):
    """ÇÖKMEYEN PDF OLUŞTURUCU"""
    
    # --- KRİTİK NOKTA: Verileri temizle ---
    text = super_temizlik(text)
    ogrenci_adi = super_temizlik(ogrenci_adi)
    konu = super_temizlik(konu)
    
    class PDF(FPDF):
        def header(self):
            if os.path.exists("logo.png"):
                try:
                    self.image('logo.png', 10, 8, 20)
                    self.set_font('Arial', 'B', 12)
                    self.cell(25)
                    self.cell(0, 10, 'TC. ADU OZEL EGITIM RAPORU', 0, 1, 'L')
                except: pass
            else:
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'TC. OZEL EGITIM RAPORU', 0, 1, 'C')
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

    try:
        pdf = PDF()
        pdf.add_page()
        
        # Font Ayarı
        font_path = 'arial.ttf'
        if os.path.exists(font_path):
            pdf.add_font('Arial', '', font_path, uni=True)
            pdf.set_font('Arial', '', 11)
        else:
            pdf.set_font("Helvetica", size=11)

        # Yazdırma
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"Ogrenci: {ogrenci_adi} | Konu: {konu}", 0, 1)
        pdf.line(10, 35, 200, 35)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, text)
        
        return pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e:
        st.error(f"PDF Oluşturulamadı: {e}")
        return None

def metni_seslendir(text):
    try:
        # Seslendirme için temizliğe gerek yok, gTTS Türkçeyi sever
        temiz = text.replace("*", "").replace("#", "")
        tts = gTTS(text=temiz, lang='tr')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

def sifirla():
    st.session_state.asama = 0
    st.session_state.sorular = ""
    st.session_state.analiz = ""
    st.rerun()

# --------------------------------------------------------------------------
# 3. ARAYÜZ
# --------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=120)
    else: st.write("🇹🇷 ADÜ")
    st.markdown("---")
    st.info("**Eray Cangel**\n\nÖzel Eğitim Uzmanı\nNo: 242018077")
    st.markdown("---")
    st.header("📋 Öğrenci")
    ad = st.text_input("Adı Soyadı", "Zekeriya Ayral")
    sinif = st.selectbox("Sınıf", [1, 2, 3, 4, 5, 6, 7, 8])
    egitim_modeli = st.selectbox("Model", ["Renzulli", "SCAMPER", "Purdue"])
    st.markdown("---")
    if st.button("🔄 Yeni Analiz", type="primary"): sifirla()

col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("logo.png"): st.image("logo.png", width=80)
    else: st.write("🇹🇷")
with col2:
    st.title("Özel Eğitim Asistanı")
    st.caption("MEB Standartlarına Uygun Raporlama ve Analiz Aracı")
st.markdown("---")

# AŞAMA 0: GİRİŞ
if st.session_state.asama == 0:
    st.info(f"Model: {egitim_modeli} | Sınıf: {sinif}")
    
    uploaded_file = st.file_uploader("Görsel Yükle (Opsiyonel):", type=["jpg", "png"])
    resim = Image.open(uploaded_file) if uploaded_file else None
    if resim: st.image(resim, width=200)

    colA, colB = st.columns([3, 1])
    with colA:
        konu = st.text_input("Konu/Kazanım:", placeholder="Örn: Sürdürülebilir Enerji")
    with colB:
        st.write("")
        st.write("")
        if st.button("Başlat 🚀", type="primary"):
            if konu:
                with st.spinner("Analiz yapılıyor (Bu işlem 10-15 saniye sürebilir)..."):
                    st.session_state.konu = konu
                    st.session_state.sorular = soru_uret(konu, sinif, egitim_modeli, resim)
                    st.session_state.asama = 1
                    st.rerun()

# AŞAMA 1: SORU - CEVAP
elif st.session_state.asama == 1:
    st.success("Sorular Hazır.")
    st.markdown(st.session_state.sorular)
    
    with st.form("cevap_form"):
        cvp = st.text_area("Öğrenci Cevapları:", height=150)
        if st.form_submit_button("Raporla 🎯"):
            if cvp:
                with st.spinner("Rapor yazılıyor..."):
                    st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cvp, egitim_modeli)
                    st.session_state.asama = 2
                    st.rerun()

# AŞAMA 2: SONUÇ
elif st.session_state.asama == 2:
    st.markdown(f"### Rapor: {ad}")
    st.markdown(st.session_state.analiz)
    
    c1, c2 = st.columns(2)
    with c1:
        # PDF Butonu
        pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
        if pdf_data:
            st.download_button("📄 PDF İndir", data=pdf_data, file_name="Rapor.pdf", mime="application/pdf", type="primary")
        else:
            st.error("PDF oluşturulamadı.")
            
    with c2:
        # Ses Butonu
        if st.button("🔊 Dinle"):
            ses = metni_seslendir(st.session_state.analiz)
            if ses: st.audio(ses)
    
    st.markdown("---")
    if st.button("Yeni Konu"): sifirla()
