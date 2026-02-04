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
        
        # --- MODEL SEÇİMİ: GEMINI 3 FLASH ⚡ ---
        # Önce standart ismi dener, olmazsa preview (ön izleme) ismini dener.
        # Bu sayede Google isim değişikliği yapsa bile kodun çalışmaya devam eder.
        try:
            model_ai = genai.GenerativeModel('gemini-3.0-flash')
        except:
            model_ai = genai.GenerativeModel('gemini-3.0-flash-preview')
            
    except Exception as e:
        st.error(f"Sistem Hatası: API anahtarı doğrulanamadı. ({e})")
        st.stop()
else:
    st.error("⚠️ Sistem Hatası: API Anahtarı eksik. Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# Session State (Hafıza) Tanımları
if 'asama' not in st.session_state: st.session_state.asama = 0
if 'sorular' not in st.session_state: st.session_state.sorular = ""
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'konu' not in st.session_state: st.session_state.konu = ""

# --------------------------------------------------------------------------
# 2. GÜÇLENDİRİLMİŞ FONKSİYONLAR 🛠️
# --------------------------------------------------------------------------

def super_temizlik(metin):
    """
    PDF oluştururken 'Latin-1' hatasını önlemek için metni temizler.
    Türkçe karakterleri korur, emojileri ve bozuk sembolleri atar.
    """
    if not metin: return ""
    
    # Riskli karakterleri güvenli hale getir
    degisimler = {
        "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
        "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
        "…": "...", "“": '"', "”": '"', "’": "'", "●": "*", "–": "-", "—": "-"
    }
    for eski, yeni in degisimler.items():
        metin = metin.replace(eski, yeni)
        
    # Regex ile sadece okunabilir karakterleri tut (Emoji temizliği)
    metin = re.sub(r'[^\x00-\x7F]+', '', metin)
    return metin

def yapay_zeka_istegi(prompt, resim=None):
    """
    Yapay zekaya istek atar. Hata alırsa (Kota vb.) 3 kereye kadar tekrar dener.
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
            # Kota/Hız hatası varsa bekle
            if "429" in hata or "quota" in hata:
                bekleme = (i + 1) * 2 
                st.toast(f"Sistem yoğun, bekleniyor... ({bekleme} sn)")
                time.sleep(bekleme)
                continue
            else:
                # Model ismi bulunamazsa kullanıcıya bilgi ver
                if "not found" in hata:
                     return "⚠️ Model Hatası: 'gemini-3.0-flash' ismi sistemde farklı olabilir. Lütfen geliştirici ile iletişime geçin."
                return f"Beklenmedik Hata: {str(e)}"
                
    return "⚠️ Sistem şu an cevap veremiyor. Lütfen daha sonra tekrar deneyiniz."

def soru_uret(konu, sinif, model_tipi, resim=None):
    """MEB Mevzuatına uygun, Başöğretmen kimliğiyle soru üretir."""
    prompt = f"""
    ROL: Sen T.C. Milli Eğitim Bakanlığı (MEB) mevzuatına, Özel Eğitim Hizmetleri Yönetmeliğine ve BİLSEM yönergelerine hakim, kıdemli bir özel eğitim uzmanısın (Başöğretmen).
    
    DURUM:
    - Öğrenci: {sinif}. sınıf düzeyinde, özel yetenekli tanısı almış.
    - Konu/Kazanım: '{konu}'
    - Kullanılacak Farklılaştırma Modeli: {model_tipi}
    
    GÖREV: 
    Öğrencinin hazırbulunuşluk düzeyini belirlemek amacıyla, seçilen '{model_tipi}' yaklaşımına uygun 3 adet 'Üst Düzey Düşünme Becerisi' (Analiz, Sentez, Değerlendirme) sorusu hazırla.
    
    TALİMATLAR:
    1. Dil kullanımı tamamiyle resmi, akademik ve MEB terminolojisine (Kazanım, Gösterge, Performans) uygun olsun.
    2. Sorular doğrudan konunun derinliğini ölçsün.
    3. Eğer görsel veri verildiyse, sorulardan en az biri görseli yorumlamaya dayalı olsun.
    """
    return yapay_zeka_istegi(prompt, resim)

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    """Öğrenci cevabını analiz eder ve Resmi Rapor formatında döner."""
    prompt = f"""
    GÖREV: Aşağıdaki öğrenci cevaplarını bir 'Özel Eğitim Değerlendirme Kurulu' üyesi ciddiyetiyle analiz et.
    
    VERİLER:
    - Sorular: {sorular}
    - Öğrenci Cevapları: {cevaplar}
    - Uygulanan Model: {model_tipi}
    
    ÇIKTI FORMATI (Lütfen bu resmi başlıkları kullan):
    
    1. 📊 PERFORMANS DÜZEYİ: (Öğrencinin mevcut durumu, bağımsız yapabilirlik seviyesi.)
    2. ✅ KAZANIM DEĞERLENDİRMESİ: (Güçlü yönlerin MEB diliyle ifadesi.)
    3. 🚀 GELİŞİM ALANLARI: (Desteklenmesi gereken noktalar.)
    4. 🎯 ZENGİNLEŞTİRME EYLEM PLANI:
       - '{model_tipi}' stratejisine uygun, somut bir 'Performans Görevi' veya 'Proje Tabanlı Öğrenme' önerisi.
       - Bu görev hangi disiplinlerarası beceriyi hedefler?
    
    ÖNEMLİ: Senli-benli konuşma. Resmi rapor dili kullan.
    """
    return yapay_zeka_istegi(prompt)

def create_pdf(text, ogrenci_adi, konu):
    """PDF Oluşturucu (Çökme Korumalı)"""
    # 1. Metni temizle
    text = super_temizlik(text)
    ogrenci_adi = super_temizlik(ogrenci_adi)
    konu = super_temizlik(konu)
    
    class PDF(FPDF):
        def header(self):
            # Logo varsa ekle
            if os.path.exists("logo.png"):
                try:
                    self.image('logo.png', 10, 8, 20)
                    self.set_font('Arial', 'B', 12)
                    self.cell(25)
                    self.cell(0, 10, 'TC. ADU OZEL EGITIM RAPORU', 0, 1, 'L')
                except: pass
            else:
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'TC. OZEL EGITIM PLANLAMA RAPORU', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()} | Resmi Hizmete Ozeldir', 0, 0, 'C')

    try:
        pdf = PDF()
        pdf.add_page()
        
        # Font Yükleme (Arial varsa kullan, yoksa Helvetica)
        font_path = 'arial.ttf'
        if os.path.exists(font_path):
            pdf.add_font('Arial', '', font_path, uni=True)
            pdf.set_font('Arial', '', 11)
        else:
            pdf.set_font("Helvetica", size=11)

        # Başlık Bilgileri
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"Ogrenci: {ogrenci_adi} | Konu: {konu}", 0, 1)
        pdf.line(10, 35, 200, 35) # Ayırıcı çizgi
        pdf.ln(5)
        
        # Rapor Metni
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 7, text)
        
        # Çıktıyı güvenli şekilde oluştur (latin-1 replace)
        return pdf.output(dest='S').encode('latin-1', 'replace')
    except: 
        return None

def metni_seslendir(text):
    """Metni sese çevirir (gTTS)"""
    try:
        # Okumayı zorlaştıracak işaretleri temizle
        temiz = text.replace("*", "").replace("#", "").replace("📊", "").replace("✅", "")
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
# 3. ARAYÜZ TASARIMI
# --------------------------------------------------------------------------

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=120)
    else: 
        st.write("🇹🇷 ADÜ")
        
    st.markdown("---")
    st.info("**Eray Cangel**\n\nÖzel Eğitim Uzmanı\nNo: 242018077")
    
    st.markdown("---")
    st.header("📋 Öğrenci Bilgileri")
    ad = st.text_input("Adı Soyadı", "Zekeriya Ayral")
    sinif = st.selectbox("Sınıf Seviyesi", [1, 2, 3, 4, 5, 6, 7, 8])
    egitim_modeli = st.selectbox("Farklılaştırma Modeli", ["Renzulli (Üçlü Halka)", "SCAMPER (Yaratıcılık)", "Purdue Modeli"])
    
    st.markdown("---")
    if st.button("🔄 Yeni Analiz / Sıfırla", type="primary"): 
        sifirla()

# --- ANA EKRAN ---
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("logo.png"): st.image("logo.png", width=80)
    else: st.write("🇹🇷")
with col2:
    st.title("Özel Eğitim Asistanı")
    st.caption("T.C. Milli Eğitim Bakanlığı Standartlarına Uygun Raporlama ve Analiz Aracı")

st.markdown("---")

# --- AKIŞ MANTIĞI ---

# AŞAMA 0: GİRİŞ VE SORU ÜRETME
if st.session_state.asama == 0:
    st.info(f"📌 **Seçilen Model:** {egitim_modeli} | **Sınıf:** {sinif}")
    
    # Görsel Yükleme Alanı
    uploaded_file = st.file_uploader("Varsa materyal/çalışma görseli yükleyiniz (Opsiyonel):", type=["jpg", "png", "jpeg"])
    resim = Image.open(uploaded_file) if uploaded_file else None
    if resim: st.image(resim, width=250, caption="Analize eklenecek görsel")

    colA, colB = st.columns([3, 1])
    with colA:
        konu = st.text_input("Kazanım / Konu Başlığı:", placeholder="Örn: Sürdürülebilir Enerji Kaynakları")
    with colB:
        st.write("")
        st.write("")
        if st.button("Analizi Başlat 🚀", type="primary"):
            if konu:
                with st.spinner("Gemini 3 Flash (Yüksek Performans) Modeli Analiz Yapıyor..."):
                    st.session_state.konu = konu
                    st.session_state.sorular = soru_uret(konu, sinif, egitim_modeli, resim)
                    st.session_state.asama = 1
                    st.rerun()
            else:
                st.warning("Lütfen bir konu başlığı giriniz.")

# AŞAMA 1: CEVAPLARI ALMA
elif st.session_state.asama == 1:
    st.success("✅ Performans belirleme soruları hazır.")
    st.markdown(st.session_state.sorular)
    
    with st.form("cevap_form"):
        cvp = st.text_area("Öğrenci Cevaplarını Giriniz:", height=150, placeholder="Öğrencinin verdiği cevapları buraya not ediniz...")
        if st.form_submit_button("Raporu Oluştur 🎯", type="primary"):
            if cvp:
                with st.spinner("Resmi rapor yazılıyor..."):
                    st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cvp, egitim_modeli)
                    st.session_state.asama = 2
                    st.rerun()
            else:
                st.error("Lütfen cevap alanını boş bırakmayınız.")

# AŞAMA 2: SONUÇ VE ÇIKTILAR
elif st.session_state.asama == 2:
    st.markdown(f"### 📋 Resmi Değerlendirme Raporu: {ad}")
    st.markdown(st.session_state.analiz)
    
    c1, c2 = st.columns(2)
    with c1:
        # PDF Butonu
        pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
        if pdf_data:
            st.download_button("📄 Raporu PDF Olarak İndir", data=pdf_data, file_name=f"Rapor_{ad}.pdf", mime="application/pdf", type="primary")
        else: st.error("PDF oluşturulamadı.")
            
    with c2:
        # Ses Butonu
        if st.button("🔊 Raporu Sesli Dinle"):
            with st.spinner("Seslendiriliyor..."):
                ses = metni_seslendir(st.session_state.analiz)
                if ses: st.audio(ses, format='audio/mp3')
    
    st.markdown("---")
    if st.button("Yeni Öğrenci / Konu"): sifirla()
