import sqlite3
import pandas as pd

DB_NAME = "ndt_stammdaten.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tabelle für Aufträge
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auftraege (
            auftrag_nr TEXT PRIMARY KEY,
            teile_nr TEXT,
            teilebezeichnung TEXT,
            charge TEXT,
            fremdcharge TEXT,
            pruefvorgabe TEXT,
            werkstoff TEXT
        )
    """)
    
    # 2. Tabelle für Stammdaten / Dropdown-Optionen (pro Verfahren)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stammdaten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verfahren TEXT,
            kategorie TEXT,
            wert TEXT
        )
    """)
    
    # Standard-Einfügungen falls Tabellen leer sind
    cursor.execute("SELECT COUNT(*) FROM auftraege")
    if cursor.fetchone()[0] == 0:
        sample_auftraege = [
            ("SEMS255", "210120", "R=3D-20,80-S-WPHY70-42\"-0.600\"-SEG_FBE", "1XEFT", "956042", "QP-2026-70_Rev.1", "WPHY70"),
            ("PRJ-2026-101", "998877", "Druckbehälter Behälter-Typ B", "CH-442", "112233", "QP-2026-10_Rev.0", "P355GH")
        ]
        cursor.executemany("INSERT INTO auftraege VALUES (?, ?, ?, ?, ?, ?, ?)", sample_auftraege)

    cursor.execute("SELECT COUNT(*) FROM stammdaten")
    if cursor.fetchone()[0] == 0:
        sample_stammdaten = [
            # MT
            ("MT", "Prüf-Norm", "ASTM E709"),
            ("MT", "Prüf-Norm", "ASME Sec. V Art.7"),
            ("MT", "Zulässigkeitskrit.", "ASME Sec. VIII Div.1 App6"),
            ("MT", "Magnetisierungstechn.", "longitudinal magnetizing"),
            ("MT", "Prüfmaschine", "High amperage generator"),
            ("MT", "Magnetisierungsstrom", "AC"),
            ("MT", "Magnetpulver Type", "Fluoflux Konzentrat MF-655 WB"),
            # UT
            ("UT", "Prüf-Norm", "EN ISO 17640"),
            ("UT", "Prüf-Norm", "EN 10246"),
            ("UT", "Prüfkopf / Frequenz", "4 MHz, 45°"),
            ("UT", "Prüfkopf / Frequenz", "2 MHz, 60°"),
            ("UT", "Koppelmittel", "Ultraschallgel"),
            # PT
            ("PT", "Prüf-Norm", "EN ISO 3452-1"),
            ("PT", "Eindringmittel System", "MR Turco / Type II"),
            ("PT", "Zwischenreinigung", "Lösemittel")
        ]
        cursor.executemany("INSERT INTO stammdaten (verfahren, kategorie, wert) VALUES (?, ?, ?)", sample_stammdaten)

    conn.commit()
    conn.close()

# Hilfsfunktionen zum Laden
def get_all_auftraege_df():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM auftraege", conn)
    conn.close()
    return df

def get_auftrag_dict(auftrag_nr):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM auftrag_nr WHERE auftrag_nr = ?", (auftrag_nr,))
    # Besser über Pandas oder direkt fetchone:
    query = f"SELECT * FROM auftraege WHERE auftrag_nr = '{auftrag_nr}'"
    df = pd.read_sql(query, conn)
    conn.close()
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def get_stammdaten_liste(verfahren, kategorie):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT wert FROM stammdaten WHERE verfahren = ? AND kategorie = ?", (verfahren, kategorie))
    ergebnisse = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ergebnisse

# Beim Import initialisieren
init_db()