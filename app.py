import streamlit as st
import pandas as pd
import io
import sqlite3
import tempfile
import os
from fpdf import FPDF

st.set_page_config(page_title="YourDNA | Poznaj Siebie", page_icon="🧬", layout="centered")

# --- INICJALIZACJA BAZY (automatyczna dla MVP) ---
# W środowisku produkcyjnym odpalamy stworz_baze.py osobno.
if not os.path.exists("baza_700k.db"):
    import stworz_baze
    stworz_baze.zainicjalizuj_baze()

# --- SYSTEM ZARZĄDZANIA SESJĄ ---
if 'is_paid' not in st.session_state:
    st.session_state.is_paid = False

def process_payment():
    st.session_state.is_paid = True

# --- FUNKCJE GENEROWANIA PDF ---
def wyczysc_tekst(tekst):
    tekst = str(tekst).replace('\xa0', ' ')
    emotikony = ['☕', '🏃', '🔥', '🍷', '🥛', '☀️', '🥬', '🧠', '👁️', '🌟', '📊']
    for emoji in emotikony:
        tekst = tekst.replace(emoji, '')
    return tekst.strip()

def stworz_pdf(raport, tytul_pdf):
    pdf = FPDF()
    font_path = "Roboto-Regular.ttf"
    
    # Dodanie czcionki, jeśli istnieje w repozytorium
    if os.path.exists(font_path):
        pdf.add_font("Roboto", style="", fname=font_path)
        pdf.set_font("Roboto", size=10)
    else:
        pdf.set_font("Arial", size=10)
    
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Nagłówek dokumentu
    pdf.set_font(pdf.font_family, size=18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, txt=wyczysc_tekst(tytul_pdf), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    # Wypisywanie wyników
    for wynik in raport:
        pdf.set_font(pdf.font_family, size=14)
        pdf.set_text_color(41, 128, 185) 
        pdf.multi_cell(0, 8, txt=wyczysc_tekst(wynik['cecha']), new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font(pdf.font_family, size=9)
        pdf.set_text_color(120, 120, 120)
        czest_txt = f"Czestotliwosc / Frequency: {wynik.get('czestotliwosc', 'Brak / N/A')}"
        pdf.multi_cell(0, 5, txt=wyczysc_tekst(czest_txt), new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font(pdf.font_family, size=11)
        pdf.set_text_color(0, 0, 0)
        diag_txt = f"{wynik['genotyp']} - {wynik['diagnoza']}"
        pdf.multi_cell(0, 6, txt=wyczysc_tekst(diag_txt), new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font(pdf.font_family, size=10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 6, txt=wyczysc_tekst(wynik['szczegoly']), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

# --- LOGIKA ANALIZY Z PANDAS ---
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
                
            cursor.execute("""
                SELECT tytul, opis FROM tlumaczenia_genow 
                WHERE rsid = ? AND jezyk = ? AND genotyp = ?
            """, (rsid, jezyk, user_genotype))
            
            diag_info = cursor.fetchone()
            if diag_info:
                tytul, opis = diag_info
                raport.append({
                    "cecha": name,
                    "genotyp": user_genotype,
                    "diagnoza": tytul,
                    "szczegoly": opis,
                    "is_premium": is_premium,
                    "czestotliwosc": czestotliwosc
                })
                
    conn.close()
    return raport

# --- INTERFEJS UŻYTKOWNIKA ---

# Wybór języka (Rozwijana lista z flagami i wyszukiwaniem)
jezyki = {
    "🇵🇱 Polski": "pl",
    "🇬🇧 English": "en",
    "🇩🇪 Deutsch": "de",
    "🇫🇷 Français": "fr",
    "🇪🇸 Español": "es",
    "🇮🇹 Italiano": "it"
}

wybrany_jezyk = st.selectbox("🌍 Wybierz język / Select language:", list(jezyki.keys()))
kod_jezyka = jezyki[wybrany_jezyk]

# Rozbudowany słownik interfejsu (UI) dla wielu języków
ui = {
    "pl": {
        "main_title": "Odkryj swój kod",
        "upload": "Wgraj swój surowy plik DNA. Twój plik jest analizowany lokalnie i natychmiast usuwany.",
        "drag": "Przeciągnij plik DNA (.txt/.csv)",
        "no_file": "Nie masz pliku DNA?",
        "test_btn": "📥 Pobierz plik testowy",
        "success_pay": "🎉 Płatność przebiegła pomyślnie! Twój pełny profil genetyczny został odblokowany.",
        "pdf_btn": "📄 Pobierz swój raport w formacie PDF",
        "pdf_title": "Twój Osobisty Raport DNA",
        "success_free": "✅ Analiza zakończona! Oto darmowy raport:",
        "pay_warn": "🔒 To tylko ułamek Twoich wyników!",
        "pay_desc": "W Twoim pliku wykryliśmy ukryte geny odpowiadające za m.in. tolerancję alkoholu, przyswajanie witaminy D i radzenie sobie ze stresem.",
        "pay_btn": "💳 Zapłać 99 zł (SYMULACJA)"
    },
    "en": {
        "main_title": "Discover your code",
        "upload": "Upload your raw DNA file. Your file is analyzed locally and deleted immediately.",
        "drag": "Drag and drop DNA file (.txt/.csv)",
        "no_file": "Don't have a DNA file?",
        "test_btn": "📥 Download test file",
        "success_pay": "🎉 Payment successful! Your full genetic profile has been unlocked.",
        "pdf_btn": "📄 Download your report in PDF",
        "pdf_title": "Your Personal DNA Report",
        "success_free": "✅ Analysis complete! Here is your free report:",
        "pay_warn": "🔒 This is just a fraction of your results!",
        "pay_desc": "We detected hidden genes responsible for alcohol tolerance, vitamin D absorption, and stress management.",
        "pay_btn": "💳 Pay 25 EUR (SIMULATION)"
    },
    "de": {
        "main_title": "Entdecke deinen Code",
        "upload": "Laden Sie Ihre rohe DNA-Datei hoch. Ihre Datei wird lokal analysiert und sofort gelöscht.",
        "drag": "DNA-Datei hier ablegen (.txt/.csv)",
        "no_file": "Haben Sie keine DNA-Datei?",
        "test_btn": "📥 Testdatei herunterladen",
        "success_pay": "🎉 Zahlung erfolgreich! Ihr vollständiges genetisches Profil wurde entsperrt.",
        "pdf_btn": "📄 Laden Sie Ihren Bericht als PDF herunter",
        "pdf_title": "Ihr persönlicher DNA-Bericht",
        "success_free": "✅ Analyse abgeschlossen! Hier ist Ihr kostenloser Bericht:",
        "pay_warn": "🔒 Dies ist nur ein Bruchteil Ihrer Ergebnisse!",
        "pay_desc": "Wir haben versteckte Gene entdeckt, die für Alkoholtoleranz, Vitamin-D-Aufnahme und Stressbewältigung verantwortlich sind.",
        "pay_btn": "💳 25 EUR Bezahlen (SIMULATION)"
    },
    "fr": {
        "main_title": "Découvrez votre code",
        "upload": "Téléchargez votre fichier ADN brut. Votre fichier est analysé localement et supprimé immédiatement.",
        "drag": "Faites glisser le fichier ADN (.txt/.csv)",
        "no_file": "Vous n'avez pas de fichier ADN ?",
        "test_btn": "📥 Télécharger le fichier de test",
        "success_pay": "🎉 Paiement réussi ! Votre profil génétique complet a été débloqué.",
        "pdf_btn": "📄 Téléchargez votre rapport en PDF",
        "pdf_title": "Votre rapport ADN personnel",
        "success_free": "✅ Analyse terminée ! Voici votre rapport gratuit :",
        "pay_warn": "🔒 Ce n'est qu'une fraction de vos résultats !",
        "pay_desc": "Nous avons détecté des gènes cachés responsables de la tolérance à l'alcool, de l'absorption de la vitamine D et de la gestion du stress.",
        "pay_btn": "💳 Payer 25 EUR (SIMULATION)"
    },
    "es": {
        "main_title": "Descubre tu código",
        "upload": "Sube tu archivo de ADN sin procesar. Tu archivo se analiza localmente y se elimina de inmediato.",
        "drag": "Arrastra el archivo de ADN (.txt/.csv)",
        "no_file": "¿No tienes un archivo de ADN?",
        "test_btn": "📥 Descargar archivo de prueba",
        "success_pay": "🎉 ¡Pago exitoso! Tu perfil genético completo ha sido desbloqueado.",
        "pdf_btn": "📄 Descarga tu informe en PDF",
        "pdf_title": "Tu informe de ADN personal",
        "success_free": "✅ ¡Análisis completado! Aquí tienes tu informe gratuito:",
        "pay_warn": "🔒 ¡Esto es solo una fracción de tus resultados!",
        "pay_desc": "Hemos detectado genes ocultos responsables de la tolerancia al alcohol, la absorción de vitamina D y el manejo del estrés.",
        "pay_btn": "💳 Pagar 25 EUR (SIMULACIÓN)"
    },
    "it": {
        "main_title": "Scopri il tuo codice",
        "upload": "Carica il tuo file DNA grezzo. Il tuo file viene analizzato localmente ed eliminato immediatamente.",
        "drag": "Trascina il file DNA (.txt/.csv)",
        "no_file": "Non hai un file DNA?",
        "test_btn": "📥 Scarica il file di test",
        "success_pay": "🎉 Pagamento riuscito! Il tuo profilo genetico completo è stato sbloccato.",
        "pdf_btn": "📄 Scarica il tuo rapporto in PDF",
        "pdf_title": "Il tuo rapporto DNA personale",
        "success_free": "✅ Analisi completata! Ecco il tuo rapporto gratuito:",
        "pay_warn": "🔒 Questa è solo una frazione dei tuoi risultati!",
        "pay_desc": "Abbiamo rilevato geni nascosti responsabili della tolleranza all'alcol, dell'assorbimento della vitamina D e della gestione dello stress.",
        "pay_btn": "💳 Paga 25 EUR (SIMULAZIONE)"
    }
}

t = ui[kod_jezyka]

# Dynamiczny główny tytuł na stronie:
st.title(f"🧬 YourDNA | {t['main_title']}")
st.markdown(t["upload"])

test_dna_content = """# Test DNA File
rsid\tchromosome\tposition\tgenotype
rs762551\t1\t123\tAA
rs1815739\t11\t123\tCC
rs9939609\t16\t123\tTT
"""

col1, col2 = st.columns([2, 1])
with col2:
    st.markdown(t["no_file"])
    st.download_button(label=t["test_btn"], data=test_dna_content, file_name="test_yourdna.txt", mime="text/plain", use_container_width=True)

with col1:
    uploaded_file = st.file_uploader(t["drag"], type=['txt', 'csv'])

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    genotypy_uzytkownika = parse_dna_file(file_content)
    
    gotowy_raport = pobierz_wyniki_z_bazy(genotypy_uzytkownika, kod_jezyka, st.session_state.is_paid)
    
    if st.session_state.is_paid:
        st.balloons()
        st.success(t["success_pay"])
        
        pdf_bytes = stworz_pdf(gotowy_raport, t["pdf_title"])
        st.download_button(
            label=t["pdf_btn"],
            data=pdf_bytes,
            file_name="Raport_YourDNA.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        st.divider()
    else:
        st.success(t["success_free"])
        st.divider()
        
    for wynik in gotowy_raport:
        if wynik.get("is_premium"):
            st.subheader(f"🌟 {wynik['cecha']}")
        else:
            st.subheader(wynik['cecha'])
            
        st.caption(f"📊 {wynik.get('czestotliwosc', '')}")
        st.info(f"**{wynik['genotyp']}** — {wynik['diagnoza']}")
        st.write(wynik['szczegoly'])
        st.write("---")
        
    if not st.session_state.is_paid:
        st.warning(f"**{t['pay_warn']}**")
        st.markdown(t["pay_desc"])
        st.button(t["pay_btn"], type="primary", use_container_width=True, on_click=process_payment)
