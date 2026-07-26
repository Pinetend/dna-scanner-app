import streamlit as st
import pandas as pd
import io
import time

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="DNA Scanner | Poznaj Siebie", page_icon="🧬", layout="centered")

# --- NASZA BAZA WIEDZY I SILNIK (z Fazy 2) ---
premium_knowledge_base = {
    "rs762551": {
        "name": "☕ Metabolizm kofeiny (CYP1A2)",
        "AA": {"title": "Szybki metabolizm",
               "description": "Kofeina daje Ci mocnego kopa, ale szybko znika z krwiobiegu. Możesz ją pić nawet późnym popołudniem."},
        "AC": {"title": "Umiarkowany metabolizm",
               "description": "Przetwarzasz kofeinę w standardowym tempie. Unikaj espresso po 16:00."},
        "CC": {"title": "Wolny metabolizm",
               "description": "Kofeina utrzymuje się we krwi bardzo długo. Pij kawę tylko rano, inaczej zepsujesz swój sen!"}
    },
    "rs1815739": {
        "name": "🏃 Predyspozycje sportowe (ACTN3)",
        "CC": {"title": "Gen sprintera",
               "description": "Twoje mięśnie są stworzone do sportów siłowych i szybkich zrywów (np. podnoszenie ciężarów, sprint)."},
        "CT": {"title": "Typ mieszany",
               "description": "Masz świetny balans. Sprawdzisz się zarówno na siłowni, jak i podczas dłuższych biegów."},
        "TT": {"title": "Urodzony maratończyk",
               "description": "Twoje włókna mięśniowe są wolnokurczliwe. Masz naturalną przewagę w sportach wytrzymałościowych."}
    }
}


def parse_dna_file(file_content):
    lines = [line for line in file_content.split('\n') if not line.startswith('#') and line.strip()]
    df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', header=None,
                     names=['rsid', 'chromosome', 'position', 'genotype'], dtype=str, on_bad_lines='skip')
    user_snps = dict(zip(df.rsid, df.genotype.str.replace(" ", "").str.upper()))
    return user_snps


def generate_report(user_snps, knowledge_base):
    report = []
    for rsid, info in knowledge_base.items():
        if rsid in user_snps:
            user_genotype = user_snps[rsid]
            if user_genotype in info:
                report.append(
                    {"cecha": info["name"], "genotyp": user_genotype, "diagnoza": info[user_genotype]["title"],
                     "szczegoly": info[user_genotype]["description"]})
    return report


# --- INTERFEJS UŻYTKOWNIKA (FRONTEND) ---

st.title("🧬 Odkryj sekrety swojego DNA")
st.markdown(
    "Wgraj swój surowy plik DNA z 23andMe lub MyHeritage i poznaj swoje genetyczne predyspozycje. **Twój plik jest analizowany lokalnie i natychmiast usuwany.**")

# Pole do wgrywania pliku
uploaded_file = st.file_uploader("Przeciągnij i upuść plik DNA (.txt lub .csv)", type=['txt', 'csv'])

if uploaded_file is not None:
    # Kiedy użytkownik wgra plik, pokazujemy pasek ładowania (dla efektu "wow")
    with st.spinner('Trwa analizowanie ponad 700 000 wariantów genetycznych...'):
        time.sleep(2)  # Sztuczne opóźnienie, żeby wyglądało profesjonalnie

        # Odczytujemy plik
        file_content = uploaded_file.getvalue().decode("utf-8")
        genotypy_uzytkownika = parse_dna_file(file_content)
        gotowy_raport = generate_report(genotypy_uzytkownika, premium_knowledge_base)

    st.success("✅ Analiza zakończona sukcesem! Oto Twój darmowy raport:")
    st.divider()

    # Wyświetlanie wyników w ładnych kafelkach
    for wynik in gotowy_raport:
        st.subheader(f"{wynik['cecha']}")
        st.info(f"**Twój Genotyp:** {wynik['genotyp']} — {wynik['diagnoza']}")
        st.write(wynik['szczegoly'])
        st.write("---")

    # --- PAYWALL (Zachęta do zakupu pełnej wersji) ---
    st.warning("🔒 **To tylko 2 z ponad 50 zbadanych cech!**")
    st.markdown("""
    W Twoim pliku wykryliśmy informacje dotyczące m.in.:
    * 🥦 Predyspozycji do otyłości i metabolizmu węglowodanów
    * 🧠 Skłonności do stresu i pracy pod presją
    * 💊 Zapotrzebowania na witaminy D3, B12 i magnez
    """)

    # Przycisk (który w przyszłości podepniemy pod bramkę płatności)
    st.button("Odblokuj pełny raport za 99 zł", type="primary", use_container_width=True)