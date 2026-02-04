import streamlit as st
import google.generativeai as genai
import os

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="ADÜ - Özel Eğitim Asistanı", 
    layout="wide"
)

# ==========================================
# 🔐 GÜVENLİK AYARI (Cloud İçin)
# ==========================================
# API Anahtarını kodun içinden değil, güvenli kasadan (Secrets) alıyoruz.
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Eğer kasada bulamazsa (veya yereldeysen) hata vermemesi için uyarı gösterir
    st.error("⚠️ API Anahtarı Bulunamadı! Lütfen Streamlit Secrets ayarlarını yapınız.")
    GOOGLE_API_KEY = "" # Boş bırakıyoruz

# ==========================================

# --- BAĞLANTI ---
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        model_ai = genai.GenerativeModel('models/gemini-flash-latest')
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")

# --- HAFIZA ---
if 'asama' not in st.session_state: st.session_state.asama = 0
if 'sorular' not in st.session_state: st.session_state.sorular = ""
if 'analiz' not in st.session_state: st.session_state.analiz = ""
if 'konu' not in st.session_state: st.session_state.konu = ""

# --- FONKSİYONLAR ---
def soru_uret(konu, sinif, model_tipi):
    prompt = f"""
    Sen uzman bir özel eğitim öğretmenisin. 
    Öğrenci: {sinif}. sınıf, üstün yetenekli. Konu: '{konu}'. Yaklaşım: {model_tipi}.
    GÖREV: Bu öğrencinin derinliğini ölçmek için 3 adet yaratıcı, ezber bozan, üst düzey soru hazırla.
    """
    try:
        return model_ai.generate_content(prompt).text
    except:
        return "Yapay zeka şu an cevap veremiyor, lütfen tekrar dene."

def cevap_analiz_et(sorular, cevaplar, model_tipi):
    prompt = f"""
    SORULAR: {sorular}
    CEVAPLAR: {cevaplar}
    GÖREV: Bir mentör gibi analiz et. Rapor dili resmi ve akademik olsun.
    1. Hakimiyet yüzdesi ver.
    2. Eğer %80 üzeriyse '{model_tipi}' modeline uygun YARATICI BİR PROJE GÖREVİ ver.
    3. Eksik varsa belirt.
    """
    try:
        return model_ai.generate_content(prompt).text
    except:
        return "Analiz yapılamadı."

def sifirla():
    st.session_state.asama = 0
    st.session_state.sorular = ""
    st.session_state.analiz = ""
    st.rerun()

# ==========================================
# ARAYÜZ TASARIMI
# ==========================================

# --- YAN MENÜ ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        # Logo yoksa bile uygulama çökmesin diye:
        st.write("ADÜ Özel Eğitim")
    
    st.markdown("---")
    st.markdown("### Hazırlayan")
    st.info("**Eray Cangel**\n\nÖzel Eğitim Öğretmenliği\nNo: 242018077")
    
    st.markdown("---")
    st.header("Öğrenci Ayarları")
    ad = st.text_input("Öğrenci Adı", "Zekeriya Ayral")
    sinif = st.selectbox("Sınıf Seviyesi", [4, 5, 6, 7, 8])
    egitim_modeli = st.selectbox("Model", ["Renzulli (Zenginleştirme)", "SCAMPER (Yaratıcılık)", "Purdue Modeli"])
    
    st.markdown("---")
    if st.button("Yeni Konu / Sıfırla", type="primary"):
        sifirla()

# --- ANA EKRAN ---

col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=80)
with col2:
    st.title("Kişiselleştirilmiş Hızlandırma Planlayıcı")
    st.caption("Adnan Menderes Üniversitesi | Özel Eğitim Bölümü Projesi")

st.markdown("---")

# --- AKIŞ ---

# 1. GİRİŞ
if st.session_state.asama == 0:
    st.markdown(f"""
    ### Hoş Geldiniz.
    Bu sistem, **{egitim_modeli}** modelini temel alarak üstün yetenekli öğrenciler için
    seviye tespiti yapar ve kişiye özel **zenginleştirilmiş rota** oluşturur.
    """)
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        konu_girisi = st.text_input("Hızlandırılacak Konu Başlığı:", placeholder="Örn: Yapay Zeka Etiği, Küresel Isınma...")
    with col_b:
        st.write("") 
        st.write("") 
        if st.button("Soruları Hazırla", type="primary"):
            if not GOOGLE_API_KEY:
                st.error("Sistem Hatası: API Anahtarı Bulunamadı (Secrets ayarını kontrol edin).")
            elif not konu_girisi:
                st.warning("Lütfen bir konu başlığı giriniz.")
            else:
                with st.spinner("Yapay zeka soruları hazırlıyor..."):
                    st.session_state.konu = konu_girisi
                    st.session_state.sorular = soru_uret(konu_girisi, sinif, egitim_modeli)
                    st.session_state.asama = 1
                    st.rerun()

# 2. SINAV
elif st.session_state.asama == 1:
    st.success(f"Konu: **{st.session_state.konu}** için seviye tespit soruları hazırlanmıştır.")
    
    with st.container(border=True):
        st.markdown(st.session_state.sorular)
    
    st.write("### Öğrenci Cevapları")
    with st.form("cevap_formu"):
        cevaplar = st.text_area("Öğrenci cevaplarını buraya giriniz:", height=200, placeholder="Detaylı cevaplar analizin doğruluğunu artırır.")
        
        submitted = st.form_submit_button("Analiz Et ve Rota Oluştur", type="primary")
        if submitted:
            if len(cevaplar) < 5:
                st.error("Lütfen cevap alanını doldurunuz.")
            else:
                with st.spinner("Cevaplar değerlendiriliyor, rapor oluşturuluyor..."):
                    st.session_state.analiz = cevap_analiz_et(st.session_state.sorular, cevaplar, egitim_modeli)
                    st.session_state.asama = 2
                    st.rerun()

# 3. SONUÇ
elif st.session_state.asama == 2:
    st.markdown(f"## Sonuç Raporu: {ad}")
    
    with st.container(border=True):
        st.markdown(st.session_state.analiz)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Raporu İndir (TXT)", st.session_state.analiz, file_name=f"{ad}_Rapor.txt")
    with col2:
        if st.button("Yeni Öğrenci Girişi"):
            sifirla()

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Adnan Menderes Üniversitesi © 2026 | Hazırlayan: Eray Cangel</div>", unsafe_allow_html=True)