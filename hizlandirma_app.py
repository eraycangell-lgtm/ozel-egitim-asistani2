import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
from gtts import gTTS
from io import BytesIO
import os
import time

# --------------------------------------------------------------------------
# 1. AYARLAR VE SAYFA YAPISI
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ADÜ - Özel Eğitim Asistanı", 
    page_icon="🇹🇷", 
    layout="wide"
)

# --------------------------------------------------------------------------
# 2. GÜVENLİK VE BAĞLANTI (API KEY)
# --------------------------------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    try:
        genai.configure(api_key=api_key)
        model_ai = genai.GenerativeModel('gemini-flash-latest') 
    except Exception as e:
        st.error(f"API Bağlantı Hatası: {e}")
else:
    st.error("⚠️ API Anahtarı Bulunamadı! Lütfen Streamlit Secrets ayarlarını yapınız.")
    st.stop()

# --------------------------------------------------------------------------
# 3. OTURUM YÖNETİMİ
# --------------------------------------------------------------------------
if 'asama' not in st.session_state: st.session_state.asama = 0
if 'sorular' not in st.session_state: st.session_state.sorular = ""
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'konu' not in st.session_state: st.session_state.konu = ""

# --------------------------------------------------------------------------
# 4. FONKSİYONLAR (GARANTİ ÇÖZÜMLER 🛠️)
# --------------------------------------------------------------------------

def tr_karakter_temizle(metin):
    """
    PDF hatasını önlemek için Türkçe karakterleri ASCII'ye çevirir.
    Bu fonksiyon 'ş' -> 's' yapar, böylece PDF asla çökmez.
    """
    if metin is None: return ""
    
    degisimler = {
        "ğ": "g", "Ğ": "G",
        "ş": "s", "Ş": "S",
        "ı": "i", "İ": "I",
        "ç": "c", "Ç": "C",
        "ö": "o", "Ö": "O",
        "ü": "u", "Ü": "U",
        "…": "...", "“": '"', "”": '"', "’": "'", "●": "*"
    }
    for eski, yeni in degisimler.items():
        metin = metin.replace(eski, yeni)
    return metin

def metni_seslendir(text):
    """Metni sese çevirir."""
    try:
        temiz_metin = text.replace("*", "").replace("#", "").replace("📊", "").replace("✅", "")
        tts = gTTS(text=temiz_metin, lang='tr', slow=False)
        ses_dosyasi = BytesIO()
        tts.write_to_fp(ses_dosyasi)
        return ses_dosyasi
    except:
        return None

def yapay_zeka_cevap(prompt_text, resim=None):
    """Hata yakalama mekanizmalı yapay zeka isteği"""
    try:
        if resim:
            response = model_ai.generate_content([prompt_text, resim])
        else:
            response = model_ai.generate_content(prompt_text)
        return response.text
    except Exception as e:
        hata_msj = str(e)
        if "429" in hata_msj or "quota" in hata_msj.lower():
            return "⚠️ HIZ SINIRI: Google sistemi şu an çok yoğun. Lütfen 30 saniye bekleyip tekrar deneyin."
        else:
            return f"⚠️ Bir hata oluştu: {hata_msj}"

def soru_uret(konu, sinif, model_tipi, resim=None):
    prompt_text = f"""
    ROL: Sen T.C. MEB mevzuatına hakim özel eğitim uzmanısın.
    KONU: {konu}. SINIF: {sinif}. MODEL: {model_tipi}.
    GÖREV: Öğrenci için 3 adet üst düzey düşünme becerisi sorusu hazırla.
    """
    return yapay_zeka_cevap(prompt_text, resim)

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    prompt = f"""
    GÖREV: Aşağıdaki cevapları 'BEP Birimi' ciddiyetiyle analiz et.
    SORULAR: {sorular}
    CEVAPLAR: {cevaplar}
    MODEL: {model_tipi}
    ÇIKTI FORMATI:
    1. PERFORMANS DUZEYI
    2. KAZANIM DEGERLENDIRMESI
    3. GELISIM ALANLARI
    4. ZENGINLESTIRME EYLEM PLANI
    """
    return yapay_zeka_cevap(prompt)

