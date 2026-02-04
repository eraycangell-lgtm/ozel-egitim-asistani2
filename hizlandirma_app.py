import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
from gtts import gTTS
from io import BytesIO
import os

# --------------------------------------------------------------------------
# 1. AYARLAR
# --------------------------------------------------------------------------
st.set_page_config(page_title="ADÜ Asistanı (Debug Modu)", layout="wide")

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model_ai = genai.GenerativeModel('gemini-flash-latest')
    except Exception as e:
        st.error(f"⚠️ API Bağlantı Hatası: {e}")
else:
    st.error("⚠️ API Anahtarı Bulunamadı! Secrets ayarlarını kontrol et.")
    st.stop()

# --------------------------------------------------------------------------
# 2. FONKSİYONLAR (HATA GÖSTEREN VERSİYON 🚨)
# --------------------------------------------------------------------------

def tr_duzelt(text):
    """PDF için Türkçe karakterleri ASCII'ye zorlar (Çökmemesi için)"""
    mapping = {
        "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
        "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
        "…": "...", "●": "*"
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text

def metni_seslendir(text):
    try:
        temiz = text.replace("*", "").replace("#", "")
        tts = gTTS(text=temiz, lang='tr')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"Ses Hatası: {e}")
        return None

def yapay_zeka_sor(prompt, resim=None):
    """Hata olursa sebebini açıkça yazar"""
    try:
        if resim:
            response = model_ai.generate_content([prompt, resim])
        else:
            response = model_ai.generate_content(prompt)
        return response.text
    except Exception as e:
        # BURASI KRİTİK: Hatayı gizlemiyoruz, ekrana basıyoruz
        return f"⚠️ HATA OLUŞTU:\n{str(e)}"

def create_pdf(text, ogrenci, konu):
    """PDF oluştururken hata verirse yakalar"""
    try:
        text = tr_duzelt(text)
        ogrenci = tr_duzelt(ogrenci)
        konu = tr_duzelt(konu)

        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'OZEL EGITIM RAPORU', 0, 1, 'C')
                self.ln(5)

        pdf = PDF()
        pdf.add_page()
        
        # Arial varsa kullan yoksa Helvetica
        if os.path.exists('arial.ttf'):
            pdf.add_font('Arial', '', 'arial.ttf', uni=True)
            pdf.set_font('Arial', '', 11)
        else:
            pdf.set_font('Helvetica', '', 11)

        pdf.multi_cell(0, 7, f"Ogrenci: {ogrenci}\nKonu: {konu}\n\n{text}")
        
        # 'latin-1' hatasını önleyen sihirli kod: 'replace'
        return pdf.output(dest='S').encode('latin-1', 'replace')
    
    except Exception as e:
        st.error(f"PDF Hatası Detayı: {e}")
        return None

# --------------------------------------------------------------------------
# 3. ARAYÜZ
# --------------------------------------------------------------------------
if 'asama' not in st.session_state: st.session_state.asama = 0
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'sorular' not in st.session_state: st.session_state.sorular = ""

st.title("🛠️ Hata Tespit Modu")

# Aşama 0: Giriş
if st.session_state.asama == 0:
    konu = st.text_input("Konu Giriniz:")
    if st.button("Soruları Üret"):
        if konu:
            prompt = f"Sen MEB uzmanısın. Konu: {konu}. 3 adet soru sor."
            st.session_state.sorular = yapay_zeka_sor(prompt)
            st.session_state.konu = konu
            st.session_state.asama = 1
            st.rerun()

# Aşama 1: Soru & Cevap
elif st.session_state.asama == 1:
    st.info(st.session_state.sorular)
    cvp = st.text_area("Cevaplar:")
    if st.button("Analiz Et"):
        prompt = f"Analiz et: {cvp}. Sorular: {st.session_state.sorular}"
        st.session_state.analiz = yapay_zeka_sor(prompt)
        st.session_state.asama = 2
        st.rerun()

# Aşama 2: Sonuç
elif st.session_state.asama == 2:
    st.write(st.session_state.analiz)
    
    # PDF Butonu
    pdf_data = create_pdf(st.session_state.analiz, "Ogrenci", st.session_state.get('konu', 'Genel'))
    if pdf_data:
        st.download_button("PDF İndir", pdf_data, "rapor.pdf", "application/pdf")
    
    # Ses Butonu
    if st.button("Sesli Dinle"):
        ses = metni_seslendir(st.session_state.analiz)
        if ses: st.audio(ses)
        
    if st.button("Başa Dön"):
        st.session_state.asama = 0
        st.rerun()
