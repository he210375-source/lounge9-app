import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="ラウンジ給与管理（クラウド保存版）", layout="wide")

# --- Googleスプレッドシート接続設定 ---
# スプレッドシートのURLをここに貼り付けてください
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/12rrlajWISU1jjQS9iZRoZ8Spm8cyv4rrtLVS2k1JQRo/edit?gid=620061519#gid=620061519"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- データの読み込み関数 ---
def load_data():
    try:
        # 給与履歴の読み込み
        df_log = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="data_log")
        # スタッフ情報の読み込み
        df_staff = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="staff_data")
        staff_dict = dict(zip(df_staff["名前"], df_staff["基本時給"]))
        return df_log, staff_dict
    except:
        # 失敗した場合は空のデータを返す
        return pd.DataFrame(columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"]), {"テスト嬢": 3000}

# 初期読み込み
if "data_log" not in st.session_state or "staff_data" not in st.session_state:
    log, staff = load_data()
    st.session_state.data_log = log
    st.session_state.staff_data = staff

# --- 控除計算関数 ---
def calculate_deduction(amount):
    if amount < 5000: return 0
    elif amount <= 30400:
        steps = [(5900, 100), (6900, 200), (7900, 300), (8900, 400), (9900, 500), (10800, 600), (11800, 700), (12800, 800), (13800, 900), (14800, 1000), (15700, 1100), (16700, 1200), (17700, 1300), (18700, 1400), (19700, 1500), (20600, 1600), (21700, 1700), (22600, 1800), (23600, 1900), (24600, 2000), (25500, 2100), (26500, 2200), (27500, 2300), (28500, 2400), (29400, 2500), (30400, 2600)]
        for limit, val in steps:
            if amount <= limit: return val
        return 2600
    else: return math.ceil((amount - 5000) * 0.1021)

# --- メイン画面 ---
st.title("☁️ クラウド給与管理システム")

tab_cal, tab_input, tab_staff, tab_log = st.tabs(["📅 カレンダー", "📝 給与入力", "👭 スタッフ管理", "📊 月間集計"])

# --- タブ3: スタッフ管理 ---
with tab_staff:
    st.subheader("👭 スタッフ管理")
    staff_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
    edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True, key="staff_editor")
    
    if st.button("💾 スタッフ情報をスプレッドシートに保存"):
        # スプレッドシートへ書き込み
        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="staff_data", data=edited_staff)
        st.session_state.staff_data = dict(zip(edited_staff["名前"], edited_staff["基本時給"]))
        st.success("スプレッドシートを更新しました！")

# --- タブ2: 給与入力 ---
with tab_input:
    st.subheader("📝 給与入力")
    selected_staff = st.selectbox("スタッフを選択", list(st.session_state.staff_data.keys()))
    work_date = st.date_input("勤務日", datetime.now())
    c_t1, c_t2 = st.columns(2)
    with c_t1: start_time = st.time_input("出勤", datetime.strptime("20:00", "%H:%M").time())
    with c_t2: end_time = st.time_input("退勤", datetime.strptime("01:00", "%H:%M").time())
    current_wage = st.number_input("時給", value=st.session_state.staff_data[selected_staff])
    douhan = st.number_input("同伴", min_value=0)
    shimei = st.number_input("指名", min_value=0)
    etc_deduction = st.number_input("その他控除", min_value=0)

    if st.button("🚀 データをスプレッドシートに保存"):
        s_dt = datetime.combine(work_date, start_time)
        e_dt = datetime.combine(work_date, end_time)
        if e_dt <= s_dt: e_dt += timedelta(days=1)
        h = (e_dt - s_dt).total_seconds() / 3600
        gross = (current_wage * h) + (douhan * 3000) + (shimei * 1000)
        tax = calculate_deduction(gross)
        net = gross - tax - etc_deduction
        
        new_row = pd.DataFrame([[str(work_date), selected_staff, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), round(h, 2), current_wage, int(gross), int(tax + etc_deduction), int(net)]], columns=st.session_state.data_log.columns)
        
        # 既存データと結合してスプレッドシートを更新
        updated_log = pd.concat([st.session_state.data_log, new_row], ignore_index=True)
        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="data_log", data=updated_log)
        st.session_state.data_log = updated_log
        st.success("スプレッドシートに保存しました！")

# --- カレンダーと集計はこれまでのロジックを維持（省略） ---
# (ここから下のコードは以前のものと同様です。カレンダーとタブ4をそのまま入れてください)
