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
        gross = (current_wage * h) + (douhan * 3000) + (shimei * shimei_p)
        tax = calculate_deduction(gross)
        net = gross - tax - etc_deduct
        
        new_entry = pd.DataFrame([[
            work_date, selected_staff, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
            round(h, 2), current_wage, int(gross), int(tax + etc_deduction), int(net)
        ]], columns=st.session_state.data_log.columns)
        st.session_state.data_log = pd.concat([st.session_state.data_log, new_entry], ignore_index=True)
        st.rerun()

# --- メイン画面 ---
st.title("📊 月別・スタッフ別 給与集計")

if not st.session_state.data_log.empty:
    # データ型を確実に日付にする
    df = st.session_state.data_log.copy()
    df['日付'] = pd.to_datetime(df['日付'])
    df['年月'] = df['日付'].dt.strftime('%Y-%m')

    # --- 月選択フィルタ ---
    months = sorted(df['年月'].unique(), reverse=True)
    target_month = st.selectbox("表示する月を選択", months)
    
    # 選択した月のデータに絞り込み
    month_df = df[df['年月'] == target_month]

    # --- 月間サマリー表示 ---
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{target_month} 総支給額", f"{int(month_df['支給額'].sum()):,} 円")
    c2.metric(f"{target_month} 総控除額", f"{int(month_df['控除額'].sum()):,} 円")
    c3.metric(f"{target_month} 総手取り額", f"{int(month_df['手取り'].sum()):,} 円")

    st.markdown("---")

    # --- タブ表示 ---
    tab1, tab2, tab3 = st.tabs(["👥 スタッフ別集計", "📋 月間明細一覧", "⚙️ 設定"])

    with tab1:
        st.subheader(f"{target_month} のスタッフ別合計")
        # スタッフごとに集計
        summary = month_df.groupby("スタッフ名")[["支給額", "控除額", "手取り"]].sum().reset_index()
        st.dataframe(summary.style.format({
            "支給額": "{:,}円", "控除額": "{:,}円", "手取り": "{:,}円"
        }), use_container_width=True)
        
        # グラフ表示
        st.bar_chart(summary.set_index("スタッフ名")["支給額"])

    with tab2:
        st.subheader(f"{target_month} の全データ（編集可）")
        edited_month_df = st.data_editor(month_df.drop(columns=['年月']), use_container_width=True, num_rows="dynamic")
        if st.button("編集内容を反映して保存"):
            # 元のlogから、当該月以外のデータ + 今回編集した当該月のデータを合体させる
            other_month_df = df[df['年月'] != target_month].drop(columns=['年月'])
            st.session_state.data_log = pd.concat([other_month_df, edited_month_df], ignore_index=True)
            st.success("更新しました")
            st.rerun()

    with tab3:
        st.subheader("スタッフ基本情報")
        staff_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
        edited_staff = st.data_editor(staff_df, num_rows="dynamic", use_container_width=True)
        if st.button("スタッフ情報を更新"):
            st.session_state.staff_data = dict(zip(edited_staff["名前"], edited_staff["基本時給"]))
            st.rerun()
else:
    st.info("データがありません。サイドバーから入力を開始してください。")
