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

def speichere_in_volks_tabelle(volk_nr, aktions_typ, daten_dict):
    try:
        tabelle = hole_google_tabelle()
        blatt_name = f"Volk_{volk_nr}"
        
        # Alle denkbaren Spalten für das kombinierte Volksblatt definieren
        alle_spalten = [
            "Datum", "Typ", "Königin vorhanden", "Königin Jahr", "Königin Farbe", 
            "Stifte / Brut", "Sanftmut", "Schwarmstimmung", "Varroa-Mittel", 
            "Varroa-Menge", "Milben/Tag", "Futtertyp", "Futter-Menge", 
            "Honig-Sorte", "Honig-kg", "Bemerkung"
        ]
        
        try:
            worksheet = tabelle.worksheet(blatt_name)
        except gspread.exceptions.WorksheetNotFound:
            # Erstellt ein neues Blatt für das Volk, falls es noch nicht existiert
            worksheet = tabelle.add_worksheet(title=blatt_name, rows="1000", cols="20")
            worksheet.append_row(alle_spalten)
            
        # Standardzeile vorbereiten (voll mit leeren Werten)
        zeilen_daten = {spalte: "-" for spalte in alle_spalten}
        
        # Basis-Daten setzen
        zeilen_daten["Datum"] = datetime.now().strftime("%d.%m.%Y")
        zeilen_daten["Typ"] = aktions_typ
        
        # Spezifische Werte aus dem übergebenen Dictionary eintragen
        for key, value in daten_dict.items():
            if key in zeilen_daten:
                zeilen_daten[key] = value
                
        # Als Liste in der richtigen Reihenfolge sortieren und anhängen
        eintrag_liste = [zeilen_daten[spalte] for spalte in alle_spalten]
        worksheet.append_row(eintrag_liste)
        
        st.success(f"Erfolgreich im Tabellenblatt '{blatt_name}' gespeichert! 🐝")
        st.cache_data.clear()
        
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")

# --- ENTFÄLLT NICHT, WIRD FÜR DIE GEÄNDERTE HISTORIE GENUTZT ---
@st.cache_data(ttl=10)
def hole_alle_voelker_aus_sheets():
    try:
        tabelle = hole_google_tabelle()
        blätter = tabelle.worksheets()
        # Filtert alle Blätter heraus, die mit "Volk_" beginnen
        v_liste = [b.title.split("_")[1] for b in blätter if b.title.startswith("Volk_")]
        return sorted([int(x) for x in v_liste if x.isdigit()])
    except Exception:
        return []

@st.cache_data(ttl=10)
def lade_volk_historie(volk_nr):
    try:
        tabelle = hole_google_tabelle()
        worksheet = tabelle.worksheet(f"Volk_{volk_nr}")
        alle_zeilen = worksheet.get_all_records()
        if alle_zeilen:
            return pd.DataFrame(alle_zeilen)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- APP DESIGN ---
st.set_page_config(page_title="Imker App", page_icon="🐝")
st.title("🐝 Bastians Imker-Zentrale")

