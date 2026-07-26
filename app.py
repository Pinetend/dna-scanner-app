import streamlit as st
import pandas as pd
import io
import time

st.set_page_config(page_title="YourDNA | Poznaj Siebie", page_icon="🧬", layout="centered")

# --- SYSTEM ZARZĄDZANIA SESJĄ (PŁATNOŚCIĄ) ---
# Domyślnie każdy nowy użytkownik ma status "Nieopłacony"
if 'is_paid' not in st.session_state:
    st.session_state.is_paid = False

def process_payment():
    # Ta funkcja imituje udaną płatność przez Stripe
    st.session_state.is_paid = True

# --- 1. ROZBUDOWANA BAZA WIEDZY (Podział na Free i Premium) ---
knowledge_base = {
    # ==========================================
    # 🟢 PAKIET DARMOWY (Przynęta)
    # ==========================================
    "rs762551": {
        "name": "☕ Metabolizm kofeiny (CYP1A2)", "is_premium": False,
        "AA": {"title": "Szybki metabolizm", "description": "Kofeina daje Ci mocnego kopa, ale szybko znika z krwiobiegu."},
        "AC": {"title": "Umiarkowany metabolizm", "description": "Przetwarzasz kofeinę w standardowym tempie."},
        "CC": {"title": "Wolny metabolizm", "description": "Kofeina utrzymuje się we krwi bardzo długo. Pij kawę tylko rano."}
    },
    "rs1815739": {
        "name": "🏃 Predyspozycje sportowe (ACTN3)", "is_premium": False,
        "CC": {"title": "Gen sprintera", "description": "Twoje mięśnie są stworzone do sportów siłowych i szybkich zrywów."},
        "CT": {"title": "Typ mieszany", "description": "Masz świetny balans między siłą a wytrzymałością."},
        "TT": {"title": "Urodzony maratończyk", "description": "Masz naturalną przewagę w sportach wytrzymałościowych."}
    },

    # ==========================================
    # 🌟 PAKIET PREMIUM: DIETA I METABOLIZM
    # ==========================================
    "rs9939609": {
        "name": "🔥 Spalanie tłuszczu i apetyt (Gen FTO)", "is_premium": True,
        "TT": {"title": "Niskie ryzyko otyłości", "description": "Twój organizm dobrze reguluje uczucie sytości. Masz standardowe tempo spalania tkanki tłuszczowej."},
        "TA": {"title": "Podwyższone uczucie głodu", "description": "Możesz mieć genetyczną skłonność do podjadania i nieco wolniejszy metabolizm."},
        "AA": {"title": "Wysokie ryzyko otyłości", "description": "Gen 'FTO' sprawia, że po posiłku wolniej czujesz sytość. Musisz uważać na kalorykę."}
    },
    "rs671": {
        "name": "🍷 Tolerancja alkoholu (ALDH2)", "is_premium": True,
        "GG": {"title": "Normalna tolerancja", "description": "Twój organizm prawidłowo rozkłada toksyczny aldehyd octowy. Nie doświadczasz tzw. 'Asian flush'."},
        "GA": {"title": "Słaba tolerancja", "description": "Masz znacznie obniżoną zdolność rozkładu alkoholu. Możesz odczuwać zaczerwienienie twarzy i szybsze bicie serca po wypiciu."},
        "AA": {"title": "Brak tolerancji", "description": "Twoja wątroba ma ogromne trudności z metabolizmem alkoholu. Spożywanie alkoholu jest dla Ciebie wysoce toksyczne."}
    },
    "rs4988235": {
        "name": "🥛 Trawienie laktozy (MCM6)", "is_premium": True,
        "TT": {"title": "Pełna tolerancja", "description": "Twoje geny pozwalają na bezproblemowe trawienie mleka krowiego w dorosłym życiu."},
        "CT": {"title": "Dobra tolerancja", "description": "Prawdopodobnie dobrze trawisz nabiał, choć tolerancja może delikatnie spadać z wiekiem."},
        "CC": {"title": "Nietolerancja laktozy", "description": "Twój organizm przestał produkować laktazę. Zwykłe mleko może powodować silny dyskomfort."}
    },

    # ==========================================
    # 🌟 PAKIET PREMIUM: WITAMINY I ZDROWIE
    # ==========================================
    "rs2282679": {
        "name": "☀️ Przyswajanie Witaminy D (GC)", "is_premium": True,
        "AA": {"title": "Prawidłowy poziom", "description": "Twoje geny sprzyjają utrzymaniu optymalnego poziomu witaminy D we krwi."},
        "AC": {"title": "Umiarkowane ryzyko niedoboru", "description": "Masz lekko obniżoną zdolność transportu witaminy D. Rozważ suplementację w zimie."},
        "CC": {"title": "Wysokie ryzyko niedoboru", "description": "Twój genotyp wiąże się ze znacznie gorszym transportem witaminy D. Koniecznie badaj jej poziom!"}
    },
    "rs1801133": {
        "name": "🥬 Kwas foliowy i detoks (MTHFR)", "is_premium": True,
        "CC": {"title": "Optymalny metabolizm", "description": "Twój enzym MTHFR działa na 100%. Świetnie przyswajasz zwykły kwas foliowy z diety."},
        "CT": {"title": "Obniżona wydajność (o 30%)", "description": "Twój organizm nieco gorzej przetwarza kwas foliowy. Warto zadbać o zielone warzywa w diecie."},
        "TT": {"title": "Niska wydajność (o 70%)", "description": "Posiadasz mutację, która drastycznie utrudnia przyswajanie zwykłego kwasu foliowego. Rozważ suplementację formą metylowaną."}
    },

    # ==========================================
    # 🌟 PAKIET PREMIUM: UMYSŁ I STRES
    # ==========================================
    "rs4680": {
        "name": "🧠 Radzenie sobie ze stresem (Gen COMT)", "is_premium": True,
        "GG": {"title": "Typ Wojownika (Warrior)", "description": "Twój mózg szybko usuwa dopaminę. Jesteś niezwykle opanowany pod presją i świetnie radzisz sobie w stresujących sytuacjach, ale możesz potrzebować silnych bodźców do motywacji na co dzień."},
        "AG": {"title": "Typ Mieszany", "description": "Posiadasz optymalny balans między pracą pod presją a codzienną koncentracją i kreatywnością."},
        "AA": {"title": "Typ Myśliciela (Worrier)", "description": "Masz wysoki poziom dopaminy na co dzień. Masz świetną pamięć, wysoką empatię i kreatywność, ale w sytuacjach silnego stresu łatwo się przebodźcowujesz i panikujesz."}
    },

    # ==========================================
    # 🌟 PAKIET PREMIUM: CECHY FIZYCZNE
    # ==========================================
    "rs12913832": {
        "name": "👁️ Kolor oczu (Gen OCA2/HERC2)", "is_premium": True,
        "AA": {"title": "Brązowe", "description": "Posiadasz wariant silnie związany z produkcją melaniny, co zazwyczaj daje ciemny kolor tęczówki."},
        "AG": {"title": "Mieszany (Piwny/Zielony)", "description": "Genotyp heterozygotyczny. Produkcja melaniny jest umiarkowana."},
        "GG": {"title": "Jasne (Niebieskie/Szare)", "description": "Ten wariant wyłącza produkcję dużej ilości melaniny w tęczówce, co skutkuje jasnym kolorem oczu."}
    }
}

