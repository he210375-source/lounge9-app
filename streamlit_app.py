import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="ラウンジ給与管理（修正版）", layout="wide")

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
    elif amount <= 30400:
        steps = [
            (5900, 100), (6900, 200), (7900, 300), (8900, 400), (9900, 500),
            (10800, 600), (11800, 700), (12800, 800), (13800, 900), (14800, 1000),
            (15700, 1100), (16700, 1200), (17700, 1300), (18700, 1400), (19700, 1500),
            (20600, 1600), (21700, 1700), (22600, 1800), (23600, 1900), (24600, 2000),
            (25500, 2100), (26500, 2200), (27500, 2300), (28500, 2400), (29400, 2500), (30400, 2600)
        ]
        for limit, val in steps:
            if amount <= limit: return val
        return 2600
    else:
        return math.ceil((amount - 5000) * 0.1021)

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
    etc_deduction = st.number_input("その他控除(送迎等)", min_value=0)

    if st.button("✅ データを保存"):
        s_dt = datetime.combine(work_date, start_time)
        e_dt = datetime.combine(work_date, end_time)
        if e_dt <= s_dt: e_dt += timedelta(days=1)
        h = (e_dt - s_dt).total_seconds() / 3600
        gross = (current_wage * h) + (douhan * 3000) + (shimei * shimei_p)
        tax = calculate_deduction(gross)
        net = gross - tax - etc_deduction
        
        # 保存時は「日付」をdatetime型のままにする（集計で使うため）
        new_entry = pd.DataFrame([[
            work_date, selected_staff, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
            round(h, 2), current_wage, int(gross), int(tax + etc_deduction), int(net)
        ]], columns=st.session_state.data_log.columns)
        st.session_state.data_log = pd.concat([st.session_state.data_log, new_entry], ignore_index=True)
        st.rerun()

# --- メイン画面 ---
st.title("📅 勤務カレンダー管理")

# カレンダー用イベントデータの作成
calendar_events = []
if not st.session_state.data_log.empty:
    for _, row in st.session_state.data_log.iterrows():
        # 【重要】カレンダーに渡す辞書データ内の「日付」を文字列に変換する
        res_dict = row.to_dict()
        res_dict["日付"] = str(res_dict["日付"]) # datetimeを文字列に変換
        
        calendar_events.append({
            "title": f"{row['スタッフ名']} ({int(row['手取り']):,}円)",
            "start": str(row["日付"]),
            "end": str(row["日付"]),
            "resource": res_dict
        })

calendar_options = {
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,dayGridWeek"
    },
    "initialView": "dayGridMonth",
    "selectable": True,
}

# カレンダーの表示
cal = calendar(events=calendar_events, options=calendar_options, key="calendar")

# カレンダーのイベントをクリックした時の処理
if cal.get("eventClick"):
    st.markdown("---")
    st.subheader("📌 クリックした日の詳細データ")
    # 安全にデータを取得
    event_data = cal["eventClick"]["event"]["extendedProps"]["resource"]
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("スタッフ名", event_data["スタッフ名"])
    col_b.metric("勤務時間", f"{event_data['勤務時間']}h")
    col_c.metric("手取り額", f"{int(event_data['手取り']):,}円")
    
    with st.expander("詳細内訳を見る"):
        st.write(f"・勤務日: {event_data['日付']}")
        st.write(f"・出退勤: {event_data['出勤']} ～ {event_data['退勤']}")
        st.write(f"・支給総額: {int(event_data['支給額']):,}円")
        st.write(f"・控除合計: {int(event_data['控除額']):,}円")

st.markdown("---")
tab1, tab2 = st.tabs(["📊 月間集計", "⚙️ 設定"])

with tab1:
    if not st.session_state.data_log.empty:
        df = st.session_state.data_log.copy()
        df['日付'] = pd.to_datetime(df['日付'])
        df['年月'] = df['日付'].dt.strftime('%Y-%m')
        months = sorted(df['年月'].unique(), reverse=True)
        target_month = st.selectbox("集計月を選択", months)
        month_df = df[df['年月'] == target_month]
        
        summary = month_df.groupby("スタッフ名")[["支給額", "控除額", "手取り"]].sum().reset_index()
        st.dataframe(summary.style.format({
            "支給額": "{:,}円", "控除額": "{:,}円", "手取り": "{:,}円"
        }), use_container_width=True)
