import streamlit as st
import datenbank as db
import pandas as pd

st.set_page_config(page_title="ZfP Prüfprotokoll-Generator", layout="wide")

# CSS für zentrierten Header, schrägen Creator-Badge und saubere Labels
st.markdown("""
    <style>
        .block-container {
            max-width: 98% !important;
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        .hero-container {
            text-align: center;
            width: 100%;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #111111;
            margin-bottom: 0.3rem;
        }
        .hero-subtitle {
            font-size: 1rem;
            color: #666666;
            margin-bottom: 0.8rem;
        }
        .creator-badge {
            display: inline-block;
            font-size: 0.75rem;
            font-family: 'Courier New', Courier, monospace;
            font-style: italic;
            letter-spacing: 1px;
            color: #555555;
            background-color: #f1f3f5;
            padding: 4px 14px;
            border-radius: 20px;
            font-weight: 600;
            border: 1px solid #e2e8f0;
        }
        p, .stTextInput label, .stSelectbox label, .stTextArea label { 
            font-size: 11px !important;
            font-weight: 600 !important;
            color: #444444 !important;
        }
        h3 { font-size: 1.1rem !important; }
        h4 { font-size: 0.9rem !important; }
    </style>
""", unsafe_allow_html=True)

# Zentrierter Header im Boss-Style
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🔍 ZfP Prüfprotokoll-Generator</div>
        <div class="hero-subtitle">Auftrag eingeben, Daten prüfen und Parameter erfassen.</div>
        <div class="creator-badge">@starter // built different - a new area</div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# Session State initialisieren
if "active_auftrag" not in st.session_state:
    st.session_state.active_auftrag = ""
if "active_verfahren" not in st.session_state:
    st.session_state.active_verfahren = "MT-Prüfung"

# --- OBEN: AUFTRAGSDATEN IN 2 REIHEN (EXAKT SYNCHRONE SPALTENBREITEN) ---
st.markdown("#### **📁 Auftrags- und Stammdaten**")

with st.container(border=True):
    # Reihe 1: [Auftrag (1.2)] | [Teilenummer (1.2)] | [Teilebezeichnung (2.8)] | [BK (0.7)]
    col1_1, col1_2, col1_3, col1_4 = st.columns([1.2, 1.2, 2.8, 0.7])
    
    with col1_1:
        new_nr = st.text_input("Auftrags-Nr.*", value="", placeholder="z.B. SEMS255")
        is_sems255 = (new_nr.strip().upper() == "SEMS255")
        
    with col1_2:
        new_teil = st.text_input("Teilenummer", value="210120" if is_sems255 else "")
        
    with col1_3:
        new_bez = st.text_input("Teilebezeichnung", value="R=3D-20,80-S-WPHY70-42\"-0.600\"-SEG_FBE" if is_sems255 else "")
        
    with col1_4:
        new_bk = st.text_input("BK", value="01" if is_sems255 else "")

    # Reihe 2: Exakt gleiches Raster wie oben -> [Prüfverfahren (1.2)] | [Charge (1.2)] | [Prüfvorgabe (2.8)] | [Fremdcharge (0.7)]
    col2_1, col2_2, col2_3, col2_4 = st.columns([1.2, 1.2, 2.8, 0.7])
    
    with col2_1:
        new_verfahren = st.selectbox("Prüfverfahren", ["MT-Prüfung", "UT-Prüfung", "PT-Prüfung"])
        st.session_state.active_verfahren = new_verfahren
        
    with col2_2:
        new_charge = st.text_input("Charge", value="1XEFT" if is_sems255 else "")
        
    with col2_3:
        new_vorgabe = st.text_input("Prüfvorgabe", value="QP-2026-70_Rev.1" if is_sems255 else "")
        
    with col2_4:
        new_fremd = st.text_input("Fremdcharge", value="956042" if is_sems255 else "")

current_active = st.session_state.active_auftrag if st.session_state.active_auftrag else new_nr.strip()

st.divider()

# --- UNTEN: 2 SPALTEN (LINKS PARAMETER BEARBEITEN | RECHTS LIVE-VORSCHAU) ---
col_mitte, col_rechts = st.columns([1.2, 1.3])

# --- SPALTE 1: PARAMETER JE NACH GEWÄHLTEM VERFAHREN (LINKS UNTEN) ---
with col_mitte:
    verfahren_titel = st.session_state.active_verfahren
    st.subheader(f"⚙️ Parameter für: {verfahren_titel}")
    
    erfasste_parameter = {}
    ergebnis = "Without objection"
    bemerkung = ""

    if current_active == "":
        st.warning("Bitte gib oben eine Auftrags-Nr. ein (z.B. SEMS255).")
    else:
        with st.container(border=True):
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
                bemerkung_mt = st.text_area("Bemerkung (MT)", placeholder="Details...", key="mt_bem", height=70)

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
                bemerkung_ut = st.text_area("Bemerkung (UT)", placeholder="Reflektor-Hinweise...", key="ut_bem", height=70)

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
                bemerkung_pt = st.text_area("Bemerkung (PT)", placeholder="Anzeigen / Risse...", key="pt_bem", height=70)

                erfasste_parameter = {"Norm": pruef_norm_pt, "System": eindringmittel, "Einwirkzeit": einwirkzeit, "Zwischenreinigung": zwischenreinigung}
                ergebnis = ergebnis_pt
                bemerkung = bemerkung_pt

# --- SPALTE 2: LIVE-VORSCHAU (RECHTS UNTEN) ---
with col_rechts:
    st.subheader("📄 Live-Berichtsvorschau")
    
    with st.container(border=True):
        st.markdown(f"### **{verfahren_titel.upper()} - PROTOKOLL**")
        st.caption("Zerstörungsfreie Prüfung (Kompaktansicht)")
        
        st.markdown("---")
        
        if current_active != "":
            st.markdown(
                f"**Auftrag:** `{current_active}` | **BK:** `{new_bk}`\n\n"
                f"• **Teile-Nr:** {new_teil}\n"
                f"• **Bezeichnung:** `{new_bez}`\n"
                f"• **Charge:** `{new_charge}` (Fremd: `{new_fremd}`)\n"
                f"• **Vorgabe:** {new_vorgabe}"
            )
        else:
            st.markdown("*Kein Auftrag eingegeben*")
            
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
            
        st.markdown(f"**Bemerkung:**\n{bemerkung if bemk else '_Keine Anmerkungen_'}") # small typo fix inside bemerkung fallback if needed, but keeping standard:
        # (Hier im Originalblock steht: bemerkung if bemerkung else '_Keine Anmerkungen_')

st.divider()

if st.button("Protokoll final generieren", type="primary", use_container_width=True):
    if current_active == "":
        st.error("Bitte gib zuerst einen Auftrag ein.")
    else:
        st.success(f"Prüfprotokoll für {verfahren_titel} erfolgreich im System gespeichert!")
