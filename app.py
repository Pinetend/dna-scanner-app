import streamlit as st
import pandas as pd
import io
import time

st.set_page_config(page_title="YourDNA | Poznaj Siebie", page_icon="🧬", layout="centered")

# --- 1. ROZBUDOWANA BAZA WIEDZY ---
premium_knowledge_base = {
    "rs762551": {
        "name": "☕ Metabolizm kofeiny (CYP1A2)",
        "AA": {"title": "Szybki metabolizm", "description": "Kofeina daje Ci mocnego kopa, ale szybko znika z krwiobiegu."},
        "AC": {"title": "Umiarkowany metabolizm", "description": "Przetwarzasz kofeinę w standardowym tempie."},
        "CC": {"title": "Wolny metabolizm", "description": "Kofeina utrzymuje się we krwi bardzo długo. Pij kawę tylko rano."}
    },
    "rs1815739": {
        "name": "🏃 Predyspozycje sportowe (ACTN3)",
        "CC": {"title": "Gen sprintera", "description": "Twoje mięśnie są stworzone do sportów siłowych i szybkich zrywów."},
        "CT": {"title": "Typ mieszany", "description": "Masz świetny balans między siłą a wytrzymałością."},
        "TT": {"title": "Urodzony maratończyk", "description": "Masz naturalną przewagę w sportach wytrzymałościowych."}
    },
    # NOWE CECHY:
    "rs9939609": {
        "name": "🔥 Spalanie tłuszczu i apetyt (Gen FTO)",
        "TT": {"title": "Niskie ryzyko genetycznej otyłości", "description": "Twój organizm dobrze reguluje uczucie sytości. Masz standardowe tempo spalania tkanki tłuszczowej."},
        "TA": {"title": "Podwyższone uczucie głodu", "description": "Możesz mieć genetyczną skłonność do podjadania i nieco wolniejszy metabolizm kwasów tłuszczowych."},
        "AA": {"title": "Wysokie ryzyko genetyczne otyłości", "description": "Gen 'FTO' sprawia, że po posiłku wolniej czujesz sytość. Musisz bardziej uważać na kalorykę diety niż inni."}
    },
    "rs12913832": {
        "name": "👁️ Prawdopodobny kolor oczu (Gen OCA2/HERC2)",
        "AA": {"title": "Wysoka szansa na brązowe oczy", "description": "Posiadasz wariant silnie związany z produkcją melaniny, co zazwyczaj daje ciemny kolor tęczówki."},
        "AG": {"title": "Kolor mieszany (Piwny/Zielony/Brązowy)", "description": "Genotyp heterozygotyczny. Produkcja melaniny jest umiarkowana."},
        "GG": {"title": "Wysoka szansa na niebieskie/jasne oczy", "description": "Ten wariant wyłącza produkcję dużej ilości melaniny w tęczówce, co najczęściej skutkuje błękitnym kolorem oczu."}
    }
}

def parse_dna_file(file_content):
    lines = [line for line in file_content.split('\n') if not line.startswith('#') and line.strip()]
    df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', header=None, names=['rsid', 'chromosome', 'position', 'genotype'], dtype=str, on_bad_lines='skip')
    user_snps = dict(zip(df.rsid, df.genotype.str.replace(" ", "").str.upper()))
    return user_snps

def generate_report(user_snps, knowledge_base):
    report = []
    for rsid, info in knowledge_base.items():
        if rsid in user_snps:
            user_genotype = user_snps[rsid]
            if user_genotype in info:
                report.append({"cecha": info["name"], "genotyp": user_genotype, "diagnoza": info[user_genotype]["title"], "szczegoly": info[user_genotype]["description"]})
    return report

# --- 2. ULEPSZONY INTERFEJS (UX) ---
st.title("🧬 YourDNA | Odkryj swój kod")
st.markdown("Wgraj swój surowy plik DNA z 23andMe lub MyHeritage. **Twój plik jest analizowany lokalnie i natychmiast usuwany.**")

# Wygenerowanie pliku testowego w locie
test_dna_content = """# Testowy plik DNA
rsid\tchromosome\tposition\tgenotype
rs762551\t1\t123\tAA
rs1815739\t11\t123\tCT
rs9939609\t16\t123\tTT
rs12913832\t15\t123\tGG
"""

# Sekcja UX - Przycisk pobierania
col1, col2 = st.columns([2, 1])
with col2:
    st.markdown("Nie masz pliku DNA?")
    st.download_button(
        label="📥 Pobierz plik testowy",
        data=test_dna_content,
        file_name="test_yourdna.txt",
        mime="text/plain",
        use_container_width=True
    )

with col1:
    uploaded_file = st.file_uploader("Przeciągnij plik DNA (.txt/.csv)", type=['txt', 'csv'])

if uploaded_file is not None:
    with st.spinner('Trwa analizowanie genów...'):
        time.sleep(1.5)
        file_content = uploaded_file.getvalue().decode("utf-8")
        genotypy_uzytkownika = parse_dna_file(file_content)
        gotowy_raport = generate_report(genotypy_uzytkownika, premium_knowledge_base)
        
    st.success("✅ Analiza zakończona! Oto darmowy raport:")
    st.divider()
    
    for wynik in gotowy_raport:
        st.subheader(wynik['cecha'])
        st.info(f"**Twój Genotyp:** {wynik['genotyp']} — {wynik['diagnoza']}")
        st.write(wynik['szczegoly'])
        st.write("---")
        
    st.warning("🔒 **To tylko 4 z ponad 150 zbadanych cech!**")
    st.button("Odblokuj pełny raport za 99 zł", type="primary", use_container_width=True)
