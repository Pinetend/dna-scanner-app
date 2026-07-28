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
st.title("🧬 YourDNA | Odkryj swój kod")

# Wybór języka (Tłumaczenia interfejsu)
jezyk_wybor = st.radio("Wybierz język / Select language:", ["Polski (pl)", "English (en)"], horizontal=True)
kod_jezyka = "pl" if "Polski" in jezyk_wybor else "en"

# Słownik interfejsu
ui = {
    "pl": {
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
        "pay_btn": "💳 Pay $25 (SIMULATION)"
    }
}

t = ui[kod_jezyka]
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