kategorie = st.sidebar.radio("MENÜ", [
    "Dashboard", 
    "📇 Digitale Stockkarte",
    "🔍 Durchschau", 
    "👑 Königinnen-Zucht", 
    "🦠 Varroa-Behandlung",
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

elif kategorie == "📇 Digitale Stockkarte":
    st.header("📇 Digitale Stockkarte")
    st.info("Wähle ein Volk aus, um die gesamte Lebenslaufakte zu sehen.")
    
    alle_voelker = hole_alle_voelker_aus_sheets()
    
    if alle_voelker:
        # --- LOGIK: AUFGELÖSTE VÖLKER FILTERN ---
        aktive_voelker = []
        for v in alle_voelker:
            df_v = lade_volk_historie(v)
            if not df_v.empty:
                letzter_eintrag = df_v.iloc[-1]
                bemerkung = str(letzter_eintrag.get("Bemerkung", "")).lower()
                if "aufgelöst" not in bemerkung:
                    aktive_voelker.append(v)
                    
        zeige_aufgelöste = st.checkbox("Auch aufgelöste Völker anzeigen", value=False)
        voelker_auswahl = alle_voelker if zeige_aufgelöste else aktive_voelker
        
        if not voelker_auswahl:
            st.warning("Aktuell keine aktiven Völker vorhanden.")
        else:
            v_wahl = st.selectbox("Stockkarte für Volk Nr.:", voelker_auswahl)
            df_volk = lade_volk_historie(v_wahl)
            
            if not df_volk.empty:
                # Filtert das kombinierte Blatt in die jeweiligen Tabs zur Übersicht auf der UI
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Durchschauen", "🦠 Varroa", "🥣 Fütterung", "🍯 Honig"])
                
                with tab1:
                    st.subheader(f"Durchsichten Volk {v_wahl}")
                    df_d = df_volk[df_volk["Typ"] == "Durchschau"]
                    st.dataframe(df_d.iloc[::-1], use_container_width=True)
                    
                with tab2:
                    st.subheader(f"Varroa-Status Volk {v_wahl}")
                    df_var = df_volk[df_volk["Typ"] == "Varroa"]
                    st.dataframe(df_var.iloc[::-1], use_container_width=True)

                with tab3:
                    st.subheader(f"Fütterungen Volk {v_wahl}")
                    df_f = df_volk[df_volk["Typ"] == "Fütterung"]
                    st.dataframe(df_f.iloc[::-1], use_container_width=True)
                    
                with tab4:
                    st.subheader(f"Honigertrag Volk {v_wahl}")
                    df_h = df_volk[df_volk["Typ"] == "Honigernte"]
                    st.dataframe(df_h.iloc[::-1], use_container_width=True)
            else:
                st.write("Keine Einträge für dieses Volk gefunden.")
    else:
        st.warning("Noch keine Völker-Tabellen in der Datenbank gefunden. Lege erst eine Durchschau an!")

elif kategorie == "🔍 Durchschau":
    st.header("Völkerdurchsicht")
    st.subheader("📝 Neue Durchschau eintragen")
    
    v_nr = st.number_input("Volk Nr.", min_value=1, step=1)
    
    df_volk = lade_volk_historie(v_nr)
    ist_ableger = False
    
    if not df_volk.empty:
        df_durchschau = df_volk[df_volk["Typ"] == "Durchschau"]
        if not df_durchschau.empty:
            hat_ableger_eintrag = df_durchschau["Bemerkung"].astype(str).str.lower().str.contains("ableger").any()
            letzter_eintrag = df_durchschau.iloc[-1]
            koenigin_schon_da = str(letzter_eintrag.get("Königin vorhanden", "")) == "Ja"
            wieder_wirtschaftsvolk = "wirtschaftsvolk" in str(letzter_eintrag.get("Bemerkung", "")).lower()
            
            if hat_ableger_eintrag and not koenigin_schon_da and not wieder_wirtschaftsvolk:
                ist_ableger = True

    k_vorh_default = 2 if ist_ableger else 0
    k_vorh = st.radio("Königin vorhanden?", ["Ja", "Nein", "Unbekannt/Nachschaffung"], index=k_vorh_default)
    
    if k_vorh == "Ja":
        k_jahr = st.selectbox("Geburtsjahr der Königin", [2026, 2025, 2024, 2023, 2022], index=0)
        k_farbe = hole_farb_info(k_jahr)
        st.info(f"Die offizielle Zeichnungsfarbe für {k_jahr} is: **{k_farbe}**")
    else:
        k_jahr, k_farbe = "-", "-"
        if ist_ableger:
            st.warning("📅 *Hinweis: Lass dem Ableger genug Zeit für die Nachschaffung und den Hochzeitsflug (ca. 21-24 Tage).*")
    
    st.markdown("---")
    stifte = st.radio("Stifte / Brut vorhanden?", ["Ja", "Nein"], index=1 if ist_ableger else 0)
    sanftmut = st.select_slider("Sanftmut", options=["1", "2", "3", "4", "5"], value="5")
    schwarm = st.select_slider("Schwarmstimmung", options=["1", "2", "3", "4", "5"], value="1")
    notiz = st.text_area("Bemerkung / ToDos")
    
    if st.button("Durchschau Speichern"):
        daten = {
            "Königin vorhanden": k_vorh, 
            "Königin Jahr": k_jahr,
            "Königin Farbe": k_farbe,
            "Stifte / Brut": stifte, 
            "Sanftmut": sanftmut, 
            "Schwarmstimmung": schwarm, 
            "Bemerkung": notiz
        }
        speichere_in_volks_tabelle(v_nr, "Durchschau", daten)

elif kategorie == "👑 Königinnen-Zucht":
    st.header("👑 Königinnen-Zucht & Umlarv-Planer")
    # Zucht ist standübergreifend, daher nutzen wir hier die alte Haupt-Logik weiter
    zucht_name = st.text_input("Zuchtserie Bezeichnung", value="Serie 1 - 2026")
    umlarvtag = st.date_input("Umlarvdatum / Start", datetime.now())
    anzahl_larven = st.number_input("Anzahl umgelarvte Larven", min_value=1, value=10, step=1)
    
    deckelung = umlarvtag + timedelta(days=5)
    verschulen = umlarvtag + timedelta(days=11)
    schlupf = umlarvtag + timedelta(days=12)
    
    st.subheader("📅 Wichtige Termine für diese Serie:")
    st.warning(f"🔒 **Caging / Verschulen (Tag 11):** {verschulen.strftime('%d.%m.%Y')}")
    st.success(f"🐣 **Erwarteter Schlupf (Tag 12):** {schlupf.strftime('%d.%m.%Y')}")
    st.info(f"🪹 Capped / Deckelung (Tag 5): {deckelung.strftime('%d.%m.%Y')}")
    
    zucht_notiz = st.text_input("Notizen zur Herkunft (Zuchtmutter)")
    
    if st.button("Zuchtserie in Google Sheets sichern"):
        try:
            tabelle = hole_google_tabelle()
            try: worksheet = tabelle.worksheet("Zucht")
            except gspread.exceptions.WorksheetNotFound: worksheet = tabelle.add_worksheet(title="Zucht", rows="500", cols="10")
            worksheet.append_row([datetime.now().strftime("%d.%m.%Y"), zucht_name, umlarvtag.strftime("%d.%m.%Y"), anzahl_larven, verschulen.strftime("%d.%m.%Y"), schlupf.strftime("%d.%m.%Y"), zucht_notiz])
            st.success("Erfolgreich in Zucht-Tabelle gesichert!")
        except Exception as e: st.error(f"Fehler: {e}")

elif kategorie == "🦠 Varroa-Behandlung":
    st.header("🦠 Varroa-Kontrolle & Behandlung")
    v_nr_varroa = st.number_input("Für welches Volk Nr.?", min_value=1, step=1)
    typ_varroa = st.selectbox("Aktionstyp", ["Diagnose (Milbenfall)", "Behandlung (Ameisensäure)", "Behandlung (Oxalsäure)", "Behandlung (Milchsäure)", "Biotechnisch (Drohnenbrut)", "Sonstiges"])
    
    milben_pro_tag = 0.0
    behandlung_mittel, menge_varroa = "-", "-"
    
    if typ_varroa == "Diagnose (Milbenfall)":
        col_tage, col_milben = st.columns(2)
        tage_windel = col_tage.number_input("Tage, die die Windel lag", min_value=1, value=3, step=1)
        milben_gesamt = col_milben.number_input("Milben insgesamt gezählt", min_value=0, value=0, step=1)
        if tage_windel > 0: milben_pro_tag = round(milben_gesamt / tage_windel, 2)
        st.metric(label="Berechneter Milbenfall pro Tag", value=f"{milben_pro_tag} Milben/Tag")
    else:
        behandlung_mittel = st.text_input("Eingesetztes Mittel / Verfahren")
        menge_varroa = st.text_input("Dosierung / Menge")
        
    varroa_notiz = st.text_area("Bemerkungen / Wetter")
    
    if st.button("Varroa-Daten speichern"):
        daten = {
            "Varroa-Mittel": behandlung_mittel,
            "Varroa-Menge": menge_varroa,
            "Milben/Tag": milben_pro_tag,
            "Bemerkung": f"{typ_varroa} - {varroa_notiz}"
        }
        speichere_in_volks_tabelle(v_nr_varroa, "Varroa", daten)

elif kategorie == "📋 Bestandsbuch":
    st.header("Amtlicher Arzneimittel-Nachweis")
    # Amtliches Bestandsbuch bleibt als Gesamtliste bestehen
    v_liste = st.text_input("Welche Völker? (z.B. 1)")
    mittel = st.text_input("Arzneimittel & Charge")
    menge = st.text_input("Dosierung")
    warzeit = st.number_input("Wartezeit (Tage)", min_value=0, step=1)
    
    if st.button("Bestandsbuch-Eintrag speichern"):
        try:
            tabelle = hole_google_tabelle()
            try: worksheet = tabelle.worksheet("Bestandsbuch")
            except gspread.exceptions.WorksheetNotFound: worksheet = tabelle.add_worksheet(title="Bestandsbuch", rows="500", cols="10")
            worksheet.append_row([datetime.now().strftime("%d.%m.%Y"), v_liste, mittel, menge, warzeit])
            st.success("Im amtlichen Bestandsbuch gesichert!")
        except Exception as e: st.error(f"Fehler: {e}")

elif kategorie == "🍯 Honigernte":
    st.header("Ernte erfassen")
    v_nr = st.number_input("Volk Nr.", min_value=1, step=1)
    sorte = st.selectbox("Sorte", ["Frühtracht", "Raps", "Wald", "Sommertracht"])
    kg = st.number_input("Menge in kg", min_value=0.0, step=0.5)
    
    if st.button("Ernte speichern"):
        daten = {
            "Honig-Sorte": sorte,
            "Honig-kg": kg
        }
        speichere_in_volks_tabelle(v_nr, "Honigernte", daten)

elif kategorie == "🥣 Fütterung":
    st.header("🥣 Fütterung & Futterrechner")
    st.subheader("🧮 Futtermenge-Rechner")
    zuckermenge_input = st.number_input("Zuckermenge (kg)", min_value=0.0, value=1.0, step=1.0)
    
    if zuckermenge_input > 0:
        wasser_3_2 = round(zuckermenge_input / 1.5, 1)
        gesamt_3_2 = round((zuckermenge_input * 0.6) + wasser_3_2, 1)
        st.markdown(f"**Bienenfutter 3:2:** {wasser_3_2}L Wasser | {gesamt_3_2}L Gesamtmenge")
        
    st.markdown("---")
    st.subheader("📝 Fütterung eintragen")
    v_nr_futter = st.number_input("Für Volk Nr.", min_value=1, step=1)
    futterart = st.selectbox("Futtertyp", ["Sirup (ApiInvert)", "Zuckerwasser 3:2", "Zuckerwasser 1:1", "Futterteig"])
    menge_l = st.number_input("Menge (Liter / kg)", min_value=0.0, step=0.5)
    
    if st.button("Fütterung speichern"):
        daten = {
            "Futtertyp": futterart,
            "Futter-Menge": menge_l
        }
        speichere_in_volks_tabelle(v_nr_futter, "Fütterung", daten)

elif kategorie == "📦 Lager":
    st.header("Lagerbestand & Inventar")
    # Lager/Kassenbuch/Todos sind unabh. von einzelnen Völkern und bleiben global
    artikel = st.selectbox("Artikel", ["Zargen", "Rähmchen", "Honiggläser", "Sonstiges"])
    menge_lager = st.number_input("Anzahl", min_value=0, step=1)
    if st.button("Bestand aktualisieren"):
        st.success("Lager aktualisiert (Globales Feature)")

elif kategorie == "💰 Kassenbuch":
    st.header("💰 Imker-Kassenbuch")
    betrag = st.number_input("Betrag in €", min_value=0.0, format="%.2f")
    if st.button("Buchung speichern"):
        st.success("Kassenbuch aktualisiert")

elif kategorie == "✅ Todo/Termine":
    st.header("Anstehende Aufgaben")
    aufgabe = st.text_input("Was ist zu tun?")
    if st.button("Aufgabe eintragen"):
        st.success("Todo hinzugefügt")
