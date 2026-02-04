import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Özel Eğitim Asistanı", page_icon="🧩", layout="wide")

# --- API Anahtarı (Streamlit Secrets'tan çeker) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    st.warning("Lütfen Streamlit panelinden API anahtarını ayarlayınız.")

# --- Model Ayarı (Latest) ---
model_ai = genai.GenerativeModel('gemini-flash-latest')

# --- PDF Oluşturma Fonksiyonu ---
def create_pdf(text):
    class PDF(FPDF):
        def header(self):
            # Başlık (Varsa logonun olduğu yer)
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Ozel Egitim Asistani Raporu', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    
    # Türkçe karakter desteği için font ekleme
    # Klasöründe 'arial.ttf' dosyası olduğundan emin ol!
    try:
        pdf.add_font('Arial', '', 'arial.ttf', uni=True)
        pdf.set_font('Arial', '', 12)
    except:
        # Font bulunamazsa standart fonta dön (Türkçe karakterler bozuk çıkabilir)
        pdf.set_font("Arial", size=12)

    # Metni yazdır (Satır satır)
    # multi_cell uzun metinleri alt satıra geçirir
    pdf.multi_cell(0, 10, text)
    
    return pdf.output(dest='S').encode('latin-1', 'replace') # Streamlit için byte verisi

# --- Arayüz ---
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=150)
    except:
        st.write("🧩") # Logo yoksa emoji göster
with col2:
    st.title("Üstün Yetenekli Hızlandırma Planlayıcısı")
    st.markdown("*Özel Eğitim Asistanınız*")

# Kullanıcıdan Girdi Alma
soru = st.text_area("Öğrenci durumu veya sorunuzu buraya yazın:", height=150, 
                   placeholder="Örn: 3. sınıf öğrencisi matematikte çok ileri, ne yapabilirim?")

if st.button("Plan Hazırla ✨"):
    if soru:
        with st.spinner("Asistan düşünüyor..."):
            try:
                response = model_ai.generate_content(soru)
                cevap = response.text
                
                st.markdown("### 💡 Öneri Planı")
                st.write(cevap)
                
                # --- PDF İNDİRME BUTONU ---
                st.markdown("---")
                pdf_data = create_pdf(cevap)
                st.download_button(
                    label="📄 Bu Planı PDF Olarak İndir",
                    data=pdf_data,
                    file_name="ozel_egitim_plani.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
    else:
        st.warning("Lütfen önce bir soru yazın.")