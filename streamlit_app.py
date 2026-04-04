import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="給与管理システム", layout="wide")

# --- 設定（URLをあなたのものに書き換えてください） ---
SPREADSHEET_URL = "あなたのスプレッドシートのURL"

# 接続初期化
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. データ読み込み関数（安定化のためキャッシュをオフにする） ---
def load_all_data():
    try:
        # スプレッドシートから最新を取得
        df_log = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="data_log", ttl=0)
        df_staff = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="staff_data", ttl=0)
        
        # 型変換の安定化
        df_log["日付"] = pd.to_datetime(df_log["日付"]).dt.date
        staff_dict = dict(zip(df_staff["名前"], df_staff["基本時給"]))
        return df_log, staff_dict
    except Exception:
        return pd.DataFrame(columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"]), {"テスト嬢": 3000}

# 起動時のデータ取得
if "data_log" not in st.session_state:
    log, staff = load_all_data()
    st.session_state.data_log = log
    st.session_state.staff_data = staff

# --- 2. 控除計算ロジック ---
def calculate_deduction(amount):
    if amount < 5000: return 0
    elif amount <= 30400:
        steps = [(5900, 100), (6900, 200), (7900, 300), (8900, 400), (9900, 500), (10800, 600), (11800, 700), (12800, 800), (13800, 900), (14800, 1000), (15700, 1100), (16700, 1200), (17700, 1300), (18700, 1400), (19700, 1500), (20600, 1600), (21700, 1700), (22600, 1800), (23600, 1900), (24600, 2000), (25500, 2100), (26500, 2200), (27500, 2300), (28500, 2400), (29400, 2500), (30400, 2600)]
        for limit, val in steps:
            if amount <= limit: return val
        return 2600
    else: return math.ceil((amount - 5000) * 0.1021)

# --- 3. メイン画面の構築 ---
st.title("👠 クラウド給与管理")

# 画面をリセットするためのフラグ
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# タブの作成
tab_cal, tab_input, tab_summary, tab_staff = st.tabs(["📅 カレンダー", "📝 給与入力", "📊 月間集計", "👭 スタッフ管理"])

# --- タブ1: カレンダー（エラー対策済み） ---
with tab_cal:
    # フォーム送信直後はカレンダーを描画しない（エラー回避）
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
        st.rerun()

    st.subheader("勤務状況一覧")
    events = []
    if not st.session_state.data_log.empty:
        for _, row in st.session_state.data_log.iterrows():
            events.append({
                "title": f"{row['スタッフ名']} {int(row['手取り']):,}円",
                "start": str(row["日付"]),
                "end": str(row["日付"]),
                "resource": {"name": row['スタッフ名'], "pay": int(row['手取り']), "time": f"{row['出勤']}~{row['退勤']}"}
            })
    
    # keyを固定してブラウザの混乱を防ぐ
    cal_output = calendar(events=events, options={"initialView": "dayGridMonth"}, key="stable_calendar")
    
    if cal_output.get("eventClick"):
        res = cal_output["eventClick"]["event"]["extendedProps"]["resource"]
        st.info(f"📌 {res['name']} さんの詳細: {res['time']} / 手取り {res['pay']:,}円")

# --- タブ2: 給与入力 ---
with tab_input:
    st.subheader("給与データ登録")
    if not st.session_state.staff_data:
        st.warning("スタッフを登録してください")
    else:
        with st.form("salary_form", clear_on_submit=True):
            target = st.selectbox("スタッフを選択", list(st.session_state.staff_data.keys()))
            d = st.date_input("勤務日", datetime.now())
            c1, c2 = st.columns(2)
            t_in = c1.time_input("出勤時刻", datetime.strptime("20:00", "%H:%M").time())
            t_out = c2.time_input("退勤時刻", datetime.strptime("01:00", "%H:%M").time())
            wage = st.number_input("適用時給", value=st.session_state.staff_data[target])
            back = st.number_input("手当（バック）合計", min_value=0)
            etc = st.number_input("送迎・その他控除", min_value=0)
            
            submitted = st.form_submit_button("保存してカレンダーに反映")
            
            if submitted:
                s_dt = datetime.combine(d, t_in)
                e_dt = datetime.combine(d, t_out)
                if e_dt <= s_dt: e_dt += timedelta(days=1)
                h = (e_dt - s_dt).total_seconds() / 3600
                gross = (wage * h) + back
                tax = calculate_deduction(gross)
                net = gross - tax - etc
                
                # 新しいデータ行を作成
                new_row = pd.DataFrame([[d, target, t_in.strftime("%H:%M"), t_out.strftime("%H:%M"), round(h, 2), wage, int(gross), int(tax + etc), int(net)]], columns=st.session_state.data_log.columns)
                
                # 更新とスプレッドシート反映
                updated_log = pd.concat([st.session_state.data_log, new_row], ignore_index=True)
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="data_log", data=updated_log)
                
                # セッションを更新して再起動フラグを立てる
                st.session_state.data_log = updated_log
                st.session_state.form_submitted = True
                st.success("スプレッドシートに保存しました！")
                st.rerun()

# --- タブ3: 月間集計 ---
with tab_summary:
    st.subheader("月間集計レポート")
    if not st.session_state.data_log.empty:
        df_sum = st.session_state.data_log.copy()
        df_sum["日付"] = pd.to_datetime(df_sum["日付"])
        df_sum["年月"] = df_sum["日付"].dt.strftime("%Y-%m")
        target_m = st.selectbox("表示月", sorted(df_sum["年月"].unique(), reverse=True), key="month_sel")
        
        month_data = df_sum[df_sum["年月"] == target_m]
        res_table = month_data.groupby("スタッフ名")[["支給額", "控除額", "手取り"]].sum()
        st.dataframe(res_table.style.format("{:,}円"), use_container_width=True)
    else:
        st.info("データがまだありません。")

# --- タブ4: スタッフ管理 ---
with tab_staff:
    st.subheader("スタッフ名簿・時給設定")
    s_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
    ed_s_df = st.data_editor(s_df, num_rows="dynamic", use_container_width=True, key="staff_editor_final")
    
    if st.button("スタッフ情報を更新（クラウド保存）"):
        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="staff_data", data=ed_s_df)
        st.session_state.staff_data = dict(zip(ed_s_df["名前"], ed_s_df["基本時給"]))
        st.success("クラウド上の情報を更新しました。")
        st.rerun()
