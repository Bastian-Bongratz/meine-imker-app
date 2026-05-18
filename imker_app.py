import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

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
        
        if not alle_werte or len(alle_werte) == 0 or alle_werte == [[]]:
            überschriften = ["Datum"] + list(daten_dict.keys())
            worksheet.append_row(überschriften)
            
        jetzt = datetime.now().strftime("%d.%m.%Y")
        eintrag = [jetzt] + list(daten_dict.values())
        
        worksheet.append_row(eintrag)
        st.success(f"Erfolgreich im Tabellenblatt '{blatt_name}' gespeichert! 🐝")
        st.cache_data.clear()
        
    except Exception as e:
        if "200" in str(e):
            st.success(f"Erfolgreich im Tabellenblatt '{blatt_name}' gespeichert! 🐝")
            st.cache_data.clear()
        else:
            st.error(f"Fehler beim Speichern: {e}")

# --- DATEN FÜR HISTORIE LADEN ---
@st.cache_data(ttl=10)
def lade_historie(blatt_name):
    try:
        tabelle = hole_google_tabelle()
        worksheet = tabelle.worksheet(blatt_name)
        alle_zeilen = worksheet.get_all_records()
        if alle_zeilen:
            return pd.DataFrame(alle_zeilen)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- APP DESIGN ---
st.set_page_config(page_title="Imker App", page_icon="🐝")
st.title("🐝 Bastians Imker-Zentrale")

# Menüpunkte inklusive Kassenbuch
kategorie = st.sidebar.radio("MENÜ", [
    "Dashboard", 
    "🔍 Durchschau", 
    "👑 Königinnen-Zucht", 
    "📋 Bestandsbuch", 
    "🍯 Honigernte", 
    "🥣 Fütterung", 
    "📦 Lager", 
    "💰 Kassenbuch",
    "✅ Todo/Termine"
])

def hole_farb_info(jahr):
    endziffer = str(jahr)[-1]
    if endziffer in ["1", "6"]: return "🤍 Weiß"
    elif endziffer in ["2", "7"]: return "💛 Gelb"
    elif endziffer in ["3", "8"]: return "❤️ Rot"
    elif endziffer in ["4", "9"]: return "💚 Grün"
    elif endziffer in ["5", "0"]: return "💙 Blau"
    return "Unbekannt"

if kategorie == "Dashboard":
    st.subheader("Übersicht")
    col1, col2, col3 = st.columns(3)
    col1.metric("Stände", "Stand 1")
    col2.metric("Todos", "Offen")
    col3.metric("Termine", "Keine")

elif kategorie == "🔍 Durchschau":
    st.header("Völkerdurchsicht")
    st.subheader("📝 Neue Durchschau eintragen")
    
    # 1. Volk-Nummer eingeben
    v_nr = st.number_input("Volk Nr.", min_value=1, step=1)
    
    # --- LOGIK FÜR ABLEGER-ERKENNUNG ---
    df_durchschau = lade_historie("Durchschau")
    ist_ableger = False
    
    if not df_durchschau.empty and "Volk" in df_durchschau.columns:
        # Filter nach dem aktuell ausgewählten Volk
        volk_historie = df_durchschau[df_durchschau["Volk"] == v_nr]
        
        if not volk_historie.empty:
            # Den letzten Eintrag dieses Volks holen
            letzter_eintrag = volk_historie.iloc[-1]
            # Prüfen, ob das Wort "ableger" in den Bemerkungen steht
            if "ableger" in str(letzter_eintrag.get("Bemerkung", "")).lower():
                ist_ableger = True

    # Visueller Hinweis und dynamische Vorauswahl, wenn es ein Ableger ist
    if ist_ableger:
        st.info("ℹ️ Dieses Volk ist aktuell als **Ableger** deklariert.")
        k_vorh_default = 2  # Index 2 entspricht "Unbekannt/Nachschaffung"
    else:
        k_vorh_default = 0  # Index 0 entspricht "Ja"

    # 2. Eingabefelder für das Formular
    k_vorh = st.radio("Königin vorhanden?", ["Ja", "Nein", "Unbekannt/Nachschaffung"], index=k_vorh_default)
    
    # DYNAMISCHE FELDER: Königinnen-Details nur zeigen, wenn auch eine Königin da ist
    if k_vorh == "Ja":
        k_jahr = st.selectbox("Geburtsjahr der Königin", [2026, 2025, 2024, 2023, 2022], index=0)
        k_farbe = hole_farb_info(k_jahr)
        st.info(f"Die offizielle Zeichnungsfarbe für {k_jahr} ist: **{k_farbe}**")
    else:
        # Standardwerte setzen, wenn keine Königin da ist
        k_jahr = "-"
        k_farbe = "-"
        if ist_ableger:
            st.warning("📅 *Hinweis: Lass dem Ableger genug Zeit für die Nachschaffung und den Hochzeitsflug (ca. 21-24 Tage).*")
    
    st.markdown("---")
    stifte = st.radio("Stifte / Brut vorhanden?", ["Ja", "Nein"], index=1 if ist_ableger else 0)
    sanftmut = st.select_slider("Sanftmut", options=["1", "2", "3", "4", "5"], value="5")
    schwarm = st.select_slider("Schwarmstimmung", options=["1", "2", "3", "4", "5"], value="1")
    notiz = st.text_area("Bemerkung / ToDos")
    
    if st.button("Durchschau Speichern"):
        daten = {
            "Volk": v_nr, 
            "Königin vorhanden": k_vorh, 
            "Königin Jahr": k_jahr,
            "Königin Farbe": k_farbe,
            "Stifte / Brut": stifte, 
            "Sanftmut": sanftmut, 
            "Schwarmstimmung": schwarm, 
            "Bemerkung": notiz
        }
        speichere_in_google("Durchschau", daten)

    st.markdown("---")
    st.subheader("🗂️ Kartenindex / Völker-Historie")
    if not df_durchschau.empty and "Volk" in df_durchschau.columns:
        alle_voelker = sorted(df_durchschau["Volk"].unique())
        # Setzt die Historie-Auswahl automatisch auf das oben eingetippte Volk, falls vorhanden
        index_default = alle_voelker.index(v_nr) if v_nr in alle_voelker else 0
        ausgewaehltes_volk = st.selectbox("Historie anzeigen für Volk:", alle_voelker, index=index_default)
        df_gefiltert = df_durchschau[df_durchschau["Volk"] == ausgewaehltes_volk]
        st.dataframe(df_gefiltert.iloc[::-1], use_container_width=True)
    else:
        st.info("Sobald du einen Eintrag mit Überschriften gespeichert hast, siehst du hier dein Völker-Archiv!")

