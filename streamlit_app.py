import streamlit as st
import pandas as pd
import math
from datetime import datetime

st.set_page_config(page_title="【支店長用】給与管理システム", layout="wide")
st.title("📊 支店長用 給与管理ダッシュボード")

# --- 設定（スタッフリストなど） ---
staff_list = ["スタッフA", "スタッフB", "スタッフC", "共通/その他"]

# --- サイドバー：入力セクション ---
with st.sidebar:
    st.header("📝 データ入力")
    target_staff = st.selectbox("スタッフを選択", staff_list)
    work_date = st.date_input("勤務日", datetime.now())
    
    base_hourly_wage = st.number_input("時給 (円)", min_value=0, value=3000, step=100)
    working_hours = st.number_input("勤務時間 (h)", min_value=0.0, value=4.0, step=0.5)
    
    st.subheader("手当（バック）")
    douhan_count = st.number_input("同伴回数", min_value=0, value=0)
    shimei_count = st.number_input("指名回数", min_value=0, value=0)
    shimei_unit_price = st.number_input("指名手当単価 (円)", min_value=0, value=1000)
    
    etc_deduction = st.number_input("その他控除（送迎等）", min_value=0, value=0)
    
    submit_button = st.button("このデータを記録する")

# --- 計算ロジック（前回の条件を維持） ---
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

# 計算の実行
basic_pay = base_hourly_wage * working_hours
total_back = (douhan_count * 3000) + (shimei_count * shimei_unit_price)
total_supply = basic_pay + total_back
deduction = calculate_deduction(total_supply)
final_pay = total_supply - deduction - etc_deduction

# --- データ保存（簡易的にセッション状態に保存） ---
if "data_log" not in st.session_state:
    st.session_state.data_log = pd.DataFrame(columns=["日付", "スタッフ名", "支給額", "控除額", "手取り"])

if submit_button:
    new_data = pd.DataFrame([[work_date, target_staff, total_supply, deduction + etc_deduction, final_pay]], 
                            columns=["日付", "スタッフ名", "支給額", "控除額", "手取り"])
    st.session_state.data_log = pd.concat([st.session_state.data_log, new_data], ignore_index=True)
    st.success(f"{target_staff} のデータを保存しました")

# --- メイン画面：分析・一覧 ---
tab1, tab2 = st.tabs(["全体サマリー", "履歴データ"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("総支払額", f"{int(st.session_state.data_log['支給額'].sum()):,} 円")
    col2.metric("総控除額", f"{int(st.session_state.data_log['控除額'].sum()):,} 円")
    col3.metric("スタッフ数", len(st.session_state.data_log["スタッフ名"].unique()))

    if not st.session_state.data_log.empty:
        st.subheader("スタッフ別 支給ランキング")
        staff_summary = st.session_state.data_log.groupby("スタッフ名")["手取り"].sum()
        st.bar_chart(staff_summary)

with tab2:
    st.subheader("入出金履歴一覧")
    st.dataframe(st.session_state.data_log, use_container_width=True)
    
    # CSVダウンロード機能
    csv = st.session_state.data_log.to_csv(index=False).encode('utf_8_sig')
    st.download_button("CSVとしてダウンロード", csv, "salary_data.csv", "text/csv")
