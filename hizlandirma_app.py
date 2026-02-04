import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
import os

# --------------------------------------------------------------------------
# 1. AYARLAR VE SAYFA YAPISI
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ADÜ - Özel Eğitim Asistanı", 
    page_icon="🧩", 
    layout="wide"
)

# --------------------------------------------------------------------------
# 2. GÜVENLİK VE BAĞLANTI (API KEY)
# --------------------------------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    try:
        genai.configure(api_key=api_key)
        model_ai = genai.GenerativeModel('gemini-flash-latest') # En hızlı ve güncel model
    except Exception as e:
        st.error(f"API Bağlantı Hatası: {e}")
else:
    st.error("⚠️ API Anahtarı Bulunamadı! Lütfen Streamlit Secrets ayarlarını yapınız.")
    st.stop()

# --------------------------------------------------------------------------
# 3. OTURUM YÖNETİMİ (Session State)
# --------------------------------------------------------------------------
if 'asama' not in st.session_state: st.session_state.asama = 0
if 'sorular' not in st.session_state: st.session_state.sorular = ""
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'konu' not in st.session_state: st.session_state.konu = ""
# Resim verisi session state'de tutulmaz (büyük veri), her seferinde yeniden yüklenir veya akışta kullanılır.

# --------------------------------------------------------------------------
# 4. FONKSİYONLAR (Yapay Zeka ve PDF)
# --------------------------------------------------------------------------

def soru_uret(konu, sinif, model_tipi, resim=None):
    """Öğrenci seviyesini ölçmek için sorular üretir. Resim varsa onu da dikkate alır."""
    prompt_text = f"""
    Sen uzman bir özel eğitim öğretmenisin. 
    Öğrenci: {sinif}. sınıf, üstün yetenekli. Konu: '{konu}'. Yaklaşım: {model_tipi}.
    GÖREV: Bu öğrencinin konu hakkındaki derinliğini ölçmek için 3 adet yaratıcı, ezber bozan, üst düzey soru hazırla.
    
    Eğer bir resim verildiyse, soruları mutlaka o görseldeki içerikle ilişkilendirerek sor.
    Sorular düşündürücü olsun.
    """
    
    try:
        if resim:
            # Resim varsa listeye ekleyip gönderiyoruz
            response = model_ai.generate_content([prompt_text, resim])
        else:
            response = model_ai.generate_content(prompt_text)
        return response.text
    except:
        return "Yapay zeka şu an cevap veremiyor, lütfen tekrar dene."

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    """Öğrencinin cevaplarını analiz eder ve proje önerir."""
    prompt = f"""
    SORULAR: {sorular}
    CEVAPLAR: {cevaplar}
    GÖREV: Bir mentör gibi analiz et. Rapor dili resmi, akademik ve yapıcı olsun.
    1. Konuya hakimiyet yüzdesi ver.
    2. Güçlü ve gelişmeye açık yönleri birer cümleyle yaz.
    3. Eğer %80 üzeriyse '{model_tipi}' modeline uygun YARATICI BİR PROJE GÖREVİ (Somut bir çıktı) ver.
    4. Türkçe karakterlere dikkat et.
    """
    try:
        return model_ai.generate_content(prompt).text
    except:
        return "Analiz yapılamadı."

def create_pdf(text, ogrenci_adi, konu):
    """Türkçe karakter ve sembol destekli PDF oluşturur."""
    
    # --- Metin Temizliği (Sembol Düzeltme) ---
    replacements = {
        "**": "", "__": "", "### ": "", "## ": "", # Markdown temizliği
        "≈": " yaklasik ", "≠": " esit degil ", "≤": " kucuk esit ", "≥": " buyuk esit ",
        "×": "x", "÷": "/", "−": "-", "–": "-", "—": "-", # Matematik sembolleri
        "Δ": "Delta", "π": "Pi", "∑": "Toplam", "∞": "Sonsuz", "√": "karekok",
        "→": "->", "←": "<-", "●": "*"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # --- PDF Sınıfı ---
    class PDF(FPDF):
        def header(self):
            # Logo varsa ekle
            if os.path.exists("logo.png"):
                try:
                    self.image('logo.png', 10, 8, 20) # x, y, w
                    self.set_font('Arial', 'B', 14)
                    self.cell(25) # Logo boşluğu
                    self.cell(0, 10, 'Ozel Egitim Degerlendirme Raporu', 0, 1, 'L')
                except:
                    pass
            else:
                self.set_font('Arial', 'B', 14)
                self.cell(0, 10, 'Ozel Egitim Degerlendirme Raporu', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()} | ADU Ozel Egitim Asistani', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()

    # --- Font Yükleme (Kritik) ---
    font_path = 'arial.ttf'
    if os.path.exists(font_path):
        pdf.add_font('Arial', '', font_path, uni=True)
        pdf.set_font('Arial', '', 11)
    else:
        pdf.set_font("Helvetica", size=11) # Yedek font

    # --- Rapor İçeriği ---
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 10, f"Ogrenci: {ogrenci_adi} | Konu: {konu}", 0, 1)
    pdf.line(10, 35, 200, 35) # Çizgi çek
    pdf.ln(5)
    
    pdf.multi_cell(0, 7, text)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def sifirla():
    st.session_state.asama = 0
    st.session_state.sorular = ""
    st.session_state.analiz = ""
    st.rerun()

