import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from streamlit_gsheets import GSheetsConnection

# ページ設定
st.set_page_config(page_title="給与管理システム", layout="wide")

# --- スプレッドシート設定 ---
# ⚠️ ここをご自身のURLに書き換えてください
SPREADSHEET_URL = "あなたのスプレッドシートURL"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- データ読み込み（エラー回避のためキャッシュなし） ---
def load_all_data():
    try:
        df_log = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="data_log", ttl=0)
        df_staff = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="staff_data", ttl=0)
        df_log["日付"] = pd.to_datetime(df_log["日付"]).dt.date
        staff_dict = dict(zip(df_staff["名前"], df_staff["基本時給"]))
        return df_log, staff_dict
    except:
        return pd.DataFrame(columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"]), {"テスト嬢": 3000}

# データの取得
if "data_log" not in st.session_state:
    log, staff = load_all_data()
    st.session_state.data_log = log
    st.session_state.staff_data = staff

# --- 控除計算 ---
def calculate_deduction(amount):
    if amount < 5000: return 0
    elif amount <= 30400:
        steps = [(5900, 100), (6900, 200), (7900, 300), (8900, 400), (9900, 500), (10800, 600), (11800, 700), (12800, 800), (13800, 900), (14800, 1000), (15700, 1100), (16700, 1200), (17700, 1300), (18700, 1400), (19700, 1500), (20600, 1600), (21700, 1700), (22600, 1800), (23600, 1900), (24600, 2000), (25500, 2100), (26500, 2200), (27500, 2300), (28500, 2400), (29400, 2500), (30400, 2600)]
        for limit, val in steps:
            if amount <= limit: return val
        return 2600
    else: return math.ceil((amount - 5000) * 0.1021)

# --- 画面構成（サイドバーでメニュー切り替え） ---
# タブだとパーツが裏側に残ってエラーの原因になるため、サイドバーで「物理的に消す」方式にします
st.sidebar.title("メニュー")
menu = st.sidebar.radio("機能を選択", ["📅 カレンダー表示", "📝 給与データ入力", "📊 月間集計表", "👭 スタッフ名簿設定"])

# --- 1. カレンダー表示 ---
if menu == "📅 カレンダー表示":
    st.subheader("勤務状況カレンダー")
    events = []
    if not st.session_state.data_log.empty:
        for _, row in st.session_state.data_log.iterrows():
            events.append({
                "title": f"{row['スタッフ名']} {int(row['手取り']):,}円",
                "start": str(row["日付"]),
                "end": str(row["日付"]),
            })
    
    # カレンダーのみを表示（他のパーツと混ぜない）
    calendar(events=events, options={"initialView": "dayGridMonth"}, key="fixed_calendar")

# --- 2. 給与データ入力 ---
elif menu == "📝 給与データ入力":
    st.subheader("本日のデータ登録")
    with st.form("input_form"):
        target = st.selectbox("スタッフ", list(st.session_state.staff_data.keys()))
        d = st.date_input("勤務日", datetime.now())
        c1, c2 = st.columns(2)
        t_in = c1.time_input("出勤", datetime.strptime("20:00", "%H:%M").time())
        t_out = c2.time_input("退勤", datetime.strptime("01:00", "%H:%M").time())
        wage = st.number_input("時給", value=st.session_state.staff_data[target])
        back = st.number_input("手当(バック)合計", min_value=0)
        etc = st.number_input("控除額(送迎等)", min_value=0)
        
        if st.form_submit_button("スプレッドシートへ保存"):
            s_dt = datetime.combine(d, t_in)
            e_dt = datetime.combine(d, t_out)
            if e_dt <= s_dt: e_dt += timedelta(days=1)
            h = (e_dt - s_dt).total_seconds() / 3600
            gross = (wage * h) + back
            tax = calculate_deduction(gross)
            net = gross - tax - etc
            
            new_row = pd.DataFrame([[d, target, t_in.strftime("%H:%M"), t_out.strftime("%H:%M"), round(h, 2), wage, int(gross), int(tax + etc), int(net)]], columns=st.session_state.data_log.columns)
            updated_log = pd.concat([st.session_state.data_log, new_row], ignore_index=True)
            
            conn.update(spreadsheet=SPREADSHEET_URL, worksheet="data_log", data=updated_log)
            st.session_state.data_log = updated_log
            st.success("保存しました！メニューからカレンダーに戻ってください。")

# --- 3. 月間集計表 ---
elif menu == "📊 月間集計表":
    st.subheader("スタッフ別・月別集計")
    if not st.session_state.data_log.empty:
        df = st.session_state.data_log.copy()
        df["日付"] = pd.to_datetime(df["日付"])
        df["年月"] = df["日付"].dt.strftime("%Y-%m")
        m = st.selectbox("月を選択", sorted(df["年月"].unique(), reverse=True))
        st.dataframe(df[df["年月"] == m].groupby("スタッフ名")[["支給額", "控除額", "手取り"]].sum().style.format("{:,}円"), use_container_width=True)
    else:
        st.info("データがありません")

# --- 4. スタッフ名簿設定 ---
elif menu == "👭 スタッフ名簿設定":
    st.subheader("スタッフ情報の編集")
    s_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
    ed_s_df = st.data_editor(s_df, num_rows="dynamic", use_container_width=True, key="staff_editor")
    
    if st.button("クラウドの情報を更新する"):
        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="staff_data", data=ed_s_df)
        st.session_state.staff_data = dict(zip(ed_s_df["名前"], ed_s_df["基本時給"]))
        st.success("更新完了！")