elif kategorie == "👑 Königinnen-Zucht":
    st.header("👑 Königinnen-Zucht & Umlav-Planer")
    zucht_name = st.text_input("Zuchtserie Bezeichnung", value="Serie 1 - 2026")
    umlauftag = st.date_input("Umlavdatum / Start", datetime.now())
    anzahl_larven = st.number_input("Anzahl umgelavte Larven", min_value=1, value=10, step=1)
    
    deckelung = umlauftag + timedelta(days=5)
    verschulen = umlauftag + timedelta(days=11)
    schlupf = umlauftag + timedelta(days=12)
    
    st.subheader("📅 Wichtige Termine für diese Serie:")
    st.warning(f"🔒 **Caging / Verschulen (Tag 11):** {verschulen.strftime('%d.%m.%Y')}")
    st.success(f"🐣 **Erwarteter Schlupf (Tag 12):** {schlupf.strftime('%d.%m.%Y')}")
    st.info(f"🪹 Capped / Deckelung (Tag 5): {deckelung.strftime('%d.%m.%Y')}")
    
    zucht_notiz = st.text_input("Notizen zur Herkunft (Zuchtmutter)")
    
    if st.button("Zuchtserie in Google Sheets sichern"):
        daten = {
            "Zucht-Serie": zucht_name,
            "Umlavdatum": umlauftag.strftime("%d.%m.%Y"),
            "Larven Anzahl": anzahl_larven,
            "Verschul-Datum": verschulen.strftime("%d.%m.%Y"),
            "Schlupf-Datum": schlupf.strftime("%d.%m.%Y"),
            "Herkunft/Notiz": zucht_notiz
        }
        speichere_in_google("Zucht", daten)

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

elif kategorie == "💰 Kassenbuch":
    st.header("💰 Imker-Kassenbuch")
    
    art = st.radio("Buchungsart", ["🟢 Einnahme", "🔴 Ausgabe"], index=0)
    betrag = st.number_input("Betrag in €", min_value=0.0, step=0.50, format="%.2f")
    zweck = st.text_input("Verwendungszweck / Artikel (z.B. 10 Gläser Waldhonig, neue Stockmeißel)")
    kat = st.selectbox("Kategorie", ["Honigverkauf", "Völker-/Königinnenverkauf", "Imkereibedarf & Werkzeug", "Futter & Medikamente", "Beuten & Rähmchen", "Sonstiges"])
    
    if st.button("Buchung speichern"):
        daten = {
            "Typ": art,
            "Betrag": betrag,
            "Zweck": zweck,
            "Kategorie": kat
        }
        speichere_in_google("Kassenbuch", daten)

elif kategorie == "✅ Todo/Termine":
    st.header("Anstehende Aufgaben")
    aufgabe = st.text_input("Was ist zu tun? (z.B. Varroa-Behandlung)")
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