# --------------------------------------------------------------------------
# 5. ARAYÜZ (SIDEBAR VE MAIN)
# --------------------------------------------------------------------------

# --- YAN MENÜ ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.write("🧩 ADÜ Özel Eğitim")
    
    st.markdown("---")
    st.markdown("### 🎓 Hazırlayan")
    st.info("**Eray Cangel**\n\nÖzel Eğitim Öğretmenliği\nNo: 242018077")
    
    st.markdown("---")
    st.header("⚙️ Öğrenci Ayarları")
    ad = st.text_input("Öğrenci Adı", "Zekeriya Ayral")
    sinif = st.selectbox("Sınıf Seviyesi", [1, 2, 3, 4, 5, 6, 7, 8])
    egitim_modeli = st.selectbox("Eğitim Modeli", ["Renzulli (Zenginleştirme)", "SCAMPER (Yaratıcılık)", "Purdue Modeli"])
    
    st.markdown("---")
    if st.button("🔄 Yeni Konu / Sıfırla", type="primary"):
        sifirla()

# --- ANA EKRAN ---
col_main_1, col_main_2 = st.columns([1, 6])
with col_main_1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=100)
    else:
        st.write("🧩")
with col_main_2:
    st.title("Kişiselleştirilmiş Hızlandırma Planlayıcı")
    st.caption("Adnan Menderes Üniversitesi | Özel Eğitim Bölümü Projesi")

st.markdown("---")

# --------------------------------------------------------------------------
# 6. AKIŞ MANTIĞI (AŞAMALAR)
# --------------------------------------------------------------------------

# AŞAMA 0: GİRİŞ
if st.session_state.asama == 0:
    st.info(f"📌 **Seçilen Model:** {egitim_modeli} | **Sınıf:** {sinif}")
    st.markdown("""
    Bu sistem, üstün yetenekli öğrenciler için seviye tespiti yapar ve 
    kişiye özel **zenginleştirilmiş rota** oluşturur.
    """)
    
    # --- YENİ EKLENEN KISIM: RESİM YÜKLEME ---
    uploaded_file = st.file_uploader("Varsa bir görsel yükleyin (Örn: Öğrenci resmi, çalışma kağıdı, RAM raporu)", type=["jpg", "jpeg", "png"])
    resim_goster = None
    if uploaded_file is not None:
        resim_goster = Image.open(uploaded_file)
        st.image(resim_goster, caption='Yüklenen Görsel', width=250)
    # -----------------------------------------

    col_a, col_b = st.columns([3, 1])
    with col_a:
        konu_girisi = st.text_input("Hızlandırılacak Konu Başlığı:", placeholder="Örn: Yapay Zeka Etiği, Küresel Isınma, Uzay...")
    with col_b:
        st.write("") 
        st.write("") 
        if st.button("Soruları Hazırla 🚀", type="primary"):
            if not konu_girisi:
                st.warning("Lütfen bir konu başlığı giriniz.")
            else:
                with st.spinner("Yapay zeka pedagojik analiz yapıyor..."):
                    st.session_state.konu = konu_girisi
                    # Resmi de fonksiyona gönderiyoruz
                    st.session_state.sorular = soru_uret(konu_girisi, sinif, egitim_modeli, resim_goster)
                    st.session_state.asama = 1
                    st.rerun()

# AŞAMA 1: SINAV
elif st.session_state.asama == 1:
    st.success(f"✅ Konu: **{st.session_state.konu}** için seviye tespit soruları hazır.")
    
    with st.container(border=True):
        st.markdown("### 📝 Sorular")
        st.markdown(st.session_state.sorular)
    
    st.write("### ✍️ Öğrenci Cevapları")
    with st.form("cevap_formu"):
        cevaplar = st.text_area("Öğrenci cevaplarını buraya giriniz:", height=200, placeholder="Ne kadar detaylı cevap, o kadar iyi analiz...")
        
        submitted = st.form_submit_button("Analiz Et ve Rota Oluştur 🎯", type="primary")
        if submitted:
            if len(cevaplar) < 5:
                st.error("Lütfen cevap alanını doldurunuz.")
            else:
                with st.spinner("Cevaplar değerlendiriliyor, rapor yazılıyor..."):
                    st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cevaplar, egitim_modeli)
                    st.session_state.asama = 2
                    st.rerun()

# AŞAMA 2: SONUÇ VE PDF
elif st.session_state.asama == 2:
    st.markdown(f"## 📋 Sonuç Raporu: {ad}")
    
    with st.container(border=True):
        st.markdown(st.session_state.analiz)
    
    col_res_1, col_res_2 = st.columns(2)
    with col_res_1:
        # --- PDF İNDİRME ---
        try:
            pdf_data = create_pdf(st.session_state.analiz, ad, st.session_state.konu)
            st.download_button(
                label="📄 Raporu PDF Olarak İndir",
                data=pdf_data,
                file_name=f"{ad}_{st.session_state.konu}_Rapor.pdf",
                mime="application/pdf",
                type="primary"
            )
        except Exception as e:
            st.error(f"PDF oluşturulamadı: {e}")
            
    with col_res_2:
        if st.button("Başka Bir Konuya Geç"):
            sifirla()

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey; font-size: 0.8em;'>Adnan Menderes Üniversitesi © 2026 | Developed by Gemini & Eray</div>", unsafe_allow_html=True)
