import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- GOOGLE SHEETS VERBINDUNG ---
def hole_google_tabelle():
   # ERSETZE ES DURCH DIESEN BLOCK:
scope = ["https://www.googleapis.com/auth/spreadsheets"]
# Hier reparieren wir eventuelle Formatierungsfehler im Schlüssel automatisch:
info = dict(st.secrets["gcp_service_account"])
if "private_key" in info:
    info["private_key"] = info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(info, scopes=scope)
client = gspread.authorize(creds)
    
    # Öffnet deine Google-Tabelle (Name muss exakt stimmen!)
    return client.open("Imker_Daten")

def speichere_in_google(blatt_name, daten):
    try:
        tabelle = hole_google_tabelle()
        
        # Versucht das Tabellenblatt zu öffnen, falls nicht vorhanden, wird es erstellt
        try:
            worksheet = tabelle.worksheet(blatt_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = tabelle.add_worksheet(title=blatt_name, rows="100", cols="20")
            # Erste Zeile mit Überschriften füllen, falls das Blatt neu ist
            überschriften = ["Datum"] + list(daten.keys())
            worksheet.append_row(überschriften)
            
        jetzt = datetime.now().strftime("%d.%m.%Y")
        eintrag = [jetzt] + list(daten.values())
        
        # Zeile in Google Sheets anhängen
        worksheet.append_row(eintrag)
        st.success(f"Erfolgreich in Google Sheets ({blatt_name}) gespeichert! 🐝")
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")

# --- APP DESIGN ---
st.set_page_config(page_title="Imker App", page_icon="🐝")
st.title("🐝 Bastians Imker-Zentrale")

# Menü-Auswahl
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
        # Speichert alle Durchsichten zentral im Blatt "Durchschau"
        daten = {"Volk": v_nr, "Königin": k_vorh, "Stifte": stifte, "Sanftmut": sanftmut, "Schwarm": schwarm, "Notiz": notiz}
        speichere_in_google("Durchschau", daten)

elif kategorie == "📋 Bestandsbuch":
    st.header("Amtlicher Arzneimittel-Nachweis")
    v_liste = st.text_input("Welche Völker? (z.B. 1,2,3)")
    mittel = st.text_input("Arzneimittel & Charge")
    menge = st.text_input("Dosierung")
    wartezeit = st.number_input("Wartezeit (Tage)", 0)
    
    if st.button("Bestandsbuch-Eintrag"):
        daten = {"Völker": v_liste, "Mittel": mittel, "Menge": menge, "Wartezeit": wartezeit}
        speichere_in_google("Bestandsbuch", daten)

elif kategorie == "🍯 Honigernte":
    st.header("Ernte erfassen")
    v_nr = st.number_input("Volk Nr.", 1)
    sorte = st.selectbox("Sorte", ["Frühtracht", "Raps", "Wald", "Sommer"])
    kg = st.number_input("Menge in kg", 0.0)
    
    if st.button("Ernte speichern"):
        daten = {"Volk": v_nr, "Sorte": sorte, "Menge_kg": kg}
        speichere_in_google("Honigernte", daten)
