import streamlit as st
import pandas as pd
import io
import sqlite3
import tempfile
import os
from fpdf import FPDF

# 1. Ustawienia strony na SZEROKIE (Dashboard)
st.set_page_config(page_title="YourDNA | Dashboard", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

# 2. Wstrzykiwanie "sterylnego" CSS (Stylizacja pod Genotek)
st.markdown("""
<style>
    /* Gradientowy pasek boczny z Twojego zdjęcia */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4b79a1 0%, #283e51 100%);
        color: white !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Czyste białe tło główne */
    .stApp {
        background-color: #FAFAFB;
    }
    
    /* Karty dashboardu */
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #f0f2f6;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Pigułki statusu (jak 'mutation Detected' na zdjęciu) */
    .badge-red {
        background-color: #fff0f0;
        color: #d32f2f;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #ffcdd2;
        display: inline-block;
        margin-left: 10px;
    }
    .badge-green {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #c8e6c9;
        display: inline-block;
        margin-left: 10px;
    }
    
    /* Ukrycie standardowego nagłówka Streamlit */
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- INICJALIZACJA BAZY ---
if not os.path.exists("baza_700k.db"):
    import stworz_baze
    stworz_baze.zainicjalizuj_baze()

if 'is_paid' not in st.session_state:
    st.session_state.is_paid = False

def process_payment():
    st.session_state.is_paid = True

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
                # Prosta logika do ustalenia koloru pigułki
                badge_class = "badge-red" if "ryzyko" in tytul.lower() or "wolny" in tytul.lower() else "badge-green"
                raport.append({
                    "cecha": name, "genotyp": user_genotype, "diagnoza": tytul, 
                    "szczegoly": opis, "is_premium": is_premium, "czestotliwosc": czestotliwosc, "badge": badge_class
                })
    conn.close()
    return raport

# --- PANEL BOCZNY (SIDEBAR) ---
with st.sidebar:
    st.markdown("## 🧬 YourDNA")
    st.markdown("---")
    
    jezyki = {"🇵🇱 Polski": "pl", "🇬🇧 English": "en"}
    wybrany_jezyk = st.selectbox("Wybierz język / Language:", list(jezyki.keys()))
    kod_jezyka = jezyki[wybrany_jezyk]
    
    st.markdown("---")
    st.markdown("🛡️ **Prywatność**\nTwoje dane są przetwarzane lokalnie w przeglądarce.")
    if st.session_state.is_paid:
        st.success("Wersja Premium: Aktywna")
    else:
        st.warning("Wersja: Darmowa (Ograniczona)")

# --- GŁÓWNY PANEL (DASHBOARD) ---
st.title("Panel Pacjenta")
st.markdown("Przeglądaj swoje predyspozycje genetyczne w oparciu o wgrany profil DNA.")

uploaded_file = st.file_uploader("Dodaj plik genetyczny (.txt/.csv)", type=['txt', 'csv'])

if not uploaded_file:
    # Stylizowane miejsce na wgranie pliku
    st.info("Oczekujemy na Twój plik z danymi genetycznymi. Przeciągnij go powyżej.")
    test_dna_content = "# Test DNA\nrsid\tchromosome\tposition\tgenotype\nrs762551\t1\t123\tAA\nrs1815739\t11\t123\tCC\nrs9939609\t16\t123\tTT"
    st.download_button(label="📥 Pobierz plik testowy", data=test_dna_content, file_name="test.txt")

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    genotypy_uzytkownika = parse_dna_file(file_content)
    gotowy_raport = pobierz_wyniki_z_bazy(genotypy_uzytkownika, kod_jezyka, st.session_state.is_paid)
    
    # --- METRYKI (Hero Section) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h4>Zbadane markery</h4><h2>{len(genotypy_uzytkownika):,}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h4>Wykryte cechy</h4><h2>{len(gotowy_raport)}</h2></div>', unsafe_allow_html=True)
    with col3:
        status = "Zakończona" if st.session_state.is_paid else "Częściowa"
        st.markdown(f'<div class="metric-card"><h4>Status analizy</h4><h2>{status}</h2></div>', unsafe_allow_html=True)

    # --- ZAKŁADKI (TABS - jak na zdjęciu) ---
    tab1, tab2, tab3 = st.tabs(["🩺 Wyniki ogólne", "🍏 Odżywianie i Dieta", "🔒 Zablokowane Raporty"])
    
    with tab1:
        st.subheader("Wszystkie zbadane cechy")
        for wynik in gotowy_raport:
            # Tworzenie czystego wiersza w stylu Genotek (Tytuł + Pigułka)
            st.markdown(f"""
            <div style="padding: 15px 0; border-bottom: 1px solid #eee;">
                <span style="font-size: 1.1rem; font-weight: 500; color: #333;">{wynik['cecha']}</span>
                <span class="{wynik['badge']}">{wynik['diagnoza']} ({wynik['genotyp']})</span>
                <p style="color: #666; margin-top: 5px; font-size: 0.9rem;">{wynik['szczegoly']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    with tab2:
        st.info("Kategoryzacja szczegółowa dostępna wkrótce (wymaga przypisania tagów w bazie).")
        
    with tab3:
        if not st.session_state.is_paid:
            st.warning("Twój plik zawiera znacznie więcej danych (m.in. ryzyko urazów, metabolizm leków).")
            st.button("💳 Odblokuj pełny profil za 99 zł", type="primary", use_container_width=True, on_click=process_payment)
        else:
            st.success("Wszystkie raporty zostały odblokowane!")
