import streamlit as st
import pandas as pd
import io
import sqlite3
import tempfile
import os
from fpdf import FPDF

# 1. Ustawienia strony
st.set_page_config(page_title="YourDNA | Panel Pacjenta", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

# 2. CSS z powrotem dodający piękne cienie i sterylny wygląd
st.markdown("""
<style>
    /* Białe Karty z miękkim cieniem (Dla wyników) */
    .dashboard-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); /* Dodany delikatny cień! */
        margin-bottom: 20px;
    }
    
    /* Pigułki statusu */
    .badge-red {
        background-color: #fee2e2; color: #ef4444; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; margin-left: 10px; border: 1px solid #fca5a5;
    }
    .badge-green {
        background-color: #dcfce7; color: #22c55e; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-block; margin-left: 10px; border: 1px solid #86efac;
    }
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
                badge_class = "badge-red" if "ryzyko" in tytul.lower() or "wolny" in tytul.lower() or "słaba" in tytul.lower() else "badge-green"
                raport.append({
                    "cecha": name, "genotyp": user_genotype, "diagnoza": tytul, 
                    "szczegoly": opis, "is_premium": is_premium, "czestotliwosc": czestotliwosc, "badge": badge_class
                })
    conn.close()
    return raport

# --- PANEL BOCZNY (SIDEBAR) ---
with st.sidebar:
    st.markdown("## 🧬 Genomika")
    st.markdown("---")
    
    jezyki = {"🇵🇱 Polski": "pl", "🇬🇧 English": "en"}
    wybrany_jezyk = st.selectbox("Wybierz język / Language:", list(jezyki.keys()))
    kod_jezyka = jezyki[wybrany_jezyk]
    
    st.markdown("---")
    st.markdown("🛡️ **Prywatność i Bezpieczeństwo**\n\nTwoje dane nie opuszczają tej przeglądarki.")
    
    if st.session_state.is_paid:
        st.success("● Wersja Pełna")
    else:
        st.warning("● Wersja Podstawowa")

# --- GŁÓWNY PANEL (DASHBOARD) ---
st.title("Panel Zdrowia i Predyspozycji")

st.markdown("#### Wgraj plik sekwencjonowania")
st.caption("Obsługiwane formaty: TXT, CSV (m.in. 23andMe, AncestryDNA, MyHeritage)")
uploaded_file = st.file_uploader("", type=['txt', 'csv'], label_visibility="collapsed")

if not uploaded_file:
    st.info("**Nie posiadasz własnego pliku DNA?** Pobierz plik demonstracyjny poniżej, aby przetestować system.")
    test_dna_content = "# Test DNA\nrsid\tchromosome\tposition\tgenotype\nrs762551\t1\t123\tAA\nrs1815739\t11\t123\tCC\nrs9939609\t16\t123\tTT"
    st.download_button(label="📥 Pobierz plik demonstracyjny", data=test_dna_content, file_name="demo_dna.txt")

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    genotypy_uzytkownika = parse_dna_file(file_content)
    gotowy_raport = pobierz_wyniki_z_bazy(genotypy_uzytkownika, kod_jezyka, st.session_state.is_paid)
    
    st.markdown("---")
    
    # --- ZAKŁADKI (TABS) ---
    tab1, tab2, tab3 = st.tabs(["🩺 Wykryte Markery", "🍏 Dieta i Sport", "🔒 Raport Rozszerzony"])
    
    with tab1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("Wszystkie zbadane cechy")
        st.caption("Poniżej znajduje się lista zidentyfikowanych wariantów genetycznych.")
        st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)
        
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
            
    with tab2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.info("Kategoryzacja szczegółowa dostępna wkrótce (wymaga przypisania tagów w bazie).")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab3:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        if not st.session_state.is_paid:
            st.warning("Twój plik zawiera dziesiątki tysięcy nieprzeanalizowanych markerów (m.in. ryzyko urazów, metabolizm leków, choroby układu krążenia).")
            st.button("💳 Odblokuj pełny profil za 99 zł", type="primary", use_container_width=True, on_click=process_payment)
        else:
            st.success("Wszystkie raporty zostały odblokowane!")
        st.markdown('</div>', unsafe_allow_html=True)
