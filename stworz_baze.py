import sqlite3

def zainicjalizuj_baze():
    # Tworzy plik bazy danych (lub łączy się z nim, jeśli istnieje)
    conn = sqlite3.connect("baza_700k.db")
    cursor = conn.cursor()
    
    # 1. Tabela główna (zoptymalizowana pod 700k rekordów)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snp_database (
            rsid TEXT PRIMARY KEY,
            name TEXT,
            is_premium BOOLEAN,
            czestotliwosc TEXT
        )
    ''')
    
    # 2. Tabela wielojęzycznych tłumaczeń
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tlumaczenia_genow (
            rsid TEXT,
            jezyk TEXT,
            genotyp TEXT,
            tytul TEXT,
            opis TEXT,
            PRIMARY KEY (rsid, jezyk, genotyp),
            FOREIGN KEY (rsid) REFERENCES snp_database(rsid)
        )
    ''')
    
    # 3. Wypełnianie bazy danymi testowymi
    dane_startowe_snp = [
        ("rs762551", "☕ Metabolizm kofeiny (CYP1A2)", 0, "Ok. 40% populacji"),
        ("rs1815739", "🏃 Predyspozycje sportowe (ACTN3)", 0, "Ok. 30% populacji"),
        ("rs9939609", "🔥 Spalanie tłuszczu i apetyt (Gen FTO)", 1, "Ok. 16% populacji")
    ]
    cursor.executemany("INSERT OR IGNORE INTO snp_database VALUES (?, ?, ?, ?)", dane_startowe_snp)
    
    dane_startowe_tlumaczenia = [
        # Polski (pl)
        ("rs762551", "pl", "AA", "Szybki metabolizm", "Kofeina daje Ci mocnego kopa, ale szybko znika z krwiobiegu."),
        ("rs762551", "pl", "CC", "Wolny metabolizm", "Kofeina utrzymuje się we krwi bardzo długo."),
        ("rs1815739", "pl", "CC", "Gen sprintera", "Twoje mięśnie są stworzone do sportów siłowych."),
        ("rs9939609", "pl", "TT", "Niskie ryzyko", "Twój organizm dobrze reguluje uczucie sytości."),
        
        # Angielski (en)
        ("rs762551", "en", "AA", "Fast metabolism", "Caffeine gives you a strong boost, but leaves your bloodstream quickly."),
        ("rs762551", "en", "CC", "Slow metabolism", "Caffeine stays in your blood for a very long time."),
        ("rs1815739", "en", "CC", "Sprinter gene", "Your muscles are built for power sports and short bursts."),
        ("rs9939609", "en", "TT", "Low risk", "Your body regulates satiety well.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO tlumaczenia_genow VALUES (?, ?, ?, ?, ?)", dane_startowe_tlumaczenia)
    
    conn.commit()
    conn.close()
    print("Baza SQLite została pomyślnie utworzona i zasilona danymi!")

if __name__ == "__main__":
    zainicjalizuj_baze()
