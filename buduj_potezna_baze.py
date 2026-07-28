import sqlite3
import pandas as pd
import time
import os

DB_NAME = "baza_700k.db"

def przygotuj_strukture_bazy():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tworzymy tabele główne (usuwamy stare, jeśli istnieją, by zacząć na czysto)
    cursor.execute("DROP TABLE IF EXISTS snp_database")
    cursor.execute("DROP TABLE IF EXISTS tlumaczenia_genow")
    
    cursor.execute('''
        CREATE TABLE snp_database (
            rsid TEXT PRIMARY KEY,
            name TEXT,
            is_premium BOOLEAN,
            czestotliwosc TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE tlumaczenia_genow (
            rsid TEXT,
            jezyk TEXT,
            genotyp TEXT,
            tytul TEXT,
            opis TEXT,
            PRIMARY KEY (rsid, jezyk, genotyp)
        )
    ''')
    
    # 2. INDEKSOWANIE - To dzięki temu aplikacja przeszuka 700k wierszy w 1 sekundę!
    cursor.execute("CREATE INDEX idx_rsid ON tlumaczenia_genow(rsid)")
    
    conn.commit()
    conn.close()
    print("✅ Struktura bazy danych i indeksy zostały przygotowane.")

def importuj_masowe_dane(sciezka_do_pliku_csv):
    """
    Funkcja czyta gigantyczne pliki po kawałku (chunking) 
    i ładuje je prosto do bazy danych SQLite.
    """
    if not os.path.exists(sciezka_do_pliku_csv):
        print(f"❌ Nie znaleziono pliku: {sciezka_do_pliku_csv}")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # Ustawiamy rozmiar "kęsa" na 100 000 wierszy na raz
    chunk_size = 100000 
    licznik_wierszy = 0
    start_time = time.time()
    
    print(f"🚀 Rozpoczynam przetwarzanie pliku {sciezka_do_pliku_csv}...")
    
    # Otwieramy gigantyczny plik (używamy separatora tabulacji dla plików medycznych)
    try:
        dane_chunks = pd.read_csv(sciezka_do_pliku_csv, sep='\t', chunksize=chunk_size, low_memory=False, dtype=str)
        
        for chunk in dane_chunks:
            # --- TUTAJ ZACHODZI TRANSFORMACJA DANYCH ---
            # (Gdy podłączymy prawdziwy plik ClinVar, dopasujemy nazwy kolumn)
            
            # Zapis do bazy danych - błyskawiczny insert
            # W środowisku produkcyjnym mapujemy tutaj kolumny z pliku na naszą tabelę
            chunk.to_sql('temp_import', conn, if_exists='append', index=False)
            
            licznik_wierszy += len(chunk)
            print(f"   Przetworzono: {licznik_wierszy:,} markerów...")
            
        print(f"✅ Import zakończony w {round(time.time() - start_time, 2)} sekund.")
        print(f"📊 Łącznie zaimportowano {licznik_wierszy:,} wierszy do tabeli tymczasowej.")
        
    except Exception as e:
        print(f"❌ Wystąpił błąd podczas importu: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("--- SYSTEM BUDOWY POTĘŻNEJ BAZY DNA ---")
    przygotuj_strukture_bazy()
    
    # Plik docelowy, który będziemy zasysać (na razie to tylko deklaracja)
    plik_zrodlowy = "prawdziwa_baza_clinvar.txt"
    importuj_masowe_dane(plik_zrodlowy)
