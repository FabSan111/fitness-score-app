import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ===============================
# 🔐 Google Sheets Setup
# ===============================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)

# 👉 Deine eigene SHEET_ID hier eintragen
SHEET_ID = "19xHRPMONVLlevF6uMhc5r3SCc8-ba_6bV0Y3L9Fpv3w"
sheet = client.open_by_key(SHEET_ID).sheet1

# ===============================
# 📥 Daten laden
# ===============================
df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
if df.empty:
    df = pd.DataFrame(columns=["Datum", "Kategorie", "Wert", "Score", "Kommentar"])
else:
    # Datum bereinigen und auf Tagesebene bringen
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce").dt.normalize()
    df["Kategorie"] = df["Kategorie"].astype(str).str.strip().str.capitalize()

# ===============================
# 🖥️ Streamlit Setup
# ===============================
st.set_page_config(page_title="🏋️ Fitness Score Tracker", page_icon="💪")
st.title("🏃‍♂️ Fitness Score Tracker")

# ===============================
# 📝 Eingabeformular
# ===============================
datum = st.date_input("Datum", datetime.today())
kategorie = st.selectbox("Kategorie", ["Ausdauer", "Kraft", "Beweglichkeit"])
if kategorie == "Ausdauer":
    wert = st.number_input("Intensitätswert", min_value=0, step=1)
else:
    wert = st.number_input("Dauer der Einheit in Minuten", min_value=0, step=1)
kommentar = st.text_input("Kommentar (optional)")

if st.button("Einheit speichern", key="save_unit"):
    score = wert if kategorie == "Ausdauer" else wert * 10
    new_row = pd.DataFrame([{
        "Datum": pd.to_datetime(datum).normalize(),
        "Kategorie": kategorie,
        "Wert": wert,
        "Score": score,
        "Kommentar": kommentar
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    set_with_dataframe(sheet, df)
    st.success(f"✅ Einheit gespeichert! Score: {score}")

# ===============================
# 📊 Score-Berechnung
# ===============================
st.subheader("📈 Fitness Score der letzten 28 Tage")
if not df.empty:
    cutoff = pd.to_datetime(datetime.today()).normalize() - timedelta(days=28)
    df_28 = df[df["Datum"] >= cutoff]

    ausdauer_sum = df_28[df_28["Kategorie"] == "Ausdauer"]["Score"].sum()
    kraft_sum = df_28[df_28["Kategorie"] == "Kraft"]["Score"].sum()
    beweglichkeit_sum = df_28[df_28["Kategorie"] == "Beweglichkeit"]["Score"].sum()

    ausdauer_score = ausdauer_sum / 28
    kraft_score = kraft_sum / 28
    beweglichkeit_score = beweglichkeit_sum / 28
    gesamt_score = (ausdauer_sum + kraft_sum + beweglichkeit_sum) / (28 * 3)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ausdauer", f"{ausdauer_score:.1f}")
    col2.metric("Kraft", f"{kraft_score:.1f}")
    col3.metric("Beweglichkeit", f"{beweglichkeit_score:.1f}")
    col4.metric("Gesamt", f"{gesamt_score:.1f}")

    # ===============================
    # 📉 Liniendiagramm
    # ===============================
    daily_scores = (
        df_28.groupby(["Datum", "Kategorie"])["Score"]
        .sum()
        .unstack(fill_value=0)
    )

    # Fehlende Kategorien auffüllen (damit Linien nicht unterbrochen werden)
    for cat in ["Ausdauer", "Kraft", "Beweglichkeit"]:
        if cat not in daily_scores.columns:
            daily_scores[cat] = 0

    daily_scores["Gesamt"] = daily_scores[["Ausdauer", "Kraft", "Beweglichkeit"]].sum(axis=1) / 3

    # Sicherstellen, dass jeder Tag der letzten 28 Tage vertreten ist
    all_days = pd.date_range(cutoff, pd.to_datetime(datetime.today()).normalize())
    daily_scores = daily_scores.reindex(all_days, fill_value=0)
    daily_scores.index.name = "Datum"

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily_scores.index, daily_scores["Ausdauer"], label="Ausdauer", color="blue")
    ax.plot(daily_scores.index, daily_scores["Kraft"], label="Kraft", color="red")
    ax.plot(daily_scores.index, daily_scores["Beweglichkeit"], label="Beweglichkeit", color="green")
    ax.plot(daily_scores.index, daily_scores["Gesamt"], label="Gesamt", color="black", linewidth=2)

    ax.set_title("📊 Scoreentwicklung der letzten 28 Tage")
    ax.set_xlabel("Datum")
    ax.set_ylabel("Score")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    st.pyplot(fig)

    # ===============================
    # 📜 Historie
    # ===============================
    st.subheader("📝 Trainingshistorie")
    st.dataframe(df.sort_values(by="Datum", ascending=False))

else:
    st.info("Noch keine Einträge vorhanden.")
