import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
from gtts import gTTS
from io import BytesIO
import os

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
# 4. YARDIMCI FONKSİYONLAR (GARANTİ ÇÖZÜMLER 🛠️)
# --------------------------------------------------------------------------

def tr_karakter_duzelt(metin):
    """
    PDF hatasını önlemek için riskli Türkçe karakterleri 
    en yakın ASCII karşılıklarına dönüştürür.
    """
    degisimler = {
        "ğ": "g", "Ğ": "G",
        "ş": "s", "Ş": "S",
        "ı": "i", "İ": "I",
        "ç": "c", "Ç": "C",
        "ö": "o", "Ö": "O",
        "ü": "u", "Ü": "U",
        # Diğer semboller
        "…": "...", "“": '"', "”": '"', "’": "'", "●": "*"
    }
    for eski, yeni in degisimler.items():
        metin = metin.replace(eski, yeni)
    return metin

def metni_seslendir(text):
    """Metni sese çevirir."""
    try:
        # Seslendirme motoru Türkçe karakterleri sever, temizlemeye gerek yok
        temiz_metin = text.replace("*", "").replace("#", "").replace("📊", "").replace("✅", "")
        tts = gTTS(text=temiz_metin, lang='tr', slow=False)
        ses_dosyasi = BytesIO()
        tts.write_to_fp(ses_dosyasi)
        return ses_dosyasi
    except:
        return None

def soru_uret(konu, sinif, model_tipi, resim=None):
    """MEB Kazanım odaklı sorular üretir."""
    prompt_text = f"""
    ROL: Sen T.C. Milli Eğitim Bakanlığı (MEB) mevzuatına hakim kıdemli bir özel eğitim uzmanısın.
    
    ÖĞRENCİ: {sinif}. sınıf, özel yetenekli.
    KONU: '{konu}'
    MODEL: {model_tipi}
    
    GÖREV: 
    Öğrencinin hazırbulunuşluk düzeyini belirlemek için '{model_tipi}' yaklaşımına uygun 3 adet 'Üst Düzey' soru hazırla.
    Sorular Bloom Taksonomisinin analiz/sentez basamağında olsun.
    """
    try:
        if resim:
            response = model_ai.generate_content([prompt_text, resim])
        else:
            response = model_ai.generate_content(prompt_text)
        return response.text
    except:
        return "Bağlantı hatası, lütfen tekrar deneyin."

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    """Cevapları raporlar."""
    prompt = f"""
    GÖREV: Aşağıdaki öğrenci cevaplarını bir 'BEP Birimi' üyesi ciddiyetiyle analiz et.
    
    SORULAR: {sorular}
    CEVAPLAR: {cevaplar}
    MODEL: {model_tipi}
    
    ÇIKTI FORMATI:
    1. PERFORMANS DUZEYI: (Öğrencinin durumu)
    2. KAZANIM DEGERLENDIRMESI: (Güçlü yönler)
    3. GELISIM ALANLARI: (Eksikler)
    4. ZENGINLESTIRME EYLEM PLANI: (Somut proje/görev önerisi)
    
    NOT: Türkçe karakter kullanabilirsin ama çok karmaşık sembollerden kaçın.
    """
    try:
        return model_ai.generate_content(prompt).text
    except:
        return "Rapor oluşturulamadı."

def create_pdf(text, ogrenci_adi, konu):
    """PDF Oluşturucu - HATA ÖNLEYİCİ MOD"""
    
    # 1. Metni Güvenli Hale Getir (Hata Sebebi Olan Harfleri Temizle)
    guvenli_text = tr_karakter_duzelt(text)
    guvenli_ad = tr_karakter_duzelt(ogrenci_adi)
    guvenli_konu = tr_karakter_duzelt(konu)

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

    pdf = PDF()
    pdf.add_page()
    
    # Font (Arial varsa kullan yoksa standart)
    font_path = 'arial.ttf'
    if os.path.exists(font_path):
        pdf.add_font('Arial', '', font_path, uni=True)
        pdf.set_font('Arial', '', 11)
    else:
        pdf.set_font("Arial", size=11)

    # Başlıklar
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, f"Ogrenci: {guvenli_ad} | Konu: {guvenli_konu}", 0, 1)
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)
    
    # İçerik
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 7, guvenli_text)
    
    # ÇIKTIYI GÜVENLİ ALMA (Latin-1 hatasını bypass eder)
    return pdf.output(dest='S').encode('latin-1', 'replace')

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
    st.caption("MEB Standartlarına Uygun Raporlama")

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
    st.markdown(st.session_state.analiz)
    
    c1, c2 = st.columns(2)
    with c1:
        # PDF BUTONU (Artık Çökmeyecek)
        pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
        st.download_button("📄 PDF İndir", data=pdf_data, file_name="Rapor.pdf", mime="application/pdf", type="primary")
            
    with c2:
        # SES BUTONU
        if st.button("🔊 Dinle"):
            ses = metni_seslendir(st.session_state.analiz)
            if ses: st.audio(ses, format='audio/mp3')

    st.markdown("---")
    if st.button("Yeni Konu"): sifirla()
