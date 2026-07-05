import os
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    user = os.getenv("DESTINATION__POSTGRES__CREDENTIALS__USERNAME")
    password = os.getenv("DESTINATION__POSTGRES__CREDENTIALS__PASSWORD")
    host = os.getenv("DESTINATION__POSTGRES__CREDENTIALS__HOST")
    port = os.getenv("DESTINATION__POSTGRES__CREDENTIALS__PORT")
    dbname = os.getenv("DESTINATION__POSTGRES__CREDENTIALS__DATABASE")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")

st.set_page_config(page_title="Crypto Market Dashboard", layout="wide")
st.title("Cryptocurrency Market Dashboard")

engine = get_engine()

df_coins = pd.read_sql("SELECT * FROM dbt_dev_sofia.stg_coins", engine)
df_summary = pd.read_sql(
    "SELECT * FROM dbt_dev_sofia.daily_market_summary ORDER BY date", engine
)

# ---------- Sidebar filters ----------
st.sidebar.header("Φίλτρα")
top_n = st.sidebar.slider("Top N νομίσματα", min_value=5, max_value=50, value=10, step=5)

min_date = df_summary["date"].min()
max_date = df_summary["date"].max()
date_range = st.sidebar.date_input(
    "Εύρος ημερομηνιών", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# ---------- KPI row ----------
total_market_cap = df_coins["market_cap"].sum()
total_volume = df_coins["total_volume"].sum()
num_coins = df_coins["id"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Συνολικό Market Cap", f"${total_market_cap:,.0f}")
col2.metric("Συνολικός 24h Volume", f"${total_volume:,.0f}")
col3.metric("Νομίσματα υπό παρακολούθηση", num_coins)

# ---------- Bar chart: top N by market cap ----------
st.header(f"Top {top_n} Νομίσματα κατά Market Cap")
df_top = df_coins.sort_values("market_cap", ascending=False).head(top_n)
fig_bar = px.bar(df_top, x="symbol", y="market_cap", hover_data=["name"])
st.plotly_chart(fig_bar)

# ---------- Line chart: total market cap over time (από το mart) ----------
st.header("Συνολικό Market Cap στον Χρόνο")
df_summary_filtered = df_summary[
    (df_summary["date"] >= start_date) & (df_summary["date"] <= end_date)
]
fig_summary = px.line(df_summary_filtered, x="date", y="total_market_cap")
st.plotly_chart(fig_summary)

# ---------- Line chart: price trend for a selected coin ----------
st.header("Τάση Τιμής ανά Νόμισμα")
coin_options = df_coins.sort_values("market_cap", ascending=False)["id"].tolist()
selected_coin = st.selectbox("Επίλεξε νόμισμα", coin_options)

df_history = pd.read_sql(
    """
    SELECT date, price
    FROM raw_crypto_sofia.coin_history
    WHERE coin_id = %(coin_id)s AND date BETWEEN %(start)s AND %(end)s
    ORDER BY date
    """,
    engine,
    params={"coin_id": selected_coin, "start": start_date, "end": end_date},
)
fig_line = px.line(df_history, x="date", y="price", title=f"Τιμή: {selected_coin}")
st.plotly_chart(fig_line)

# ---------- Gainers / Losers table ----------
st.header("Μεγαλύτεροι Gainers / Losers (24h)")
cols = ["symbol", "name", "current_price", "price_change_24h"]
df_gainers = df_coins.sort_values("price_change_24h", ascending=False).head(top_n)[cols]
df_losers = df_coins.sort_values("price_change_24h", ascending=True).head(top_n)[cols]

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Gainers")
    st.dataframe(df_gainers, width="stretch")
with col_b:
    st.subheader("Losers")
    st.dataframe(df_losers, width="stretch")