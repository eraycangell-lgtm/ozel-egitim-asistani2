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
# 4. FONKSİYONLAR (MEB DİLİ + SESLENDİRME + GÜVENLİ PDF 🛠️)
# --------------------------------------------------------------------------

def metni_seslendir(text):
    """Metni sese çevirir ve oynatılabilir veri döndürür."""
    try:
        # Metindeki emojileri ve garip işaretleri temizle ki okurken takılmasın
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
    ROL: Sen T.C. Milli Eğitim Bakanlığı (MEB) mevzuatına, Özel Eğitim Hizmetleri Yönetmeliğine ve BİLSEM yönergelerine hakim, kıdemli bir özel eğitim uzmanısın.
    
    DURUM:
    - Öğrenci: {sinif}. sınıf, özel yetenekli tanılı.
    - Konu/Kazanım: '{konu}'
    - Kullanılacak Farklılaştırma Modeli: {model_tipi}
    
    GÖREV: 
    Öğrencinin hazırbulunuşluk düzeyini belirlemek amacıyla, seçilen '{model_tipi}' yaklaşımına uygun 3 adet 'Üst Düzey Düşünme Becerisi' sorusu hazırla.
    
    TALİMATLAR:
    1. Dil kullanımı tamamiyle resmi, akademik ve MEB terminolojisine (Kazanım, Gösterge, Performans) uygun olsun.
    2. Sorular Bloom Taksonomisinin analiz, sentez ve değerlendirme basamaklarında olsun.
    3. Eğer görsel veri verildiyse, sorulardan en az biri görseli yorumlamaya dayalı olsun.
    """
    try:
        if resim:
            response = model_ai.generate_content([prompt_text, resim])
        else:
            response = model_ai.generate_content(prompt_text)
        return response.text
    except:
        return "MEB sunucuları yoğunluğu gibi bir hata oluştu. Lütfen tekrar deneyin."

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    """Cevapları BEP ve RAM standartlarına göre raporlar."""
    prompt = f"""
    GÖREV: Aşağıdaki öğrenci cevaplarını bir 'Bireyselleştirilmiş Eğitim Programı (BEP) Geliştirme Birimi' üyesi ciddiyetiyle analiz et.
    
    VERİLER:
    - Sorular: {sorular}
    - Öğrenci Cevapları: {cevaplar}
    - Uygulanan Model: {model_tipi}
    
    ÇIKTI FORMATI (Lütfen bu resmi formatı kullan):
    
    1. 📊 PERFORMANS DÜZEYİ: (Öğrencinin mevcut durumu, bağımsız yapabilirlik seviyesi.)
    2. ✅ KAZANIM DEĞERLENDİRMESİ: (Güçlü yönlerin MEB diliyle ifadesi.)
    3. 🚀 GELİŞİM ALANLARI: (Desteklenmesi gereken noktalar.)
    4. 🎯 ZENGİNLEŞTİRME EYLEM PLANI:
       - '{model_tipi}' stratejisine uygun, somut bir 'Performans Görevi' veya 'Proje Tabanlı Öğrenme' önerisi.
       - Bu görev hangi disiplinlerarası beceriyi hedefler?
    
    ÖNEMLİ: Senli-benli konuşma. Rapor dili kullan. Türkçe karakterlere dikkat et.
    """
    try:
        return model_ai.generate_content(prompt).text
    except:
        return "Rapor oluşturulamadı."

def create_pdf(text, ogrenci_adi, konu):
    """MEB Logolu PDF Çıktısı - Dosya Tabanlı Güvenli Yöntem"""
    
    # Emojileri temizle (PDF'te bozuk çıkmasın)
    replacements = {
        "**": "", "__": "", "### ": "", "## ": "",
        "📊": "", "✅": "", "🚀": "", "🎯": "", 
        "≈": " yaklasik ", "≠": " esit degil ", "≤": " kucuk esit ", "≥": " buyuk esit ",
        "×": "x", "÷": "/", "−": "-", "–": "-", "—": "-"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    class PDF(FPDF):
        def header(self):
            if os.path.exists("logo.png"):
                try:
                    self.image('logo.png', 10, 8, 20)
                    self.set_font('Arial', 'B', 12)
                    self.cell(25)
                    self.cell(0, 10, 'TC. ADU OZEL EGITIM PLANLAMA RAPORU', 0, 1, 'L')
                except: pass
            else:
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'TC. OZEL EGITIM PLANLAMA RAPORU', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()} | Resmi Hizmete Ozeldir', 0, 0, 'C')

    # PDF Nesnesi Oluştur
    pdf = PDF()
    pdf.add_page()
    
    # Font Yükleme (Arial)
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
    
    # --- KRİTİK DÜZELTME: Dosyaya yazıp okuma yöntemi ---
    # Bu yöntem 'latin-1' hatasını kesin olarak çözer.
    temp_filename = "gecici_rapor.pdf"
    pdf.output(temp_filename)
    
    with open(temp_filename, "rb") as f:
        pdf_bytes = f.read()
        
    # Geçici dosyayı sil (temizlik)
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    return pdf_bytes

def sifirla():
    st.session_state.asama = 0
    st.session_state.sorular = ""
    st.session_state.analiz = ""
    st.rerun()

# --------------------------------------------------------------------------
# 5. ARAYÜZ
# --------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.write("🇹🇷 MEB/ADÜ")
    st.markdown("---")
    st.info("**Eray Cangel**\n\nÖzel Eğitim Uzmanı\nNo: 242018077")
    st.markdown("---")
    st.header("📋 Öğrenci Bilgileri")
    ad = st.text_input("Adı Soyadı", "Zekeriya Ayral")
    sinif = st.selectbox("Sınıf Seviyesi", [1, 2, 3, 4, 5, 6, 7, 8])
    egitim_modeli = st.selectbox("Farklılaştırma Modeli", ["Renzulli (Üçlü Halka)", "SCAMPER (Yaratıcılık)", "Purdue Modeli"])
    st.markdown("---")
    if st.button("🔄 Yeni Analiz", type="primary"):
        sifirla()

col_main_1, col_main_2 = st.columns([1, 6])
with col_main_1:
    if os.path.exists("logo.png"): st.image("logo.png", width=100)
    else: st.write("🇹🇷")
with col_main_2:
    st.title("Bireyselleştirilmiş Hızlandırma Asistanı")
    st.caption("Milli Eğitim Bakanlığı Standartlarına Uygun Dijital Raporlama Aracı")

st.markdown("---")

if st.session_state.asama == 0:
    st.info(f"📌 **Seçilen Model:** {egitim_modeli} | **Sınıf:** {sinif}")
    st.markdown("""
    Bu sistem, **Özel Eğitim Hizmetleri Yönetmeliği** kapsamında, özel yetenekli öğrencilerin 
    hazırbulunuşluk düzeyini belirlemek ve **BEP** uyumlu zenginleştirme yapmak için tasarlanmıştır.
    """)
    uploaded_file = st.file_uploader("Varsa materyal/çalışma görseli yükleyiniz:", type=["jpg", "jpeg", "png"])
    resim_goster = None
    if uploaded_file is not None:
        resim_goster = Image.open(uploaded_file)
        st.image(resim_goster, caption='Materyal', width=250)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        konu_girisi = st.text_input("Kazanım / Konu Başlığı:", placeholder="Örn: Fen Bilimleri - Sürdürülebilirlik")
    with col_b:
        st.write("") 
        st.write("") 
        if st.button("Analizi Başlat 🚀", type="primary"):
            if not konu_girisi:
                st.warning("Lütfen bir konu/kazanım giriniz.")
            else:
                with st.spinner("MEB Müfredatına uygun sorular hazırlanıyor..."):
                    st.session_state.konu = konu_girisi
                    st.session_state.sorular = soru_uret(konu_girisi, sinif, egitim_modeli, resim_goster)
                    st.session_state.asama = 1
                    st.rerun()

elif st.session_state.asama == 1:
    st.success(f"✅ **{st.session_state.konu}** konusu için tespit soruları oluşturuldu.")
    with st.container(border=True):
        st.markdown("### 📝 Performans Belirleme Soruları")
        st.markdown(st.session_state.sorular)
    st.write("### ✍️ Öğrenci Dönütleri")
    with st.form("cevap_formu"):
        cevaplar = st.text_area("Öğrenci cevaplarını giriniz:", height=200)
        submitted = st.form_submit_button("BEP Raporunu Oluştur 🎯", type="primary")
        if submitted:
            if len(cevaplar) < 5:
                st.error("Lütfen cevap giriniz.")
            else:
                with st.spinner("Kurul değerlendirmesi yapılıyor..."):
                    st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cevaplar, egitim_modeli)
                    st.session_state.asama = 2
                    st.rerun()

elif st.session_state.asama == 2:
    st.markdown(f"## 📋 Resmi Değerlendirme Raporu: {ad}")
    
    with st.container(border=True):
        st.markdown(st.session_state.analiz)
    
    col_res_1, col_res_2 = st.columns(2)
    with col_res_1:
        # PDF BUTONU
        try:
            pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
            st.download_button(
                label="📄 Resmi Raporu İndir (PDF)",
                data=pdf_data,
                file_name=f"MEB_Ozel_Egitim_Rapor_{ad}.pdf",
                mime="application/pdf",
                type="primary"
            )
        except Exception as e:
            st.error(f"PDF Hatası: {e}")
            
    with col_res_2:
        # SESLİ OKUMA BUTONU
        if st.button("🔊 Raporu Sesli Dinle"):
            with st.spinner("Ses dosyası hazırlanıyor..."):
                ses = metni_seslendir(st.session_state.analiz)
                if ses:
                    st.audio(ses, format='audio/mp3')
                else:
                    st.error("Ses oluşturulamadı.")
    
    st.markdown("---")
    if st.button("Yeni Öğrenci / Konu"):
        sifirla()

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey; font-size: 0.8em;'>T.C. Milli Eğitim Bakanlığı Standartlarına Uygun | 2026</div>", unsafe_allow_html=True)
