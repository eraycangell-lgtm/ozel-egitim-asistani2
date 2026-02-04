import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
from gtts import gTTS
from io import BytesIO
import os
import time
import re

# --------------------------------------------------------------------------
# 1. AYARLAR VE API BAĞLANTISI
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ADÜ - Özel Eğitim Asistanı", 
    page_icon="🇹🇷", 
    layout="wide"
)

if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Sistem Hatası: API anahtarı doğrulanamadı. ({e})")
        st.stop()
else:
    st.error("⚠️ Sistem Hatası: API Anahtarı eksik. Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# --------------------------------------------------------------------------
# 2. AKILLI MODEL DEDEKTİFİ 🕵️‍♂️ (Otomatik En İyi Modeli Bulur)
# --------------------------------------------------------------------------
def en_iyi_modeli_bul():
    """
    Hesabındaki modelleri tarar. 
    Önce '3.0' serisine, yoksa '2.0' serisine bakar. En güncel 'Flash' modelini seçer.
    """
    try:
        mevcut_modeller = [m.name for m in genai.list_models()]
        # Öncelik sırası: En yeni -> En eski
        arananlar = [
            "gemini-3.0-flash", 
            "gemini-3-flash", 
            "gemini-2.0-flash", 
            "gemini-1.5-flash"
        ]
        secilen = None
        for hedef in arananlar:
            for gercek_isim in mevcut_modeller:
                if hedef in gercek_isim:
                    secilen = gercek_isim
                    break
            if secilen: break
            
        if not secilen: secilen = 'gemini-1.5-flash' # Güvenli Liman
        return secilen
    except:
        return 'gemini-1.5-flash'

aktif_model_ismi = en_iyi_modeli_bul()
model_ai = genai.GenerativeModel(aktif_model_ismi)

# --------------------------------------------------------------------------
# 3. PROFESYONEL FONKSİYONLAR (USTA ÖĞRETMEN MODU 🎓)
# --------------------------------------------------------------------------

if 'asama' not in st.session_state: st.session_state.asama = 0
if 'sorular' not in st.session_state: st.session_state.sorular = ""
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'konu' not in st.session_state: st.session_state.konu = ""

def super_temizlik(metin):
    """PDF için karakter temizliği."""
    if not metin: return ""
    degisimler = {
        "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
        "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
        "…": "...", "“": '"', "”": '"', "’": "'", "●": "-", "–": "-", "—": "-"
    }
    for eski, yeni in degisimler.items():
        metin = metin.replace(eski, yeni)
    # Sadece ASCII karakterler kalsın (Emoji temizliği)
    metin = re.sub(r'[^\x00-\x7F]+', '', metin)
    return metin

def yapay_zeka_istegi(prompt, resim=None):
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
                bekleme = (i + 1) * 2 
                st.toast(f"Sistem yoğun, bekleniyor... ({bekleme} sn)")
                time.sleep(bekleme)
                continue
            else:
                return f"Sistem Hatası: {str(e)}"
    return "Sistem şu an yanıt veremiyor."

def soru_uret(konu, sinif, model_tipi, resim=None):
    """
    PROMPT GÜNCELLEMESİ: 20 Yıllık Usta Öğretmen + MEB Ciddiyeti
    """
    prompt = f"""
    ROL: Sen MEB bünyesinde 20 yıl görev yapmış, mevzuatın kitabını yazmış, öğrenci psikolojisini ve gelişimsel süreçleri avucunun içi gibi bilen kıdemli bir 'Başöğretmensin'.
    
    GÖREV: {sinif}. sınıf düzeyindeki özel yetenekli bir öğrenci için, '{konu}' kazanımına yönelik, '{model_tipi}' farklılaştırma modeline uygun 3 adet 'Üst Düzey Düşünme Becerisi' (Analiz, Sentez, Değerlendirme) sorusu hazırla.
    
    ÜSLUP VE KURALLAR:
    1. TAM CİDDİYET: Asla emoji, ünlem (!) veya "Harika!", "Süper!" gibi laubali ifadeler kullanma.
    2. UZMANLIK: Sorular basit bilgi düzeyinde değil, öğrencinin potansiyelini zorlayacak derinlikte olmalıdır.
    3. RESMİYET: Soruları bir sınav kağıdı veya resmi bir değerlendirme formu ciddiyetiyle sun.
    """
    return yapay_zeka_istegi(prompt, resim)

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    """
    PROMPT GÜNCELLEMESİ: Kurul Başkanı Uzmanlığı + Resmi Rapor Dili
    """
    prompt = f"""
    ROL: Sen Özel Eğitim Değerlendirme Kurulunda yıllarca başkanlık yapmış, bir öğrencinin cevabından onun tüm bilişsel haritasını çıkarabilen bir uzmansın.
    
    GÖREV: Aşağıdaki öğrenci cevaplarını, İlçe Milli Eğitim Müdürlüğüne sunulacak resmi bir 'Eğitsel Değerlendirme Raporu' titizliğinde analiz et.
    
    VERİLER:
    - Sorular: {sorular}
    - Cevaplar: {cevaplar}
    - Model: {model_tipi}
    
    RAPOR FORMATI (Aynen bu başlıkları kullan, emoji YASAK):
    
    1. PERFORMANS DUZEYI
    (Öğrencinin mevcut durumu hakkında; 'gözlemlenmiştir', 'tespit edilmiştir' gibi nesnel ve edilgen yargılar kullan.)
    
    2. KAZANIM DEGERLENDIRMESI
    (Cevapların MEB müfredatındaki karşılığını teknik terimlerle açıkla.)
    
    3. GELISIM ALANLARI
    (Eksik veya desteklenmesi gereken noktaları profesyonel bir dille belirt.)
    
    4. ZENGINLESTIRME EYLEM PLANI
    (Bu öğrenci için uygulanabilir, somut ve akademik bir proje/performans görevi öner.)
    
    ÖNEMLİ: Çıktı tamamen bürokratik ve akademik bir dille yazılmalıdır. Sohbet dili kesinlikle kullanılmayacaktır.
    """
    return yapay_zeka_istegi(prompt)

def create_pdf(text, ogrenci_adi, konu):
    # PDF oluştururken temizlik yap
    text = super_temizlik(text)
    ogrenci_adi = super_temizlik(ogrenci_adi)
    konu = super_temizlik(konu)
    
    class PDF(FPDF):
        def header(self):
            if os.path.exists("logo.png"):
                try:
                    self.image('logo.png', 10, 8, 20)
                except: pass
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'TC. ADU OZEL EGITIM HIZMETLERI RAPORU', 0, 1, 'C')
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()} | Resmi Evrak - Gizlidir', 0, 0, 'C')

    try:
        pdf = PDF()
        pdf.add_page()
        font_path = 'arial.ttf'
        if os.path.exists(font_path):
            pdf.add_font('Arial', '', font_path, uni=True)
            pdf.set_font('Arial', '', 11)
        else:
            pdf.set_font("Helvetica", size=11)

        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"Ogrenci: {ogrenci_adi} | Konu: {konu}", 0, 1)
        pdf.line(10, 35, 200, 35)
        pdf.ln(5)
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, text)
        return pdf.output(dest='S').encode('latin-1', 'replace')
    except: return None

