import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 📁 Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)

# 👉 Deine eigene SHEET_ID
SHEET_ID = "19xHRPMONVLlevF6uMhc5r3SCc8-ba_6bV0Y3L9Fpv3w"
sheet = client.open_by_key(SHEET_ID).sheet1

# 📥 Daten laden
df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
if df.empty:
    df = pd.DataFrame(columns=["Datum", "Kategorie", "Wert", "Score", "Kommentar"])
else:
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")

# 🧭 Streamlit Grundkonfiguration
st.set_page_config(page_title="🏋️ Fitness Score Tracker", page_icon="💪")
st.title("🏃‍♂️ Fitness Score Tracker")

# 📅 Eingabemaske
datum = st.date_input("Datum", datetime.today())
kategorie = st.selectbox("Kategorie", ["Ausdauer", "Kraft", "Beweglichkeit"])

if kategorie == "Ausdauer":
    wert = st.number_input("Intensitätswert", min_value=0, step=1)
else:
    wert = st.number_input("Dauer der Einheit in Minuten", min_value=0, step=1)

kommentar = st.text_input("Kommentar (optional)")

# 📝 Speichern
if st.button("Einheit speichern", key="save_unit"):
    score = wert if kategorie == "Ausdauer" else wert * 10  # 🔸 Faktor 10 für Kraft & Beweglichkeit
    new_row = pd.DataFrame([{
        "Datum": datum,
        "Kategorie": kategorie,
        "Wert": wert,
        "Score": score,
        "Kommentar": kommentar
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    set_with_dataframe(sheet, df)
    st.success(f"✅ Einheit gespeichert! Score: {score}")

# 📊 Score-Berechnung
st.subheader("📈 Fitness Score der letzten 28 Tage")
if not df.empty:
    # 🧹 Daten bereinigen
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0)
    df["Kategorie"] = df["Kategorie"].astype(str).str.strip().str.capitalize()

    # 📆 Filter auf letzte 28 Tage
    cutoff = datetime.today() - timedelta(days=28)
    df_28 = df[df["Datum"] >= cutoff]

    # Summen
    ausdauer_sum = df_28[df_28["Kategorie"] == "Ausdauer"]["Score"].sum()
    kraft_sum = df_28[df_28["Kategorie"] == "Kraft"]["Score"].sum()
    beweglichkeit_sum = df_28[df_28["Kategorie"] == "Beweglichkeit"]["Score"].sum()

    # Scores
    ausdauer_score = ausdauer_sum / 28
    kraft_score = kraft_sum / 28
    beweglichkeit_score = beweglichkeit_sum / 28
    gesamt_score = (ausdauer_sum + kraft_sum + beweglichkeit_sum) / (28 * 3)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ausdauer", f"{ausdauer_score:.1f}")
    col2.metric("Kraft", f"{kraft_score:.1f}")
    col3.metric("Beweglichkeit", f"{beweglichkeit_score:.1f}")
    col4.metric("Gesamt", f"{gesamt_score:.1f}")

    # 📊 Scoreentwicklung (Diagramm)
    st.subheader("📉 Scoreentwicklung (letzte 28 Tage)")

    # Gruppierung nach Tag und Kategorie
    daily_scores = (
        df_28.groupby(["Datum", "Kategorie"])["Score"]
        .sum()
        .unstack(fill_value=0)
    )

    # Fehlende Kategorien ergänzen
    for cat in ["Ausdauer", "Kraft", "Beweglichkeit"]:
        if cat not in daily_scores.columns:
            daily_scores[cat] = 0

    # Gesamtscore berechnen
    daily_scores["Gesamt"] = (
        daily_scores["Ausdauer"] + daily_scores["Kraft"] + daily_scores["Beweglichkeit"]
    ) / 3

    # Fehlende Tage auffüllen
    all_days = pd.date_range(cutoff, datetime.today())
    daily_scores = daily_scores.reindex(all_days, fill_value=0)

    # 📈 Diagramm zeichnen
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily_scores.index, daily_scores["Gesamt"], color="black", label="Gesamt")
    ax.plot(daily_scores.index, daily_scores["Ausdauer"], color="blue", label="Ausdauer")
    ax.plot(daily_scores.index, daily_scores["Kraft"], color="red", label="Kraft")
    ax.plot(daily_scores.index, daily_scores["Beweglichkeit"], color="green", label="Beweglichkeit")

    ax.set_title("Scoreentwicklung (letzte 28 Tage)")
    ax.set_xlabel("Datum")
    ax.set_ylabel("Score")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()

    st.pyplot(fig)

    # 📜 Historie
    st.subheader("📝 Trainingshistorie")
    st.dataframe(df.sort_values(by="Datum", ascending=False))

else:
    st.info("Noch keine Einträge vorhanden.")
