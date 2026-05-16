import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- GOOGLE SHEETS VERBINDUNG ---
def hole_google_tabelle():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    info = dict(st.secrets["gcp_service_account"])
    
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    return client.open("Imker_Daten")

def speichere_in_google(blatt_name, daten_dict):
    try:
        tabelle = hole_google_tabelle()
        
        # Sucht nach dem Tabellenblatt "Durchschau"
        try:
            worksheet = tabelle.worksheet(blatt_name)
        except gspread.exceptions.WorksheetNotFound:
            # Falls das Blatt doch nicht existiert, wird es neu erstellt
            worksheet = tabelle.add_worksheet(title=blatt_name, rows="500", cols="20")
            überschriften = ["Datum"] + list(daten_dict.keys())
            worksheet.append_row(überschriften)
            
        # Falls das Blatt existiert, aber komplett leer ist, Überschriften einfügen
        if not worksheet.get_all_values():
            überschriften = ["Datum"] + list(daten_dict.keys())
            worksheet.append_row(überschriften)
            
        jetzt = datetime.now().strftime("%d.%m.%Y")
        eintrag = [jetzt] + list(daten_dict.values())
        
        # Zeile in Google Sheets anhängen
        worksheet.append_row(eintrag)
        st.success(f"Erfolgreich im Tabellenblatt '{blatt_name}' gespeichert! 🐝")
    except Exception as e:
        if "200" in str(e):
            st.success(f"Erfolgreich im Tabellenblatt '{blatt_name}' gespeichert! 🐝")
        else:
            st.error(f"Fehler beim Speichern: {e}")

# --- APP DESIGN ---
st.set_page_config(page_title="Imker App", page_icon="🐝")
st.title("🐝 Bastians Imker-Zentrale")

kategorie = st.sidebar.radio("MENÜ", ["Dashboard", "🔍 Durchschau", "📋 Bestandsbuch", "🍯 Honigernte"])

if kategorie == "Dashboard":
    st.subheader("Übersicht")
    col1, col2, col3 = st.columns(3)
    col1.metric("Stände", "Stand 1")
    col2.metric("Todos", "Offen")
    col3.metric("Termine", "Keine")

elif kategorie == "🔍 Durchschau":
    st.header("Völkerdurchsicht")
    
    # Eingabefelder der App
    stand = st.text_input("Stand", value="Stand 1")
    v_nr = st.number_input("Volk Nr.", min_value=1, step=1)
    koenigin = st.text_input("Königin Jahr/Farbe", value="Ja")
    zustand = st.selectbox("Zustand / Brut", ["Stifte vorhanden", "Keine Stifte", "Weiselunruhig"])
    notiz = st.text_area("ToDos / Bemerkung")
    
    if st.button("Durchschau speichern"):
        daten = {
            "Stand": stand,
            "Volk Nr.": v_nr,
            "Königin Jahr/Farbe": koenigin,
            "Zustand / Brut": zustand,
            "ToDos / Bemerkung": notiz
        }
        # Hier wird jetzt exakt das Blatt "Durchschau" angesteuert
        speichere_in_google("Durchschau", daten)

elif kategorie == "📋 Bestandsbuch":
    st.header("Amtlicher Arzneimittel-Nachweis")
    st.info("Hier machen wir das Gleiche, sobald die Durchschau perfekt läuft!")

elif kategorie == "🍯 Honigernte":
    st.header("Ernte erfassen")
    st.info("Hier machen wir das Gleiche, sobald die Durchschau perfekt läuft!")
