import sqlite3
import pandas as pd

def zintegruj_bazy_naukowe():
    print("Rozpoczynam integrację wielkich baz danych...")
    conn = sqlite3.connect("baza_700k.db")
    cursor = conn.cursor()
    
    # ---------------------------------------------------------
    # KROK 1: Symulacja wczytania ogromnych plików CSV z internetu
    # W rzeczywistości użyjesz tu np. pd.read_csv("dbsnp.csv", chunksize=100000)
    # ---------------------------------------------------------
    
    # Biblioteka 1: Surowe geny (dbSNP) - Tylko numery i nazwy naukowe
    dane_dbsnp = pd.DataFrame({
        "rsid": ["rs762551", "rs1815739", "rs9939609", "rs4988235", "rs1801280"],
        "nazwa_naukowa": ["CYP1A2", "ACTN3", "FTO", "MCM6", "NAT2"],
        "kategoria": ["Dieta", "Sport", "Metabolizm", "Dieta", "Detoks"]
    })
    
    # Biblioteka 2: Efekty i opisy (ClinVar / GWAS) - Co oznaczają mutacje
    dane_clinvar = pd.DataFrame({
        "rsid": ["rs762551", "rs762551", "rs1815739", "rs9939609", "rs4988235"],
        "genotyp": ["AA", "CC", "CC", "TT", "CC"],
        "jezyk": ["pl", "pl", "pl", "pl", "pl"],
        "efekt_tytul": ["Szybki metabolizm kofeiny", "Wolny metabolizm kofeiny", "Gen sprintera", "Niskie ryzyko otyłości", "Nietolerancja laktozy"],
        "efekt_opis": ["Kofeina znika szybko.", "Kofeina działa długo.", "Mięśnie siłowe.", "Dobry metabolizm tłuszczów.", "Brak enzymu laktazy."]
    })

    # ---------------------------------------------------------
    # KROK 2: Wrzucenie obu bibliotek do tymczasowych tabel SQL
    # ---------------------------------------------------------
    dane_dbsnp.to_sql("temp_dbsnp", conn, if_exists="replace", index=False)
    dane_clinvar.to_sql("temp_clinvar", conn, if_exists="replace", index=False)
    
    # ---------------------------------------------------------
    # KROK 3: Magia SQL (JOIN) - Łączenie dwóch bibliotek w gotową bazę
    # ---------------------------------------------------------
    
    # Czyszczenie docelowych tabel przed aktualizacją
    cursor.execute("DELETE FROM snp_database")
    cursor.execute("DELETE FROM tlumaczenia_genow")
    
    # 1. Zasilanie głównej tabeli genów (dodajemy ulepszone nazwy)
    cursor.execute("""
        INSERT INTO snp_database (rsid, name, is_premium, czestotliwosc)
        SELECT 
            rsid, 
            kategoria || ' (' || nazwa_naukowa || ')' AS name,
            1 AS is_premium,
            'Brak danych' AS czestotliwosc
        FROM temp_dbsnp
    """)
    
    # 2. Zasilanie tabeli tłumaczeń złączeniem (JOIN) obu baz
    cursor.execute("""
        INSERT INTO tlumaczenia_genow (rsid, jezyk, genotyp, tytul, opis)
        SELECT 
            c.rsid, 
            c.jezyk, 
            c.genotyp, 
            c.efekt_tytul, 
            c.efekt_opis
        FROM temp_clinvar c
        JOIN temp_dbsnp d ON c.rsid = d.rsid
    """)
    
    # Usuwamy tabele tymczasowe, by nie śmiecić
    cursor.execute("DROP TABLE temp_dbsnp")
    cursor.execute("DROP TABLE temp_clinvar")
    
    conn.commit()
    conn.close()
    print("Bazy zostały pomyślnie połączone przez SQL i zapisane!")

if __name__ == "__main__":
    zintegruj_bazy_naukowe()
