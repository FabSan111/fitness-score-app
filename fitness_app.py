import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

EXCEL_FILE = "fitnessdaten.xlsx"

# 📂 Datei laden oder erstellen
try:
    df = pd.read_excel(EXCEL_FILE)
    df["Datum"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce")
except FileNotFoundError:
    df = pd.DataFrame(columns=["Datum", "Kategorie", "Wert", "Score", "Kommentar"])
    df.to_excel(EXCEL_FILE, index=False)

# 🧭 App Layout
st.set_page_config(page_title="🏋️ Fitness Score Tracker", page_icon="💪")
st.title("🏃‍♂️ Fitness Score Tracker")

# 📅 Eingabebereich
datum = st.date_input("Datum", datetime.today())
kategorie = st.selectbox("Kategorie", ["Ausdauer", "Kraft", "Beweglichkeit"])

if kategorie == "Ausdauer":
    wert = st.number_input("Intensitätswert", min_value=0, step=1)
else:
    wert = st.number_input("Dauer der Einheit in Minuten", min_value=0, step=1)

kommentar = st.text_input("Kommentar (optional)")

# 📝 Einheit speichern
if st.button("Einheit speichern"):
    if kategorie == "Ausdauer":
        score = wert
    else:
        score = wert * 5

    new_row = {
        "Datum": pd.to_datetime(datum),
        "Kategorie": kategorie,
        "Wert": wert,
        "Score": score,
        "Kommentar": kommentar
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    st.success(f"✅ Einheit gespeichert! Score: {score}")

# 📊 Score-Auswertung – Summe / 28
st.subheader("📈 Fitness Score der letzten 28 Tage")

if not df.empty:
    cutoff = datetime.today() - timedelta(days=28)
    df_28 = df[df["Datum"] >= cutoff]

    # Summen pro Kategorie
    ausdauer_sum = df_28[df_28["Kategorie"] == "Ausdauer"]["Score"].sum()
    kraft_sum = df_28[df_28["Kategorie"] == "Kraft"]["Score"].sum()
    beweglichkeit_sum = df_28[df_28["Kategorie"] == "Beweglichkeit"]["Score"].sum()

    # Berechnung Score
    ausdauer_score = ausdauer_sum / 28
    kraft_score = kraft_sum / 28
    beweglichkeit_score = beweglichkeit_sum / 28
    gesamt_score = (ausdauer_sum + kraft_sum + beweglichkeit_sum) / (28 * 3)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ausdauer", f"{ausdauer_score:.1f}")
    col2.metric("Kraft", f"{kraft_score:.1f}")
    col3.metric("Beweglichkeit", f"{beweglichkeit_score:.1f}")
    col4.metric("Gesamt", f"{gesamt_score:.1f}")

    # 🧾 Historie
    st.subheader("📝 Trainingshistorie")
    st.dataframe(df.sort_values(by="Datum", ascending=False))

else:
    st.info("Noch keine Einträge vorhanden. Lege gleich los!")

# ℹ️ Hinweis
st.caption("💡 Tipp: Wenn du auf Streamlit Cloud hostest, kannst du diese Seite als App auf deinem Smartphone speichern.")
