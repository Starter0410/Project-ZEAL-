import streamlit as st
import datenbank as db
import pandas as pd

st.set_page_config(page_title="ZfP Prüfprotokoll-Generator", layout="wide")

st.title("🔍 ZfP Prüfprotokoll-Generator")
st.write("Wähle links den Auftrag, in der Mitte das Prüfverfahren (Reiter mit Datenbank-Werten) und behalte rechts die Vorschau im Blick.")

st.divider()

# Aufträge aus DB laden
df_auftraege = db.get_all_auftraege_df()
auftrag_liste = ["-- Bitte wählen --"] + df_auftraege["auftrag_nr"].tolist() if not df_auftraege.empty else ["-- Bitte wählen --"]

# --- SPALTENVERHÄLTNIS ---
col_links, col_mitte, col_rechts = st.columns([0.8, 1.4, 1.8])

# --- SPALTE 1: AUFTRAGSDATEN & NEU ERSTELLEN (LINKS) ---
with col_links:
    st.subheader("📁 Auftrag")
    
    # Session State für das Aufklappen des "Neuen Auftrag"-Formulars
    if "show_new_order_form" not in st.session_state:
        st.session_state.show_new_order_form = False

    if st.button("➕ Neuen Auftrag anlegen", use_container_width=True):
        st.session_state.show_new_order_form = not st.session_state.show_new_order_form

    # Eingabemaske für neuen Auftrag
    if st.session_state.show_new_order_form:
        with st.container(border=True):
            st.markdown("#### **Neuen Auftrag erfassen**")
            new_nr = st.text_input("Auftrags-Nr.*")
            new_teil = st.text_input("Teilenummer")
            new_bez = st.text_input("Teilebezeichnung")
            new_charge = st.text_input("Charge")
            new_fremd = st.text_input("Fremdcharge")
            new_vorgabe = st.text_input("Prüfvorgabe")
            new_werkstoff = st.text_input("Werkstoff")

            if st.button("Auftrag in DB speichern", type="primary"):
                if new_nr.strip() == "":
                    st.error("Bitte eine Auftrags-Nr. angeben.")
                else:
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO auftraege VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (new_nr, new_teil, new_bez, new_charge, new_fremd, new_vorgabe, new_werkstoff)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Auftrag {new_nr} gespeichert!")
                        st.session_state.show_new_order_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler (Nr. existiert evtl. bereits): {e}")

    st.markdown("---")
    selected_order_nr = st.selectbox("Auftrag wählen:", auftrag_liste)

    order_data = None
    if selected_order_nr != "-- Bitte wählen --":
        row = df_auftraege[df_auftraege["auftrag_nr"] == selected_order_nr].iloc[0]
        order_data = row.to_dict()
        
        st.info(
            f"**Auftrag:**\n`{order_data['auftrag_nr']}`\n\n"
            f"**Teilenummer:**\n`{order_data['teile_nr']}`\n\n"
            f"**Teilebezeichnung:**\n`{order_data['teilebezeichnung']}`\n\n"
            f"**Charge:**\n`{order_data['charge']}`\n\n"
            f"**Fremdcharge:**\n`{order_data['fremdcharge']}`\n\n"
            f"**Prüfvorgabe:**\n`{order_data['pruefvorgabe']}`"
        )
    else:
        st.warning("Bitte Auftrag wählen.")

