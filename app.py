import streamlit as st
import pandas as pd
import io
import time
import json

st.set_page_config(page_title="YourDNA | Poznaj Siebie", page_icon="🧬", layout="centered")

# --- WCZYTYWANIE BAZY WIEDZY Z PLIKU JSON ---
with open("baza.json", "r", encoding="utf-8") as file:
    knowledge_base = json.load(file)

# --- SYSTEM ZARZĄDZANIA SESJĄ (PŁATNOŚCIĄ) ---
if 'is_paid' not in st.session_state:
    st.session_state.is_paid = False

def process_payment():
    st.session_state.is_paid = True

# --- LOGIKA ANALIZY ---
def parse_dna_file(file_content):
    lines = [line for line in file_content.split('\n') if not line.startswith('#') and line.strip()]
    df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', header=None, names=['rsid', 'chromosome', 'position', 'genotype'], dtype=str, on_bad_lines='skip')
    return dict(zip(df.rsid, df.genotype.str.replace(" ", "").str.upper()))

def generate_report(user_snps, k_base, has_paid):
    report = []
    for rsid, info in k_base.items():
        if rsid in user_snps:
            if info["is_premium"] and not has_paid:
                continue
            user_genotype = user_snps[rsid]
            if user_genotype in info:
                report.append({
                    "cecha": info["name"], 
                    "genotyp": user_genotype, 
                    "diagnoza": info[user_genotype]["title"], 
                    "szczegoly": info[user_genotype]["description"],
                    "is_premium": info["is_premium"]
                })
    return report

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("🧬 YourDNA | Odkryj swój kod")
st.markdown("Wgraj swój surowy plik DNA. **Twój plik jest analizowany lokalnie i natychmiast usuwany.**")

# Rozszerzony plik testowy
test_dna_content = """# Testowy plik DNA
rsid\tchromosome\tposition\tgenotype
rs762551\t1\t123\tAA
rs1815739\t11\t123\tCT
rs9939609\t16\t123\tTT
rs671\t12\t123\tGG
rs4988235\t2\t123\tTT
rs2282679\t4\t123\tCC
rs1801133\t1\t123\tCT
rs4680\t22\t123\tAA
rs12913832\t15\t123\tGG
"""

col1, col2 = st.columns([2, 1])
with col2:
    st.markdown("Nie masz pliku DNA?")
    st.download_button(label="📥 Pobierz plik testowy", data=test_dna_content, file_name="test_yourdna.txt", mime="text/plain", use_container_width=True)

with col1:
    uploaded_file = st.file_uploader("Przeciągnij plik DNA (.txt/.csv)", type=['txt', 'csv'])

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    genotypy_uzytkownika = parse_dna_file(file_content)
    gotowy_raport = generate_report(genotypy_uzytkownika, knowledge_base, st.session_state.is_paid)
    
    if st.session_state.is_paid:
        st.balloons()
        st.success("🎉 Płatność przebiegła pomyślnie! Twój pełny profil genetyczny został odblokowany.")
    else:
        st.success("✅ Analiza zakończona! Oto darmowy raport:")
        
    st.divider()
    
    for wynik in gotowy_raport:
        if wynik.get("is_premium"):
            st.subheader(f"🌟 {wynik['cecha']}")
        else:
            st.subheader(wynik['cecha'])
            
        st.info(f"**Twój Genotyp:** {wynik['genotyp']} — {wynik['diagnoza']}")
        st.write(wynik['szczegoly'])
        st.write("---")
        
    if not st.session_state.is_paid:
        st.warning("🔒 **To tylko ułamek Twoich wyników!**")
        st.markdown("W Twoim pliku wykryliśmy ukryte geny odpowiadające za m.in. tolerancję alkoholu, przyswajanie witaminy D i radzenie sobie ze stresem.")
        st.button("💳 Zapłać 99 zł (SYMULACJA)", type="primary", use_container_width=True, on_click=process_payment)
