import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="ラウンジ給与管理", layout="wide")

# --- スプレッドシート設定（あなたのURLに書き換えてください） ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/12rrlajWISU1jjQS9iZRoZ8Spm8cyv4rrtLVS2k1JQRo/edit?gid=0#gid=0"

# 接続の初期化
conn = st.connection("gsheets", type=GSheetsConnection)

# --- データの読み込み（キャッシュを利用して安定化） ---
def load_all_data():
    try:
        df_log = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="data_log")
        df_staff = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="staff_data")
        # 日付列を確実に文字列→datetimeに変換
        df_log["日付"] = pd.to_datetime(df_log["日付"]).dt.date
        staff_dict = dict(zip(df_staff["名前"], df_staff["基本時給"]))
        return df_log, staff_dict
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame(columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"]), {"テスト嬢": 3000}

# セッション状態の初期化
if "data_log" not in st.session_state:
    log, staff = load_all_data()
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

# エラー回避のため、カレンダーと入力を物理的に離すか、
# 描画の優先順位を整理するためにタブを定義
tab_cal, tab_input, tab_summary, tab_staff = st.tabs(["📅 カレンダー", "📝 給与入力", "📊 月間集計", "👭 スタッフ管理"])

with tab_cal:
    st.subheader("勤務状況")
    events = []
    # データのコピーをとって加工
    display_df = st.session_state.data_log.copy()
    if not display_df.empty:
        for _, row in display_df.iterrows():
            events.append({
                "title": f"{row['スタッフ名']} {int(row['手取り']):,}円",
                "start": str(row["日付"]),
                "end": str(row["日付"]),
                "resource": {"name": row['スタッフ名'], "pay": int(row['手取り']), "time": f"{row['出勤']}~{row['退勤']}"}
            })
    
    # 画面リセット時のエラーを防ぐために一意のKeyを振る
    cal_data = calendar(events=events, options={"initialView": "dayGridMonth"}, key="main_calendar_widget")
    
    if cal_data.get("eventClick"):
        res = cal_data["eventClick"]["event"]["extendedProps"]["resource"]
        st.info(f"📌 {res['name']} さんの詳細: {res['time']} / 手取り {res['pay']:,}円")

with tab_input:
    st.subheader("給与データ登録")
    if not st.session_state.staff_data:
        st.warning("スタッフを登録してください")
    else:
        with st.form("input_form"): # Formを使うことでボタン押下まで再描画を抑える
            target = st.selectbox("スタッフ", list(st.session_state.staff_data.keys()))
            d = st.date_input("勤務日", datetime.now())
            c1, c2 = st.columns(2)
            t_in = c1.time_input("出勤", datetime.strptime("20:00", "%H:%M").time())
            t_out = c2.time_input("退勤", datetime.strptime("01:00", "%H:%M").time())
            wage = st.number_input("時給", value=st.session_state.staff_data[target])
            back = st.number_input("バック合計", min_value=0)
            etc = st.number_input("その他控除", min_value=0)
            
            submitted = st.form_submit_button("スプレッドシートに保存")
            
            if submitted:
                s_dt = datetime.combine(d, t_in)
                e_dt = datetime.combine(d, t_out)
                if e_dt <= s_dt: e_dt += timedelta(days=1)
                h = (e_dt - s_dt).total_seconds() / 3600
                gross = (wage * h) + back
                tax = calculate_deduction(gross)
                net = gross - tax - etc
                
                new_row = pd.DataFrame([[d, target, t_in.strftime("%H:%M"), t_out.strftime("%H:%M"), round(h, 2), wage, int(gross), int(tax + etc), int(net)]], columns=st.session_state.data_log.columns)
                updated_log = pd.concat([st.session_state.data_log, new_row], ignore_index=True)
                
                # スプレッドシート更新
                conn.update(spreadsheet=SPREADSHEET_URL, worksheet="data_log", data=updated_log)
                st.session_state.data_log = updated_log
                st.success("保存しました！カレンダーを確認してください。")
                st.rerun()

with tab_summary:
    st.subheader("月間集計")
    if not st.session_state.data_log.empty:
        df_sum = st.session_state.data_log.copy()
        df_sum["日付"] = pd.to_datetime(df_sum["日付"])
        df_sum["年月"] = df_sum["日付"].dt.strftime("%Y-%m")
        m = st.selectbox("月を選択", sorted(df_sum["年月"].unique(), reverse=True))
        st.dataframe(df_sum[df_sum["年月"] == m].groupby("スタッフ名")[["支給額", "控除額", "手取り"]].sum(), use_container_width=True)

with tab_staff:
    st.subheader("スタッフ設定")
    s_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
    ed_s_df = st.data_editor(s_df, num_rows="dynamic", use_container_width=True, key="staff_editor_sheet")
    
    if st.button("スタッフ情報をクラウドに反映"):
        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="staff_data", data=ed_s_df)
        st.session_state.staff_data = dict(zip(ed_s_df["名前"], ed_s_df["基本時給"]))
        st.success("更新しました")
        st.rerun()
