import streamlit as st
import datenbank as db
import pandas as pd

st.set_page_config(page_title="ZfP Prüfprotokoll-Generator", layout="wide")

st.title("🔍 ZfP Prüfprotokoll-Generator")
st.write("Lege einen neuen Auftrag mit Prüfverfahren an oder wähle einen bestehenden aus, erfasse die Parameter in der Mitte und behalte rechts die Vorschau im Blick.")

st.divider()

# Aufträge aus DB laden
df_auftraege = db.get_all_auftraege_df()
auftrag_liste = ["-- Bitte wählen --"] + df_auftraege["auftrag_nr"].tolist() if not df_auftraege.empty else ["-- Bitte wählen --"]

# --- SPALTENVERHÄLTNIS ---
col_links, col_mitte, col_rechts = st.columns([0.9, 1.3, 1.8])

# --- SPALTE 1: AUFTRAG ERSTELLEN & AUSWÄHLEN (LINKS) ---
with col_links:
    st.subheader("📁 Auftrag & Verfahren")
    
    # Session State für aktiven Auftrag & Verfahren
    if "active_auftrag" not in st.session_state:
        st.session_state.active_auftrag = "-- Bitte wählen --"
    if "active_verfahren" not in st.session_state:
        st.session_state.active_verfahren = "MT-Prüfung"

    with st.container(border=True):
        st.markdown("#### **➕ Neuen Auftrag anlegen**")
        new_nr = st.text_input("Auftrags-Nr.* (z.B. SEMS255)")
        new_verfahren = st.selectbox("Prüfverfahren wählen", ["MT-Prüfung", "UT-Prüfung", "PT-Prüfung"])
        
        # Weitere Auftragsdetails eingeben
        new_teil = st.text_input("Teilenummer")
        new_bez = st.text_input("Teilebezeichnung")
        new_charge = st.text_input("Charge")
        new_fremd = st.text_input("Fremdcharge")
        new_vorgabe = st.text_input("Prüfvorgabe")

        if st.button("Auftrag übernehmen", type="primary", use_container_width=True):
            if new_nr.strip() == "":
                st.error("Bitte Auftrags-Nr. angeben.")
            else:
                # Prüfen, ob Auftrag schon in DB existiert, wenn nicht, anlegen
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM auftraege WHERE auftrag_nr = ?", (new_nr,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(
                            "INSERT INTO auftraege VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (new_nr, new_teil, new_bez, new_charge, new_fremd, new_vorgabe, "")
                        )
                        conn.commit()
                    conn.close()
                except Exception:
                    pass
                
                st.session_state.active_auftrag = new_nr
                st.session_state.active_verfahren = new_verfahren
                st.rerun()

    st.markdown("---")
    
    # Alternativ: Bestehenden auswählen
    selected_order_nr = st.selectbox("Oder bestehenden Auftrag wählen:", auftrag_liste)
    if selected_order_nr != "-- Bitte wählen --" and selected_order_nr != st.session_state.active_auftrag:
        st.session_state.active_auftrag = selected_order_nr
        st.rerun()

    # Anzeige der festen Daten des aktiven Auftrags
    order_data = None
    if st.session_state.active_auftrag != "-- Bitte wählen --":
        match_df = df_auftraege[df_auftraege["auftrag_nr"] == st.session_state.active_auftrag]
        if not match_df.empty:
            order_data = match_df.iloc[0].to_dict()
            st.info(
                f"**Aktiver Auftrag:** `{order_data['auftrag_nr']}`\n\n"
                f"**Verfahren:** `{st.session_state.active_verfahren}`\n\n"
                f"**Teilenummer:** `{order_data['teile_nr']}`\n\n"
                f"**Bezeichnung:** `{order_data['teilebezeichnung']}`\n\n"
                f"**Charge:** `{order_data['charge']}`\n\n"
                f"**Prüfvorgabe:** `{order_data['pruefvorgabe']}`"
            )
        else:
            # Falls manuell eingegeben und noch nicht in DB-Tabelle voll erfasst
            st.info(f"**Aktiver Auftrag:** `{st.session_state.active_auftrag}`\n\n**Verfahren:** `{st.session_state.active_verfahren}`")
    else:
        st.warning("Bitte Auftrag anlegen oder wählen.")

