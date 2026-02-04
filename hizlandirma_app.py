import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os

# --------------------------------------------------------------------------
# 1. AYARLAR VE SAYFA YAPISI
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Özel Eğitim Asistanı",
    page_icon="🧩",
    layout="wide"
)

# API Anahtarı Kontrolü
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("⚠️ API Anahtarı bulunamadı! Lütfen Streamlit panelinden secrets ayarlarını yapın.")
    st.stop()

# Model Tanımlaması (En güncel hızlı model)
model_ai = genai.GenerativeModel('gemini-flash-latest')

# --------------------------------------------------------------------------
# 2. PDF OLUŞTURMA FONKSİYONU (Geliştirilmiş Temizlik)
# --------------------------------------------------------------------------
def create_pdf(text):
    """
    Metni alır, temizler ve PDF byte verisi olarak döndürür.
    """
    # A. Metin Temizliği (PDF'in bozulmaması için sembolleri basitleştir)
    replacements = {
        # Markdown İşaretleri
        "**": "", "__": "", "### ": "", "## ": "", "# ": "",
        
        # Matematiksel Semboller
        "≈": " yaklasik ", "≠": " esit degil ", "≤": " kucuk esit ", "≥": " buyuk esit ",
        "×": "x", "÷": "/", "−": "-", "–": "-", "—": "-",
        "Δ": "Delta", "π": "Pi", "∑": "Toplam", "∞": "Sonsuz",
        "→": "->", "←": "<-", "√": "karekok"
    }
    
    # Metindeki her bir sembolü değiştir
    for old, new in replacements.items():
        text = text.replace(old, new)

    # B. PDF Sınıfı
    class PDF(FPDF):
        def header(self):
            # Logo varsa ekle
            if os.path.exists("logo.png"):
                try:
                    self.image('logo.png', 10, 8, 25) # x, y, genişlik
                    self.set_font('Arial', 'B', 15)
                    self.cell(30) # Logo payı
                    self.cell(0, 10, 'Ozel Egitim Asistani Raporu', 0, 1, 'L')
                except:
                    pass
            else:
                self.set_font('Arial', 'B', 15)
                self.cell(0, 10, 'Ozel Egitim Asistani Raporu', 0, 1, 'C')
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    
    # C. Font Yükleme (Türkçe Karakter İçin Kritik)
    font_path = 'arial.ttf'
    if os.path.exists(font_path):
        pdf.add_font('Arial', '', font_path, uni=True)
        pdf.set_font('Arial', '', 11)
    else:
        # Font yoksa standart fonta dön (Türkçe karakterler bozuk çıkabilir)
        pdf.set_font("Helvetica", size=11)

    # D. Yazdırma (Multi-cell satır atlatmayı sağlar)
    pdf.multi_cell(0, 8, text)
    
    # E. Çıktı
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --------------------------------------------------------------------------
# 3. ARAYÜZ (FRONTEND)
# --------------------------------------------------------------------------

# Başlık ve Logo Alanı
col_logo, col_title = st.columns([1, 6])

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.write("🧩") # Logo dosyası yoksa emoji koy

with col_title:
    st.title("Üstün Yetenekli Öğrenci Planlayıcısı")
    st.markdown("**Devlerin Omuzlarında Yükselen Nesiller İçin** | *Kişiselleştirilmiş Eğitim Asistanı*")

st.markdown("---")

# Kullanıcı Giriş Alanı
soru = st.text_area(
    "Planlama veya Soru Alanı:",
    height=180,
    placeholder="Örneğin: 3. sınıf öğrencisi matematikte, özellikle kesirler konusunda çok ileri düzeyde. Ona uygun bir zenginleştirme planı hazırlar mısın?"
)

# Buton ve İşlem
if st.button("Planı Hazırla ve Analiz Et ✨", type="primary"):
    if not soru:
        st.warning("Lütfen önce bir durum veya soru giriniz.")
    else:
        with st.spinner("Asistan pedagojik analiz yapıyor..."):
            try:
                # Yapay Zekaya Gönder
                response = model_ai.generate_content(soru)
                cevap_metni = response.text
                
                # Ekrana Yazdır
                st.success("Analiz Tamamlandı!")
                st.markdown("### 📋 Hazırlanan Plan")
                st.write(cevap_metni)
                
                # PDF Oluştur ve İndir Butonu Göster
                st.markdown("---")
                pdf_verisi = create_pdf(cevap_metni)
                
                st.download_button(
                    label="📄 Bu Planı PDF Olarak İndir",
                    data=pdf_verisi,
                    file_name="ozel_egitim_plani.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