# --- SPALTE 2: DYNAMISCHE PRÜFVERFAHREN & DROPDOWNS (MITTE) ---
with col_mitte:
    st.subheader("⚙️ Prüfverfahren")
    
    tab_mt, tab_ut, tab_pt = st.tabs(["🧲 MT-Prüfung", "🔊 UT-Prüfung", "🔴 PT-Prüfung"])
    
    verfahren_titel = "MT-Prüfung"
    erfasste_parameter = {}
    ergebnis = "Without objection"
    bemerkung = ""

    # --- TAB 1: MT ---
    with tab_mt:
        st.markdown("#### **MT Parameter & Werte**")
        
        normen_mt = db.get_stammdaten_liste("MT", "Prüf-Norm")
        zulassungen_mt = db.get_stammdaten_liste("MT", "Zulässigkeitskrit.")
        techniken_mt = db.get_stammdaten_liste("MT", "Magnetisierungstechn.")
        
        # Leere Standardauswahl erzwingen (optionaler Leerwert am Anfang)
        pruef_norm_mt = st.selectbox("Prüf-Norm (MT)", ["-- Bitte wählen --"] + (normen_mt if normen_mt else []))
        zulassung_mt = st.selectbox("Zulässigkeitskrit.", ["-- Bitte wählen --"] + (zulassungen_mt if zulassungen_mt else []))
        mag_technik = st.selectbox("Magnetisierungstechn.", ["-- Bitte wählen --"] + (techniken_mt if techniken_mt else []))
        
        # Leere Felder statt fixer Vorgaben
        pruefmaschine = st.text_input("Prüfmaschine", value="", placeholder="Geraet eingeben...", key="mt_masch")
        strom = st.text_input("Magnetisierungsstrom", value="", placeholder="z.B. AC / DC...", key="mt_strom")
        
        st.markdown("---")
        oberflaeche_mt = st.text_input("Oberflächenzustand", value="", placeholder="z.B. gestrahlt...", key="mt_surf")
        ergebnis_mt = st.selectbox("Ergebnis (MT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="mt_res")
        bemerkung_mt = st.text_area("Bemerkung (MT)", placeholder="Details zur Magnetpulverprüfung...", key="mt_bem")

        verfahren_titel = "Magnetpulverprüfung (MT)"
        erfasste_parameter = {
            "Norm": pruef_norm_mt,
            "Zulässigkeit": zulassung_mt,
            "Verfahren": mag_technik,
            "Oberfläche": oberflaeche_mt
        }
        ergebnis = ergebnis_mt
        bemerkung = bemerkung_mt

    # --- TAB 2: UT ---
    with tab_ut:
        st.markdown("#### **UT Parameter & Werte**")
        
        normen_ut = db.get_stammdaten_liste("UT", "Prüf-Norm")
        koepfe_ut = db.get_stammdaten_liste("UT", "Prüfkopf / Frequenz")
        koppel_ut = db.get_stammdaten_liste("UT", "Koppelmittel")
        
        pruef_norm_ut = st.selectbox("Prüf-Norm (UT)", ["-- Bitte wählen --"] + (normen_ut if normen_ut else []))
        pruefkopf = st.selectbox("Prüfkopf / Frequenz", ["-- Bitte wählen --"] + (koepfe_ut if koepfe_ut else []))
        koppelmittel = st.selectbox("Koppelmittel", ["-- Bitte wählen --"] + (koppel_ut if koppel_ut else []))
        schallweg = st.text_input("Max. Schallweg", value="", placeholder="z.B. 100 mm...", key="ut_weg")

        st.markdown("---")
        ergebnis_ut = st.selectbox("Ergebnis (UT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="ut_res")
        bemerkung_ut = st.text_area("Bemerkung (UT)", placeholder="Reflektor-Hinweise, Echos...", key="ut_bem")

        verfahren_titel = "Ultraschallprüfung (UT)"
        erfasste_parameter = {
            "Norm": pruef_norm_ut,
            "Prüfkopf": pruefkopf,
            "Koppelmittel": koppelmittel,
            "Schallweg": schallweg
        }
        ergebnis = ergebnis_ut
        bemerkung = bemerkung_ut

    # --- TAB 3: PT ---
    with tab_pt:
        st.markdown("#### **PT Parameter & Werte**")
        
        normen_pt = db.get_stammdaten_liste("PT", "Prüf-Norm")
        system_pt = db.get_stammdaten_liste("PT", "Eindringmittel System")
        
        pruef_norm_pt = st.selectbox("Prüf-Norm (PT)", ["-- Bitte wählen --"] + (normen_pt if normen_pt else []))
        eindringmittel = st.selectbox("Eindringmittel System", ["-- Bitte wählen --"] + (system_pt if system_pt else []))
        einwirkzeit = st.text_input("Einwirkzeit Eindringmittel", value="", placeholder="z.B. 15 min...", key="pt_zeit")
        zwischenreinigung = st.text_input("Zwischenreinigung", value="", placeholder="z.B. Lösemittel...", key="pt_reinig")

        st.markdown("---")
        ergebnis_pt = st.selectbox("Ergebnis (PT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="pt_res")
        bemerkung_pt = st.text_area("Bemerkung (PT)", placeholder="Anzeigen / Risse / Poren...", key="pt_bem")

        verfahren_titel = "Eindringprüfung (PT)"
        erfasste_parameter = {
            "Norm": pruef_norm_pt,
            "System": eindringmittel,
            "Einwirkzeit": einwirkzeit,
            "Zwischenreinigung": zwischenreinigung
        }
        ergebnis = ergebnis_pt
        bemerkung = bemerkung_pt

# --- SPALTE 3: LIVE-VORSCHAU (RECHTS) ---
with col_rechts:
    st.subheader("📄 Live-Berichtsvorschau")
    
    with st.container(border=True):
        st.markdown(f"### **{verfahren_titel.upper()} - PROTOKOLL**")
        st.caption("Zerstörungsfreie Prüfung")
        
        st.markdown("---")
        
        if order_data:
            st.markdown(f"**Auftrag:** `{order_data['auftrag_nr']}`")
            st.markdown(f"**Teile-Nr.:** {order_data['teile_nr']}")
            st.markdown(f"**Bezeichnung:** `{order_data['teilebezeichnung']}`")
            st.markdown(f"**Charge:** `{order_data['charge']}`")
            st.markdown(f"**Prüfvorgabe:** {order_data['pruefvorgabe']}")
        else:
            st.markdown("*Kein Auftrag ausgewählt*")
            
        st.markdown("---")
        st.markdown("**Erfasste Parameter:**")
        for k, v in erfasste_parameter.items():
            # Zeige nur Parameter an, die auch aktiv gewählt/ausgefüllt wurden
            if v and v != "-- Bitte wählen --":
                st.markdown(f"- {k}: `{v}`")
        
        st.markdown("---")
        st.markdown("**Befund:**")
        if "Without objection" in ergebnis:
            st.success(ergebnis)
        else:
            st.error(ergebnis)
            
        st.markdown(f"**Bemerkung:**\n{bemerkung if bemerkung else '_Keine Anmerkungen_'}")

st.divider()

if st.button("Protokoll final generieren", type="primary"):
    if selected_order_nr == "-- Bitte wählen --":
        st.error("Bitte wähle zuerst einen Auftrag aus.")
    else:
        st.success(f"Prüfprotokoll für {verfahren_titel} erfolgreich im System gespeichert!")
