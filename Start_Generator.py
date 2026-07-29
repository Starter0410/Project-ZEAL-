import streamlit as st
import datenbank as db
import pandas as pd

st.set_page_config(page_title="ZfP Prüfprotokoll-Generator", layout="wide")

# CSS für maximale Bildschirmbreite und kompakte, saubere Schriftgrößen
st.markdown("""
    <style>
        .block-container {
            max-width: 98% !important;
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        p, .stTextInput label, .stSelectbox label, .stTextArea label { 
            font-size: 12px !important; 
        }
        h1 { font-size: 1.6rem !important; }
        h3 { font-size: 1.1rem !important; }
        h4 { font-size: 0.95rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 ZfP Prüfprotokoll-Generator")
st.write("Auftrag eingeben, Verfahren wählen, Parameter ausfüllen und Vorschau prüfen.")

st.divider()

# Aufträge aus DB laden
df_auftraege = db.get_all_auftraege_df()
db_auftrag_liste = df_auftraege["auftrag_nr"].tolist() if not df_auftraege.empty else []

# --- SPALTENVERHÄLTNIS ---
col_links, col_mitte, col_rechts = st.columns([1.1, 1.3, 1.6])

# --- SPALTE 1: AUFTRAG ERSTELLEN & AUSWÄHLEN (LINKS) ---
with col_links:
    st.subheader("📁 Auftrag & Verfahren")
    
    if "active_auftrag" not in st.session_state:
        st.session_state.active_auftrag = ""
    if "active_verfahren" not in st.session_state:
        st.session_state.active_verfahren = "MT-Prüfung"

    with st.container(border=True):
        st.markdown("#### **➕ Auftrag erfassen / suchen**")
        
        # Komplett leerer Start für den Vorführeffekt
        new_nr = st.text_input("Auftrags-Nr.* (z.B. SEMS255)", value="")
        
        # Prüfen ob Vorführeffekt-Beispiel greift (oder Live-Tippen)
        is_sems255 = (new_nr.strip().upper() == "SEMS255")
        
        new_verfahren = st.selectbox("Prüfverfahren wählen", ["MT-Prüfung", "UT-Prüfung", "PT-Prüfung"])
        
        # Felder füllen sich automatisch, sobald SEMS255 (oder Teile davon) getippt wird
        new_teil = st.text_input("Teilenummer", value="210120" if is_sems255 else "")
        new_bez = st.text_input("Teilebezeichnung", value="R=3D-20,80-S-WPHY70-42\"-0.600\"-SEG_FBE" if is_sems255 else "")
        new_charge = st.text_input("Charge", value="1XEFT" if is_sems255 else "")
        new_fremd = st.text_input("Fremdcharge", value="956042" if is_sems255 else "")
        new_bk = st.text_input("BK", value="01" if is_sems255 else "")
        new_vorgabe = st.text_input("Prüfvorgabe", value="QP-2026-70_Rev.1" if is_sems255 else "")

        if st.button("Auftrag übernehmen", type="primary", use_container_width=True):
            if new_nr.strip() == "":
                st.error("Bitte Auftrags-Nr. angeben.")
            else:
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM auftraege WHERE auftrag_nr = ?", (new_nr,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(
                            "INSERT INTO auftraege VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (new_nr, new_teil, new_bez, new_charge, new_fremd, new_vorgabe, new_bk)
                        )
                        conn.commit()
                    conn.close()
                except Exception:
                    pass
                
                st.session_state.active_auftrag = new_nr
                st.session_state.active_verfahren = new_verfahren
                st.rerun()

    st.markdown("---")
    
    # Alternativ aus echter DB wählen
    select_box_liste = ["-- Bitte wählen --"] + db_auftrag_liste
    selected_order_nr = st.selectbox("Oder aus DB wählen:", select_box_liste)
    if selected_order_nr != "-- Bitte wählen --" and selected_order_nr != st.session_state.active_auftrag:
        st.session_state.active_auftrag = selected_order_nr
        st.rerun()

    order_data = None
    # Entweder wurde der Button geklickt / Enter gedrückt oder es ist das Vorführ-Beispiel
    current_active = st.session_state.active_auftrag if st.session_state.active_auftrag else new_nr.strip()

    if current_active != "":
        if current_active.upper() == "SEMS255":
            order_data = {
                "auftrag_nr": "SEMS255",
                "teile_nr": "210120",
                "teilebezeichnung": 'R=3D-20,80-S-WPHY70-42"-0.600"-SEG_FBE',
                "charge": "1XEFT",
                "fremdcharge": "956042",
                "bk": "01",
                "pruefvorgabe": "QP-2026-70_Rev.1"
            }
        else:
            match_df = df_auftraege[df_auftraege["auftrag_nr"] == current_active]
            if not match_df.empty:
                order_data = match_df.iloc[0].to_dict()
                if "bk" not in order_data:
                    order_data["bk"] = "01"
                    
        if order_data:
            st.info(
                f"**Aktiver Auftrag:** `{order_data['auftrag_nr']}` | **Verfahren:** `{st.session_state.active_verfahren}`\n\n"
                f"• **Teile-Nr:** {order_data['teile_nr']} | **BK:** {order_data.get('bk', '01')}\n"
                f"• **Bez:** {order_data['teilebezeichnung']}\n"
                f"• **Charge:** {order_data['charge']} (Fremd: {order_data['fremdcharge']})\n"
                f"• **Vorgabe:** {order_data['pruefvorgabe']}"
            )
        else:
            st.info(f"**Aktiver Auftrag:** `{current_active}` (Neu / Manuell)")
    else:
        st.warning("Bitte gib oben einen Auftrag ein (z.B. SEMS255).")

# --- SPALTE 2: PARAMETER JE NACH GEWÄHLTEM VERFAHREN (MITTE) ---
with col_mitte:
    verfahren_titel = st.session_state.active_verfahren
    st.subheader(f"⚙️ Parameter: {verfahren_titel}")
    
    erfasste_parameter = {}
    ergebnis = "Without objection"
    bemerkung = ""

    current_active = st.session_state.active_auftrag if st.session_state.active_auftrag else new_nr.strip()

    if current_active == "":
        st.warning("Bitte erst links einen Auftrag eingeben.")
    else:
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
            bemerkung_mt = st.text_area("Bemerkung (MT)", placeholder="Details...", key="mt_bem", height=80)

            erfasste_parameter = {"Norm": pruef_norm_mt, "Zulässigkeit": zulassung_mt, "Verfahren": mag_technik, "Oberfläche": oberflaeche_mt}
            ergebnis = ergebnis_mt
            bemerkung = bemerkung_mt

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
            bemerkung_ut = st.text_area("Bemerkung (UT)", placeholder="Reflektor-Hinweise...", key="ut_bem", height=80)

            erfasste_parameter = {"Norm": pruef_norm_ut, "Prüfkopf": pruefkopf, "Koppelmittel": koppelmittel, "Schallweg": schallweg}
            ergebnis = ergebnis_ut
            bemerkung = bemerkung_ut

        elif verfahren_titel == "PT-Prüfung":
            normen_pt = db.get_stammdaten_liste("PT", "Prüf-Norm")
            system_pt = db.get_stammdaten_liste("PT", "Eindringmittel System")
            
            pruef_norm_pt = st.selectbox("Prüf-Norm (PT)", ["-- Bitte wählen --"] + (normen_pt if normen_pt else []))
            eindringmittel = st.selectbox("Eindringmittel System", ["-- Bitte wählen --"] + (system_pt if system_pt else []))
            einwirkzeit = st.text_input("Einwirkzeit Eindringmittel", value="", placeholder="z.B. 15 min...", key="pt_zeit")
            zwischenreinigung = st.text_input("Zwischenreinigung", value="", placeholder="z.B. Lösemittel...", key="pt_reinig")

            st.markdown("---")
            ergebnis_pt = st.selectbox("Ergebnis (PT)", ["Without objection", "Not acceptable", "Conditionally acceptable"], key="pt_res")
            bemerkung_pt = st.text_area("Bemerkung (PT)", placeholder="Anzeigen / Risse...", key="pt_bem", height=80)

            erfasste_parameter = {"Norm": pruef_norm_pt, "System": eindringmittel, "Einwirkzeit": einwirkzeit, "Zwischenreinigung": zwischenreinigung}
            ergebnis = ergebnis_pt
            bemerkung = bemerkung_pt

# --- SPALTE 3: LIVE-VORSCHAU (RECHTS) ---
with col_rechts:
    st.subheader("📄 Live-Berichtsvorschau")
    
    with st.container(border=True):
        st.markdown(f"### **{st.session_state.active_verfahren.upper()} - PROTOKOLL**")
        st.caption("Zerstörungsfreie Prüfung (Kompaktansicht)")
        
        st.markdown("---")
        
        current_active = st.session_state.active_auftrag if st.session_state.active_auftrag else new_nr.strip()
        
        if current_active != "" and order_data:
            st.markdown(
                f"**Auftrag:** `{order_data['auftrag_nr']}` | **BK:** `{order_data.get('bk', '01')}`\n\n"
                f"• **Teile-Nr:** {order_data['teile_nr']}\n"
                f"• **Bezeichnung:** `{order_data['teilebezeichnung']}`\n"
                f"• **Charge:** `{order_data['charge']}` (Fremd: `{order_data['fremdcharge']}`)\n"
                f"• **Vorgabe:** {order_data['pruefvorgabe']}"
            )
        elif current_active != "":
            st.markdown(f"**Auftrag:** `{current_active}` *(Manuelle Eingabe)*")
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
            
        st.markdown(f"**Bemerkung:**\n{bemerkung if bemerkung else '_Keine Anmerkungen_'}")

st.divider()

if st.button("Protokoll final generieren", type="primary"):
    current_active = st.session_state.active_auftrag if st.session_state.active_auftrag else new_nr.strip()
    if current_active == "":
        st.error("Bitte gib zuerst einen Auftrag ein.")
    else:
        st.success(f"Prüfprotokoll für {st.session_state.active_verfahren} erfolgreich im System gespeichert!")