def metni_seslendir(text):
    try:
        # Seslendirme için başlık işaretlerini temizle
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
# 4. ARAYÜZ TASARIMI
# --------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=120)
    else: st.write("🇹🇷 ADÜ")
    
    st.markdown("---")
    st.info("**Eray Cangel**\n\nÖzel Eğitim Uzmanı\nNo: 242018077")
    
    # Model Bilgisi
    temiz_isim = aktif_model_ismi.split('/')[-1]
    st.success(f"⚡ **Motor:** {temiz_isim}")
    
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
    st.caption("T.C. Milli Eğitim Bakanlığı Standartlarına Uygun Raporlama Aracı")

st.markdown("---")

if st.session_state.asama == 0:
    st.info(f"📌 **Model:** {egitim_modeli} | **Sınıf:** {sinif}")
    
    uploaded = st.file_uploader("Materyal Görseli (Opsiyonel):", type=["jpg", "png"])
    resim = Image.open(uploaded) if uploaded else None
    if resim: st.image(resim, width=200)

    colA, colB = st.columns([3, 1])
    with colA:
        konu = st.text_input("Kazanım / Konu:", placeholder="Örn: Sürdürülebilir Yaşam")
    with colB:
        st.write("")
        st.write("")
        if st.button("Analizi Başlat", type="primary"):
            if konu:
                with st.spinner("Başöğretmen analizi yapıyor..."):
                    st.session_state.konu = konu
                    st.session_state.sorular = soru_uret(konu, sinif, egitim_modeli, resim)
                    st.session_state.asama = 1
                    st.rerun()

elif st.session_state.asama == 1:
    st.success("Değerlendirme soruları oluşturuldu.")
    st.markdown(st.session_state.sorular)
    with st.form("cevap_form"):
        cvp = st.text_area("Öğrenci Cevapları:", height=150)
        if st.form_submit_button("Rapor Oluştur"):
            if cvp:
                with st.spinner("Resmi rapor düzenleniyor..."):
                    st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cvp, egitim_modeli)
                    st.session_state.asama = 2
                    st.rerun()

elif st.session_state.asama == 2:
    st.markdown(f"### Rapor: {ad}")
    st.markdown(st.session_state.analiz)
    
    c1, c2 = st.columns(2)
    with c1:
        pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
        if pdf_data:
            st.download_button("📄 PDF İndir", data=pdf_data, file_name="Resmi_Rapor.pdf", mime="application/pdf", type="primary")
        else: st.error("PDF hatası.")
    with c2:
        if st.button("🔊 Seslendir"):
            ses = metni_seslendir(st.session_state.analiz)
            if ses: st.audio(ses)
            
    st.markdown("---")
    if st.button("Yeni Analiz"): sifirla()
