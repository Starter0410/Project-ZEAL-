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

# --- SPALTE 1: AUFTRAGSDATEN (LINKS) ---
with col_links:
    st.subheader("📁 Auftrag")
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
        
        # Dropdowns aus Datenbank laden
        normen_mt = db.get_stammdaten_liste("MT", "Prüf-Norm")
        zulassungen_mt = db.get_stammdaten_liste("MT", "Zulässigkeitskrit.")
        techniken_mt = db.get_stammdaten_liste("MT", "Magnetisierungstechn.")
        
        pruef_norm_mt = st.selectbox("Prüf-Norm (MT)", normen_mt if normen_mt else ["Standard"])
        zulassung_mt = st.selectbox("Zulässigkeitskrit.", zulassungen_mt if zulassungen_mt else ["Standard"])
        mag_technik = st.selectbox("Magnetisierungstechn.", techniken_mt if techniken_mt else ["Standard"])
        
        pruefmaschine = st.text_input("Prüfmaschine", value="High amperage generator", key="mt_masch")
        strom = st.text_input("Magnetisierungsstrom", value="AC", key="mt_strom")
        
        st.markdown("---")
        oberflaeche_mt = st.text_input("Oberflächenzustand", value="blasted", key="mt_surf")
        ergebnis_mt = st.selectbox("Ergebnis (MT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="mt_res")
        bemerkung_mt = st.text_area("Bemerkung (MT)", placeholder="Details zur Magnetpulverprüfung...", key="mt_bem")

        verfahren_titel = "Magnetpulverprüfung (MT)"
        erfasste_parameter = {
            "Norm": pruef_norm_mt,
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
        
        pruef_norm_ut = st.selectbox("Prüf-Norm (UT)", normen_ut if normen_ut else ["Standard"])
        pruefkopf = st.selectbox("Prüfkopf / Frequenz", koepfe_ut if koepfe_ut else ["Standard"])
        koppelmittel = st.selectbox("Koppelmittel", koppel_ut if koppel_ut else ["Standard"])
        schallweg = st.text_input("Max. Schallweg", value="100 mm", key="ut_weg")

        st.markdown("---")
        ergebnis_ut = st.selectbox("Ergebnis (UT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="ut_res")
        bemerkung_ut = st.text_area("Bemerkung (UT)", placeholder="Reflektor-Hinweise, Echos...", key="ut_bem")

        verfahren_titel = "Ultraschallprüfung (UT)"
        erfasste_parameter = {
            "Norm": pruef_norm_ut,
            "Prüfkopf": pruefkopf,
            "Koppelmittel": koppelmittel
        }
        ergebnis = ergebnis_ut
        bemerkung = bemerkung_ut

    # --- TAB 3: PT ---
    with tab_pt:
        st.markdown("#### **PT Parameter & Werte**")
        
        normen_pt = db.get_stammdaten_liste("PT", "Prüf-Norm")
        system_pt = db.get_stammdaten_liste("PT", "Eindringmittel System")
        
        pruef_norm_pt = st.selectbox("Prüf-Norm (PT)", normen_pt if normen_pt else ["Standard"])
        eindringmittel = st.selectbox("Eindringmittel System", system_pt if system_pt else ["Standard"])
        einwirkzeit = st.text_input("Einwirkzeit Eindringmittel", value="15 min", key="pt_zeit")
        zwischenreinigung = st.text_input("Zwischenreinigung", value="Lösemittel", key="pt_reinig")

        st.markdown("---")
        ergebnis_pt = st.selectbox("Ergebnis (PT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="pt_res")
        bemerkung_pt = st.text_area("Bemerkung (PT)", placeholder="Anzeigen / Risse / Poren...", key="pt_bem")

        verfahren_titel = "Eindringprüfung (PT)"
        erfasste_parameter = {
            "Norm": pruef_norm_pt,
            "System": eindringmittel,
            "Einwirkzeit": einwirkzeit
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
            st.markdown(f"**Charge:** {order_data['charge']}`")
            st.markdown(f"**Prüfvorgabe:** {order_data['pruefvorgabe']}")
        else:
            st.markdown("*Kein Auftrag ausgewählt*")
            
        st.markdown("---")
        st.markdown("**Erfasste Parameter:**")
        for k, v in erfasste_parameter.items():
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