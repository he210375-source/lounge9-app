import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

st.set_page_config(page_title="【支店長用】給与管理システム", layout="wide")
st.title("📊 支店長用 給与管理ダッシュボード")

# --- 1. スタッフ管理機能（名前と時給を辞書形式で保持） ---
if "staff_data" not in st.session_state:
    # 初期データ {名前: 時給}
    st.session_state.staff_data = {"スタッフA": 3000, "スタッフB": 4000}

if "data_log" not in st.session_state:
    st.session_state.data_log = pd.DataFrame(columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"])

# --- サイドバー：設定エリア ---
with st.sidebar:
    st.header("⚙️ スタッフ事前登録")
    
    # スタッフの追加（名前と時給）
    with st.expander("新規スタッフ登録"):
        new_name = st.text_input("名前")
        new_wage = st.number_input("設定時給", min_value=0, value=3000, step=100)
        if st.button("登録を実行"):
            if new_name and new_name not in st.session_state.staff_data:
                st.session_state.staff_data[new_name] = new_wage
                st.success(f"{new_name}（時給{new_wage}円）を登録しました")
                st.rerun()
    
    # スタッフの削除
    with st.expander("登録解除"):
        delete_name = st.selectbox("削除するスタッフ", ["選択してください"] + list(st.session_state.staff_data.keys()))
        if st.button("削除を実行"):
            if delete_name != "選択してください":
                del st.session_state.staff_data[delete_name]
                st.rerun()

    st.markdown("---")
    
    # --- 2. データ入力セクション ---
    st.header("📝 本日の出勤データ入力")
    
    # スタッフ選択
    selected_staff = st.selectbox("スタッフを選択", list(st.session_state.staff_data.keys()))
    
    # 選択されたスタッフの時給を自動取得
    default_wage = st.session_state.staff_data[selected_staff]
    
    work_date = st.date_input("勤務日", datetime.now())
    
    # 出退勤時刻の入力
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_time = st.time_input("出勤時刻", datetime.strptime("20:00", "%H:%M").time())
    with col_t2:
        end_time = st.time_input("退勤時刻", datetime.strptime("01:00", "%H:%M").time())

    # 時給の確認・調整（登録時給から変更がある場合のみ上書き可能）
    current_wage = st.number_input("適用時給（自動反映）", min_value=0, value=default_wage, step=100)

    # 勤務時間の計算ロジック
    start_dt = datetime.combine(work_date, start_time)
    end_dt = datetime.combine(work_date, end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    diff_hours = (end_dt - start_dt).total_seconds() / 3600
    st.info(f"勤務時間: {diff_hours:.2f} 時間")

    st.subheader("手当（バック）")
    douhan_count = st.number_input("同伴回数 (3,000円/回)", min_value=0, value=0)
    shimei_count = st.number_input("指名回数", min_value=0, value=0)
    shimei_unit_price = st.number_input("指名手当単価 (円)", min_value=0, value=1000)
    
    etc_deduction = st.number_input("その他控除（送迎等）", min_value=0, value=0)
    
    submit_button = st.button("この日のデータを保存")

# --- 計算ロジック（控除階段） ---
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
    else:
        return math.ceil((amount - 5000) * 0.1021)

# 計算実行
basic_pay = current_wage * diff_hours
total_back = (douhan_count * 3000) + (shimei_count * shimei_unit_price)
total_supply = basic_pay + total_back
deduction = calculate_deduction(total_supply)
final_pay = total_supply - deduction - etc_deduction

# データ保存
if submit_button:
    new_data = pd.DataFrame([[
        work_date, 
        selected_staff, 
        start_time.strftime("%H:%M"), 
        end_time.strftime("%H:%M"), 
        f"{diff_hours:.2f}",
        current_wage,
        total_supply, 
        deduction + etc_deduction, 
        final_pay
    ]], columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "時給", "支給額", "控除額", "手取り"])
    st.session_state.data_log = pd.concat([st.session_state.data_log, new_data], ignore_index=True)
    st.success(f"{selected_staff} のデータを記録しました")

# --- メイン画面：表示エリア ---
tab1, tab2, tab3 = st.tabs(["📊 全体サマリー", "📋 履歴データ", "👭 登録スタッフ一覧"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("総支払額", f"{int(st.session_state.data_log['支給額'].sum()):,} 円")
    col2.metric("総控除額", f"{int(st.session_state.data_log['控除額'].sum()):,} 円")
    col3.metric("登録スタッフ数", len(st.session_state.staff_data))

    if not st.session_state.data_log.empty:
        st.subheader("スタッフ別 累計手取り額")
        staff_summary = st.session_state.data_log.groupby("スタッフ名")["手取り"].sum()
        st.bar_chart(staff_summary)

with tab2:
    st.subheader("給料計算履歴")
    st.dataframe(st.session_state.data_log, use_container_width=True)
    csv = st.session_state.data_log.to_csv(index=False).encode('utf_8_sig')
    st.download_button("CSVを書き出す", csv, f"salary_report.csv", "text/csv")

with tab3:
    st.subheader("登録済みスタッフ・時給一覧")
    staff_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
    st.table(staff_df)
