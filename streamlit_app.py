import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

st.set_page_config(page_title="ラウンジ給与管理（月別集計付）", layout="wide")

# --- 1. データの保持設定 ---
if "staff_data" not in st.session_state:
    st.session_state.staff_data = {"テスト嬢": 3000}

if "data_log" not in st.session_state:
    st.session_state.data_log = pd.DataFrame(columns=[
        "日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"
    ])

# --- 控除計算関数 ---
def calculate_deduction(amount):
    if amount < 5000: return 0
    elif amount <= 5900: return 100
    elif amount <= 6900: return 200
    elif amount <= 7900: return 300
    elif amount <= 8900: return 400
    elif amount <= 9900: return 500
    elif amount <= 10800: return 600
    elif amount <= 11800: return 700
    elif amount <= 12800: return 800
    elif amount <= 13800: return 900
    elif amount <= 14800: return 1000
    elif amount <= 15700: return 1100
    elif amount <= 16700: return 1200
    elif amount <= 17700: return 1300
    elif amount <= 18700: return 1400
    elif amount <= 19700: return 1500
    elif amount <= 20600: return 1600
    elif amount <= 21600: return 1700
    elif amount <= 22600: return 1800
    elif amount <= 23600: return 1900
    elif amount <= 24600: return 2000
    elif amount <= 25500: return 2100
    elif amount <= 26500: return 2200
    elif amount <= 27500: return 2300
    elif amount <= 28500: return 2400
    elif amount <= 29400: return 2500
    elif amount <= 30400: return 2600
    else: return math.ceil((amount - 5000) * 0.1021)

# --- サイドバー：新規入力 ---
with st.sidebar:
    st.header("📝 新規入力")
    selected_staff = st.selectbox("スタッフを選択", list(st.session_state.staff_data.keys()))
    work_date = st.date_input("勤務日", datetime.now())
    
    c_t1, c_t2 = st.columns(2)
    with c_t1: start_time = st.time_input("出勤", datetime.strptime("20:00", "%H:%M").time())
    with c_t2: end_time = st.time_input("退勤", datetime.strptime("01:00", "%H:%M").time())

    current_wage = st.number_input("適用時給", value=st.session_state.staff_data[selected_staff])
    douhan = st.number_input("同伴回数", min_value=0)
    shimei = st.number_input("指名回数", min_value=0)
    shimei_p = st.number_input("指名単価", value=1000)
    etc_deduct = st.number_input("その他控除(送迎等)", min_value=0)

    if st.button("✅ データを保存"):
        s_dt = datetime.combine(work_date, start_time)
        e_dt = datetime.combine(work_date, end_time)
        if e_dt <= s_dt: e_dt += timedelta(days=1)
        h = (e_dt - s_dt).total_seconds() / 3600
        gross = (current_wage * h) + (dou
