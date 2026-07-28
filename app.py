import streamlit as st
import pandas as pd
import io
import sqlite3
import tempfile
import os

# --- USTAWIENIA STRONY ---
st.set_page_config(page_title="YourDNA | Panel", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

# --- SŁOWNIK UI (TŁUMACZENIA) ---
ui = {
    "pl": {
        "slogan": "Odkryj swój kod",
        "upload_title": "Wgraj plik sekwencjonowania",
        "upload_desc": "Obsługiwane formaty: TXT, CSV (m.in. 23andMe, AncestryDNA, MyHeritage)",
        "premium_btn": "💳 Odblokuj pełny profil - 99 zł",
        "no_file": "Nie posiadasz własnego pliku DNA? Pobierz plik demonstracyjny poniżej.",
        "demo_btn": "📥 Pobierz plik demonstracyjny"
    },
    "en": {
        "slogan": "Discover your code",
        "upload_title": "Upload sequencing file",
        "upload_desc": "Supported formats: TXT, CSV (e.g., 23andMe, AncestryDNA, MyHeritage)",
        "premium_btn": "💳 Unlock full profile - 25 EUR",
        "no_file": "Don't have your own DNA file? Download the demo file below.",
        "demo_btn": "📥 Download demo file"
    }
}

# --- INICJALIZACJA BAZY I SESJI ---
if not os.path.exists("baza_700k.db"):
    import stworz_baze
    stworz_baze.zainicjalizuj_baze()

if 'is_paid' not in st.session_state:
    st.session_state.is_paid = False

def process_payment():
    st.session_state.is_paid = True

# --- ZAAWANSOWANY CSS (GRADIENTY I STYLIZACJA) ---
st.markdown("""
<style>
    /* Nowoczesny gradient na pasku bocznym */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        border-right: 1px solid #cbd5e1;
    }
    
    /* Globalny styl czcionek i tła */
    .stApp { background-color: #f7f9fc; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Karty wyników */
    .dashboard-card {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 24px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 20px;
    }
    
    /* Pigułki statusu */
    .badge-red { background-color: #fee2e2; color: #ef4444; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    .badge-green { background-color: #dcfce7; color: #22c55e; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    
    /* Magia CSS: Stylowanie głównego przycisku Premium (Gradient i animacja) */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(99, 102, 241, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- FUNKCJE LOGIKI ---
def parse_dna_file(file_content):
    lines = [line for line in file_content.split('\n') if not line.startswith('#') and line.strip()]
    df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', header=None, names=['rsid', 'chromosome', 'position', 'genotype'], dtype=str, on_bad_lines='skip')
    return dict(zip(df.rsid, df.genotype.str.replace(" ", "").str.upper()))

def pobierz_wyniki_z_bazy(user_snps, jezyk="pl", has_paid=False):
    conn = sqlite3.connect("baza_700k.db")
    cursor = conn.cursor()
    raport = []
    for rsid, user_genotype in user_snps.items():
        cursor.execute("SELECT name, is_premium, czestotliwosc FROM snp_database WHERE rsid = ?", (rsid,))
        snp_info = cursor.fetchone()
        if snp_info:
            name, is_premium, czestotliwosc = snp_info
            if is_premium and not has_paid:
                continue
            cursor.execute("SELECT tytul, opis FROM tlumaczenia_genow WHERE rsid = ? AND jezyk = ? AND genotyp = ?", (rsid, jezyk, user_genotype))
            diag_info = cursor.fetchone()
            if diag_info:
                tytul, opis = diag_info
                badge_class = "badge-red" if "ryzyko" in tytul.lower() or "wolny" in tytul.lower() or "słaba" in tytul.lower() else "badge-green"
                raport.append({"cecha": name, "genotyp": user_genotype, "diagnoza": tytul, "szczegoly": opis, "badge": badge_class})
    conn.close()
    return raport

# --- PANEL BOCZNY (SIDEBAR) ---
with st.sidebar:
    jezyki = {"🇵🇱 Polski": "pl", "🇬🇧 English": "en"}
    wybrany_jezyk = st.selectbox("🌍 Wybierz język / Language:", list(jezyki.keys()))
    kod_jezyka = jezyki[wybrany_jezyk]
    t = ui[kod_jezyka]
    
    # Dynamiczny, poprawny nagłówek
    st.markdown(f"## 🧬 YourDNA\n*{t['slogan']}*")
    st.markdown("---")
    
    # Przycisk Premium ZAWSZE WIDOCZNY z gradientem
    if not st.session_state.is_paid:
        st.button(t["premium_btn"], on_click=process_payment)
        st.caption("🔒 Odblokuj ukryte geny, predyspozycje do chorób i pełen raport dietetyczny.")
    else:
        st.success("✅ Wersja Premium aktywna")

# --- GŁÓWNY PANEL (DASHBOARD) ---
st.title("Panel Zdrowia i Predyspozycji")

# Uploader
st.markdown(f"#### {t['upload_title']}")
st.caption(t['upload_desc'])
uploaded_file = st.file_uploader("", type=['txt', 'csv'], label_visibility="collapsed")

if not uploaded_file:
    st.info(f"**{t['no_file']}**")
    test_dna_content = "# Test DNA\nrsid\tchromosome\tposition\tgenotype\nrs762551\t1\t123\tAA\nrs1815739\t11\t123\tCC\nrs9939609\t16\t123\tTT"
    st.download_button(label=t["demo_btn"], data=test_dna_content, file_name="demo_dna.txt")

# Wyświetlanie wyników
if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    genotypy_uzytkownika = parse_dna_file(file_content)
    gotowy_raport = pobierz_wyniki_z_bazy(genotypy_uzytkownika, kod_jezyka, st.session_state.is_paid)
    
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🩺 Wykryte Markery", "🍏 Dieta i Sport", "🔒 Raport Rozszerzony"])
    
    with tab1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        for wynik in gotowy_raport:
            st.markdown(f"""
            <div style="padding-bottom: 15px;">
                <span style="font-size: 1.1rem; font-weight: 600; color: #0f172a;">{wynik['cecha']}</span>
                <span class="{wynik['badge']}">{wynik['diagnoza']} ({wynik['genotyp']})</span>
                <p style="color: #64748b; margin-top: 8px; font-size: 0.95rem;">{wynik['szczegoly']}</p>
            </div>
            <hr style='margin: 15px 0; border: none; border-top: 1px solid #f1f5f9;'>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