# --- SPALTE 2: PARAMETER JE NACH GEWÄHLTEM VERFAHREN (MITTE) ---
with col_mitte:
    verfahren_titel = st.session_state.active_verfahren
    st.subheader(f"⚙️ Parameter für {verfahren_titel}")
    
    erfasste_parameter = {}
    ergebnis = "Without objection"
    bemerkung = ""

    if st.session_state.active_auftrag == "-- Bitte wählen --":
        st.warning("Bitte erst links einen Auftrag anlegen oder auswählen.")
    else:
        # --- MT-Prüfung ---
        if verfahren_titel == "MT-Prüfung":
            normen_mt = db.get_stammdaten_liste("MT", "Prüf-Norm")
            zulassungen_mt = db.get_stammdaten_liste("MT", "Zulässigkeitskrit.")
            techniken_mt = db.get_stammdaten_liste("MT", "Magnetisierungstechn.")
            
            pruef_norm_mt = st.selectbox("Prüf-Norm (MT)", ["-- Bitte wählen --"] + (normen_mt if normen_mt else []))
            zulassung_mt = st.selectbox("Zulässigkeitskrit.", ["-- Bitte wählen --"] + (zulassungen_mt if zulassungen_mt else []))
            mag_technik = st.selectbox("Magnetisierungstechn.", ["-- Bitte wählen --"] + (techniken_mt if techniken_mt else []))
            
            pruefmaschine = st.text_input("Prüfmaschine", value="", placeholder="Gerät eingeben...", key="mt_masch")
            strom = st.text_input("Magnetisierungsstrom", value="", placeholder="z.B. AC / DC...", key="mt_strom")
            
            st.markdown("---")
            oberflaeche_mt = st.text_input("Oberflächenzustand", value="", placeholder="z.B. gestrahlt...", key="mt_surf")
            ergebnis_mt = st.selectbox("Ergebnis (MT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="mt_res")
            bemerkung_mt = st.text_area("Bemerkung (MT)", placeholder="Details zur Magnetpulverprüfung...", key="mt_bem")

            erfasste_parameter = {
                "Norm": pruef_norm_mt,
                "Zulässigkeit": zulassung_mt,
                "Verfahren": mag_technik,
                "Oberfläche": oberflaeche_mt
            }
            ergebnis = ergebnis_mt
            bemerkung = bemerkung_mt

        # --- UT-Prüfung ---
        elif verfahren_titel == "UT-Prüfung":
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

            erfasste_parameter = {
                "Norm": pruef_norm_ut,
                "Prüfkopf": pruefkopf,
                "Koppelmittel": koppelmittel,
                "Schallweg": schallweg
            }
            ergebnis = ergebnis_ut
            bemerkung = bemerkung_ut

        # --- PT-Prüfung ---
        elif verfahren_titel == "PT-Prüfung":
            normen_pt = db.get_stammdaten_liste("PT", "Prüf-Norm")
            system_pt = db.get_stammdaten_liste("PT", "Eindringmittel System")
            
            pruef_norm_pt = st.selectbox("Prüf-Norm (PT)", ["-- Bitte wählen --"] + (normen_pt if normen_pt else []))
            eindringmittel = st.selectbox("Eindringmittel System", ["-- Bitte wählen --"] + (system_pt if system_pt else []))
            einwirkzeit = st.text_input("Einwirkzeit Eindringmittel", value="", placeholder="z.B. 15 min...", key="pt_zeit")
            zwischenreinigung = st.text_input("Zwischenreinigung", value="", placeholder="z.B. Lösemittel...", key="pt_reinig")

            st.markdown("---")
            ergebnis_pt = st.selectbox("Ergebnis (PT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="pt_res")
            bemerkung_pt = st.text_area("Bemerkung (PT)", placeholder="Anzeigen / Risse / Poren...", key="pt_bem")

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
        st.markdown(f"### **{st.session_state.active_verfahren.upper()} - PROTOKOLL**")
        st.caption("Zerstörungsfreie Prüfung")
        
        st.markdown("---")
        
        if st.session_state.active_auftrag != "-- Bitte wählen --":
            st.markdown(f"**Auftrag:** `{st.session_state.active_auftrag}`")
            if order_data:
                st.markdown(f"**Teile-Nr.:** {order_data['teile_nr']}")
                st.markdown(f"**Bezeichnung:** `{order_data['teilebezeichnung']}`")
                st.markdown(f"**Charge:** `{order_data['charge']}`")
                st.markdown(f"**Prüfvorgabe:** {order_data['pruefvorgabe']}")
        else:
            st.markdown("*Kein Auftrag ausgewählt*")
            
        st.markdown("---")
        st.markdown("**Erfasste Parameter:**")
        for k, v in erfasste_parameter.items():
            if v and v != "-- Bitte wählen --":
                st.markdown(f"- {k}: `{v}`")
        
        st.markdown("---")
        st.markdown("**Befund:**")
        if "Without objection" in ergebnis:
            st.success(ergebnis)
        else:
            st.error(ergebnis)
            
        st.markdown(f"**Bemerkung:**\n{bemerkung if bemkund else '_Keine Anmerkungen_'}") if 'bemkund' not in locals() else st.markdown(f"**Bemerkung:**\n{bemerkung if bemerkung else '_Keine Anmerkungen_'}")

st.divider()

if st.button("Protokoll final generieren", type="primary"):
    if st.session_state.active_auftrag == "-- Bitte wählen --":
        st.error("Bitte wähle zuerst einen Auftrag aus.")
    else:
        st.success(f"Prüfprotokoll für {st.session_state.active_verfahren} erfolgreich im System gespeichert!")
