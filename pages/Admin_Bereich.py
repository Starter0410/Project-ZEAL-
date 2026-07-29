import streamlit as st
import datenbank as db

st.set_page_config(page_title="Admin-Bereich", layout="wide")

st.title("🔐 Admin-Bereich (Stammdaten & Aufträge)")
st.write("Hier werden die Hintergrund-Datenbanken und Dropdown-Optionen gepflegt.")

# Passwort-Abfrage
admin_passwort = st.text_input("Admin-Passwort eingeben:", type="password")

# Definiere dein Admin-Passwort (kannst du hier anpassen)
if admin_passwort == "admin123":
    st.success("Passwort korrekt! Zugriff gewährt.")
    st.divider()

    tab_auftraege, tab_dropdowns = st.tabs(["📁 Aufträge verwalten", "⚙️ Dropdown-Werte & Normen pflegen"])

    # --- TAB 1: AUFTRÄGE VERWALTEN ---
    with tab_auftraege:
        st.subheader("Neuen Auftrag anlegen")
        with st.form("neuer_auftrag_form"):
            col1, col2 = st.columns(2)
            with col1:
                n_auftrag = st.text_input("Auftrags-Nummer (z.B. SEMS256)")
                n_teile_nr = st.text_input("Teilenummer")
                n_bezeichnung = st.text_input("Teilebezeichnung")
            with col2:
                n_charge = st.text_input("Charge")
                n_fremdcharge = st.text_input("Fremdcharge")
                n_vorgabe = st.text_input("Prüfvorgabe (QP-Nummer)")
                n_werkstoff = st.text_input("Werkstoff")
                
            submitted = st.form_submit_button("Auftrag speichern")
            if submitted and n_auftrag:
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO auftraege VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (n_auftrag, n_teile_nr, n_bezeichnung, n_charge, n_fremdcharge, n_vorgabe, n_werkstoff)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Auftrag {n_auftrag} erfolgreich gespeichert!")
                except Exception as e:
                    st.error(f"Fehler beim Speichern (Auftrag existiert evtl. schon): {e}")

        st.divider()
        st.subheader("Aktuelle Aufträge in der Datenbank")
        df_auftraege = db.get_all_auftraege_df()
        st.dataframe(df_auftraege, use_container_width=True)

    # --- TAB 2: DROPDOWNS PFLEGEN ---
    with tab_dropdowns:
        st.subheader("Optionen für Dropdown-Felder hinzufügen")
        with st.form("neue_option_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                sel_verfahren = st.selectbox("Prüfverfahren", ["MT", "UT", "PT"])
            with c2:
                sel_kategorie = st.selectbox("Kategorie / Feld", ["Prüf-Norm", "Zulässigkeitskrit.", "Magnetisierungstechn.", "Prüfkopf / Frequenz", "Koppelmittel", "Eindringmittel System"])
            with c3:
                neuer_wert = st.text_input("Neuer Wert (z.B. ASTM E709)")
                
            btn_add = st.form_submit_button("Wert zur Datenbank hinzufügen")
            if btn_add and neuer_wert:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO stammdaten (verfahren, kategorie, wert) VALUES (?, ?, ?)",
                    (sel_verfahren, sel_kategorie, neuer_wert)
                )
                conn.commit()
                conn.close()
                st.success(f"Wert '{neuer_wert}' für {sel_verfahren} ({sel_kategorie}) hinzugefügt!")

        st.divider()
        st.subheader("Vorhandene Stammdaten-Einträge")
        conn = db.get_connection()
        df_stammdaten = pd.read_sql("SELECT * FROM stammdaten", conn)
        conn.close()
        st.dataframe(df_stammdaten, use_container_width=True)

elif admin_passwort != "":
    st.error("Falsches Passwort!")
else:
    st.info("Bitte gib das Admin-Passwort ein, um den Administrationsbereich freizuschalten.")