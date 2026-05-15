import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- DATEN-SPEICHERUNG ---
DATEI_NAME = "Imker_Verwaltung.xlsx"

def speichere_in_excel(blatt, daten):
    jetzt = datetime.now().strftime("%d.%m.%Y")
    eintrag = {'Datum': jetzt}
    eintrag.update(daten)
    df_neu = pd.DataFrame([eintrag])
    
    if os.path.exists(DATEI_NAME):
        with pd.ExcelWriter(DATEI_NAME, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            try:
                df_alt = pd.read_excel(DATEI_NAME, sheet_name=blatt)
                pd.concat([df_alt, df_neu], ignore_index=True).to_excel(writer, sheet_name=blatt, index=False)
            except:
                df_neu.to_excel(writer, sheet_name=blatt, index=False)
    else:
        df_neu.to_excel(DATEI_NAME, sheet_name=blatt, index=False)
    st.success(f"Gespeichert in {blatt}!")

# --- APP DESIGN ---
st.set_page_config(page_title="Imker App", page_icon="🐝")
st.title("🐝 Bastians Imker-Zentrale")

# Menü-Auswahl (Deine Kategorien)
kategorie = st.sidebar.radio("MENÜ", ["Dashboard", "🔍 Durchschau", "📋 Bestandsbuch", "🍯 Honigernte", "🥣 Fütterung", "📦 Lager", "✅ Todo/Termine"])

if kategorie == "Dashboard":
    st.subheader("Übersicht")
    col1, col2, col3 = st.columns(3)
    col1.metric("Stände", "Stand 1")
    col2.metric("Todos", "Offen")
    col3.metric("Termine", "Keine")

elif kategorie == "🔍 Durchschau":
    st.header("Völkerdurchsicht")
    v_nr = st.number_input("Volk Nr.", min_value=1, step=1)
    k_vorh = st.radio("Königin vorhanden?", ["Nein", "Ja"], index=0)
    stifte = st.radio("Stifte / Brut?", ["Nein", "Ja"], index=0)
    sanftmut = st.select_slider("Sanftmut", options=["1", "2", "3", "4", "5"], value="5")
    schwarm = st.select_slider("Schwarmstimmung", options=["1", "2", "3", "4", "5"], value="1")
    notiz = st.text_area("Bemerkung")
    if st.button("Durchschau speichern"):
        speichere_in_excel(f"Volk_{v_nr}", {"Typ": "Durchschau", "Königin": k_vorh, "Stifte": stifte, "Sanftmut": sanftmut, "Schwarm": schwarm, "Notiz": notiz})

elif kategorie == "📋 Bestandsbuch":
    st.header("Amtlicher Arzneimittel-Nachweis")
    v_liste = st.text_input("Welche Völker? (z.B. 1,2,3)")
    mittel = st.text_input("Arzneimittel & Charge")
    menge = st.text_input("Dosierung")
    wartezeit = st.number_input("Wartezeit (Tage)", 0)
    if st.button("Bestandsbuch-Eintrag"):
        d = {"Mittel": mittel, "Menge": menge, "Wartezeit": wartezeit}
        speichere_in_excel("Bestandsbuch_Gesamt", d)
        for v in v_liste.split(","):
            speichere_in_excel(f"Volk_{v.strip()}", d)

elif kategorie == "🍯 Honigernte":
    st.header("Ernte erfassen")
    v_nr = st.number_input("Volk Nr.", 1)
    sorte = st.selectbox("Sorte", ["Frühtracht", "Raps", "Wald", "Sommer"])
    kg = st.number_input("Menge in kg", 0.0)
    if st.button("Ernte speichern"):
        speichere_in_excel("Honigernte_Gesamt", {"Sorte": sorte, "kg": kg})
        speichere_in_excel(f"Volk_{v_nr}", {"Typ": "Ernte", "kg": kg})