def create_pdf(text, ogrenci_adi, konu):
    """HATA VERMEYEN PDF OLUŞTURUCU"""
    
    # 1. ÖNCE HER ŞEYİ TEMİZLE (Kritik Adım)
    text = tr_karakter_temizle(text)
    ogrenci_adi = tr_karakter_temizle(ogrenci_adi)
    konu = tr_karakter_temizle(konu)

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
        
        # Font Yükleme (Varsa Arial, Yoksa Helvetica)
        font_path = 'arial.ttf'
        if os.path.exists(font_path):
            pdf.add_font('Arial', '', font_path, uni=True)
            pdf.set_font('Arial', '', 11)
        else:
            pdf.set_font("Helvetica", size=11)

        # Başlıklar
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"Ogrenci: {ogrenci_adi} | Konu: {konu}", 0, 1)
        pdf.line(10, 35, 200, 35)
        pdf.ln(5)
        
        # İçerik
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, text)
        
        # Çıktı (Latin-1 hatasını replace ile bypass et)
        return pdf.output(dest='S').encode('latin-1', 'replace')
    
    except Exception as e:
        return None

def sifirla():
    st.session_state.asama = 0
    st.session_state.sorular = ""
    st.session_state.analiz = ""
    st.rerun()

# --------------------------------------------------------------------------
# 5. ARAYÜZ
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
    if st.button("🔄 Sıfırla", type="primary"):
        sifirla()

col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("logo.png"): st.image("logo.png", width=80)
    else: st.write("🇹🇷")
with col2:
    st.title("Özel Eğitim Asistanı")
    st.caption("MEB Standartlarına Uygun Raporlama ve Analiz Aracı")

st.markdown("---")

if st.session_state.asama == 0:
    st.info(f"Model: {egitim_modeli} | Sınıf: {sinif}")
    
    uploaded_file = st.file_uploader("Görsel Yükle (Opsiyonel):", type=["jpg", "png"])
    resim = Image.open(uploaded_file) if uploaded_file else None
    if resim: st.image(resim, width=200)

    colA, colB = st.columns([3, 1])
    with colA:
        konu = st.text_input("Konu/Kazanım:", placeholder="Örn: Uzay Kirliliği")
    with colB:
        st.write("")
        st.write("")
        if st.button("Başlat 🚀", type="primary"):
            if konu:
                with st.spinner("Analiz ediliyor..."):
                    st.session_state.konu = konu
                    st.session_state.sorular = soru_uret(konu, sinif, egitim_modeli, resim)
                    st.session_state.asama = 1
                    st.rerun()

elif st.session_state.asama == 1:
    st.success("Sorular Hazır.")
    
    # Eğer Hız Sınırı hatası aldıysak ekrana yazdırır
    if "HIZ SINIRI" in st.session_state.sorular:
        st.warning(st.session_state.sorular)
        if st.button("Tekrar Dene"):
            st.rerun()
    else:
        st.markdown(st.session_state.sorular)
        
        with st.form("cevap_form"):
            cvp = st.text_area("Öğrenci Cevapları:", height=150)
            if st.form_submit_button("Raporla 🎯"):
                if cvp:
                    with st.spinner("Rapor yazılıyor..."):
                        st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cvp, egitim_modeli)
                        st.session_state.asama = 2
                        st.rerun()

elif st.session_state.asama == 2:
    st.markdown(f"### Rapor: {ad}")
    
    if "HIZ SINIRI" in st.session_state.analiz:
        st.warning(st.session_state.analiz)
        if st.button("Tekrar Dene"):
            st.rerun()
    else:
        st.markdown(st.session_state.analiz)
        
        c1, c2 = st.columns(2)
        with c1:
            # PDF BUTONU
            pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
            if pdf_data:
                st.download_button("📄 PDF İndir", data=pdf_data, file_name="Rapor.pdf", mime="application/pdf", type="primary")
            else:
                st.error("PDF oluşturulamadı (Hala karakter sorunu olabilir).")
                
        with c2:
            # SES BUTONU
            if st.button("🔊 Dinle"):
                ses = metni_seslendir(st.session_state.analiz)
                if ses: st.audio(ses)

        st.markdown("---")
        if st.button("Yeni Konu"): sifirla()
