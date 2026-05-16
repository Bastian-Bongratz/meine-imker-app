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
        
        try:
            worksheet = tabelle.worksheet(blatt_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = tabelle.add_worksheet(title=blatt_name, rows="500", cols="20")
            
        alle_werte = worksheet.get_all_values()
        
        if not alle_werte or len(alle_werte) == 0:
            überschriften = ["Datum"] + list(daten_dict.keys())
            worksheet.append_row(überschriften)
            
        jetzt = datetime.now().strftime("%d.%m.%Y")
        eintrag = [jetzt] + list(daten_dict.values())
        
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
    notiz = st.text_area("Bemerkung / ToDos")
    
    if st.button("Durchschau speichern"):
        daten = {
            "Volk": v_nr, 
            "Königin": k_vorh, 
            "Stifte / Brut": stifte, 
            "Sanftmut": sanftmut, 
            "Schwarmstimmung": schwarm, 
            "Bemerkung": notiz
        }
        speichere_in_google("Durchschau", daten)

elif kategorie == "📋 Bestandsbuch":
    st.header("Amtlicher Arzneimittel-Nachweis")
    v_liste = st.text_input("Welche Völker? (z.B. 1, 2, 3)")
    mittel = st.text_input("Arzneimittel & Charge")
    menge = st.text_input("Dosierung")
    warzeit = st.number_input("Wartezeit (Tage)", min_value=0, step=1)
    
    if st.button("Bestandsbuch-Eintrag speichern"):
        daten = {
            "Völker": v_liste,
            "Arzneimittel & Charge": mittel,
            "Dosierung": menge,
            "Wartezeit (Tage)": warzeit
        }
        speichere_in_google("Bestandsbuch", daten)

elif kategorie == "🍯 Honigernte":
    st.header("Ernte erfassen")
    v_nr = st.number_input("Volk Nr.", min_value=1, step=1)
    sorte = st.selectbox("Sorte", ["Frühtracht", "Raps", "Wald", "Sommertracht"])
    kg = st.number_input("Menge in kg", min_value=0.0, step=0.5)
    
    if st.button("Ernte speichern"):
        daten = {
            "Volk Nr.": v_nr,
            "Sorte": sorte,
            "Menge in kg": kg
        }
        speichere_in_google("Honigernte", daten)

elif kategorie == "🥣 Fütterung":
    st.header("Fütterung eintragen")
    v_liste = st.text_input("Völker / Stand")
    futterart = st.selectbox("Futtertyp", ["Sirup (ApiInvert)", "Zuckerwasser 3:2", "Zuckerwasser 1:1", "Futterteig"])
    menge_l = st.number_input("Menge (Liter / kg)", min_value=0.0, step=0.5)
    
    if st.button("Fütterung speichern"):
        daten = {
            "Völker / Stand": v_liste,
            "Futtertyp": futterart,
            "Menge": menge_l
        }
        speichere_in_google("Fütterung", daten)

elif kategorie == "📦 Lager":
    st.header("Lagerbestand & Inventar")
    
    # Hier sind deine neuen Lager-Felder:
    artikel = st.selectbox("Artikel / Zubehör", ["Zargen (Dadant/Zander)", "Rähmchen (Leergut)", "Rähmchen (mit Mittelwänden)", "Honiggläser (500g)", "Honiggläser (250g)", "Futterzargen", "Sonstiges"])
    menge_lager = st.number_input("Anzahl / Menge", min_value=0, step=1)
    lager_notiz = st.text_input("Anmerkung (z.B. Zustand, Lagerort)")
    
    if st.button("Bestand aktualisieren"):
        daten = {
            "Artikel": artikel,
            "Menge": menge_lager,
            "Anmerkung": lager_notiz
        }
        speichere_in_google("Lager", daten)

elif kategorie == "✅ Todo/Termine":
    st.header("Anstehende Aufgaben")
    
    # Hier sind deine neuen ToDo-Felder:
    aufgabe = st.text_input("Was ist zu tun? (z.B. Varroa-Behandlung, Königinnen verschulen)")
    stand_todo = st.text_input("Welcher Bienenstand?", value="Stand 1")
    erledigen_bis = st.date_input("Erledigen bis wann?", datetime.now())
    prio = st.select_slider("Dringlichkeit", options=["Niedrig", "Normal", "Wichtig", "🚨 Eilt sehr!"], value="Normal")
    
    if st.button("Aufgabe eintragen"):
        daten = {
            "Aufgabe": aufgabe,
            "Stand": stand_todo,
            "Fällig am": erledigen_bis.strftime("%d.%m.%Y"),
            "Priorität": prio
        }
        speichere_in_google("Termine", daten)