def parse_dna_file(file_content):
    lines = [line for line in file_content.split('\n') if not line.startswith('#') and line.strip()]
    df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', header=None, names=['rsid', 'chromosome', 'position', 'genotype'], dtype=str, on_bad_lines='skip')
    return dict(zip(df.rsid, df.genotype.str.replace(" ", "").str.upper()))

def generate_report(user_snps, k_base, has_paid):
    report = []
    for rsid, info in k_base.items():
        if rsid in user_snps:
            # Jeśli cecha jest premium, a użytkownik nie zapłacił - ignorujemy ją na tym etapie
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

# Generowanie rozszerzonego pliku testowego
test_dna_content = """# Testowy plik DNA
rsid\tchromosome\tposition\tgenotype
rs762551\t1\t123\tAA
rs1815739\t11\t123\tCT
rs9939609\t16\t123\tTT
rs12913832\t15\t123\tGG
rs2282679\t4\t123\tCC
"""

col1, col2 = st.columns([2, 1])
with col2:
    st.markdown("Nie masz pliku DNA?")
    st.download_button(label="📥 Pobierz plik testowy", data=test_dna_content, file_name="test_yourdna.txt", mime="text/plain", use_container_width=True)

with col1:
    uploaded_file = st.file_uploader("Przeciągnij plik DNA (.txt/.csv)", type=['txt', 'csv'])

if uploaded_file is not None:
    # Uruchamiamy analizę tylko raz na wgranie (optymalizacja)
    file_content = uploaded_file.getvalue().decode("utf-8")
    genotypy_uzytkownika = parse_dna_file(file_content)
    gotowy_raport = generate_report(genotypy_uzytkownika, knowledge_base, st.session_state.is_paid)
    
    # Wyświetlanie animacji sukcesu przy odblokowaniu
    if st.session_state.is_paid:
        st.balloons()
        st.success("🎉 Płatność przebiegła pomyślnie! Twój pełny profil genetyczny został odblokowany.")
    else:
        st.success("✅ Analiza zakończona! Oto darmowy raport:")
        
    st.divider()
    
    # Rysowanie kafelków z wynikami
    for wynik in gotowy_raport:
        # Dodajemy specjalne oznacznie dla cech premium
        if wynik.get("is_premium"):
            st.subheader(f"🌟 {wynik['cecha']}")
        else:
            st.subheader(wynik['cecha'])
            
        st.info(f"**Twój Genotyp:** {wynik['genotyp']} — {wynik['diagnoza']}")
        st.write(wynik['szczegoly'])
        st.write("---")
        
    # --- PAYWALL (Wyświetlany tylko, jeśli użytkownik nie zapłacił) ---
    if not st.session_state.is_paid:
        st.warning("🔒 **To tylko ułamek Twoich wyników!**")
        st.markdown("W Twoim pliku wykryliśmy ukryte geny odpowiadające za spalanie tłuszczu, kolor oczu, przyswajanie witaminy D i wiele więcej.")
        
        # Przycisk symulujący płatność (uruchamia funkcję process_payment)
        st.button("💳 Zapłać 99 zł (SYMULACJA)", type="primary", use_container_width=True, on_click=process_payment)
