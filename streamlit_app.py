import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

st.set_page_config(page_title="【支店長用】給与管理システム", layout="wide")
st.title("📊 支店長用 給与管理ダッシュボード")

# --- 1. スタッフ管理機能（セッションで保持） ---
if "staff_list" not in st.session_state:
    st.session_state.staff_list = ["スタッフA", "スタッフB"]

if "data_log" not in st.session_state:
    st.session_state.data_log = pd.DataFrame(columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "支給額", "控除額", "手取り"])

# --- サイドバー：設定エリア ---
with st.sidebar:
    st.header("⚙️ 設定・管理")
    
    # スタッフの追加・削除
    new_staff_name = st.text_input("新規スタッフ名を入力")
    if st.button("スタッフを追加"):
        if new_staff_name and new_staff_name not in st.session_state.staff_list:
            st.session_state.staff_list.append(new_staff_name)
            st.success(f"{new_staff_name}を追加しました")
    
    delete_staff_name = st.selectbox("削除するスタッフを選択", ["選択してください"] + st.session_state.staff_list)
    if st.button("選択したスタッフを削除"):
        if delete_staff_name != "選択してください":
            st.session_state.staff_list.remove(delete_staff_name)
            st.rerun()

    st.markdown("---")
    
    # --- 2. データ入力セクション ---
    st.header("📝 給与データ入力")
    target_staff = st.selectbox("給与計算するスタッフを選択", st.session_state.staff_list)
    work_date = st.date_input("勤務日", datetime.now())
    
    # 出退勤時刻の入力
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_time = st.time_input("出勤時刻", datetime.strptime("20:00", "%H:%M").time())
    with col_t2:
        end_time = st.time_input("退勤時刻", datetime.strptime("01:00", "%H:%M").time())

    # 勤務時間の計算ロジック（日またぎ対応）
    start_dt = datetime.combine(work_date, start_time)
    end_dt = datetime.combine(work_date, end_time)
    
    if end_dt <= start_dt:
        # 退勤が出勤より早い（または同じ）場合は翌日とみなす
        end_dt += timedelta(days=1)
    
    diff_hours = (end_dt - start_dt).total_seconds() / 3600
    st.info(f"計算された勤務時間: {diff_hours:.2f} 時間")

    base_hourly_wage = st.number_input("時給 (円)", min_value=0, value=3000, step=100)
    
    st.subheader("手当（バック）")
    douhan_count = st.number_input("同伴回数 (3,000円/回)", min_value=0, value=0)
    shimei_count = st.number_input("指名回数", min_value=0, value=0)
    shimei_unit_price = st.number_input("指名手当単価 (円)", min_value=0, value=1000)
    
    etc_deduction = st.number_input("その他控除（送迎等）", min_value=0, value=0)
    
    submit_button = st.button("このデータを記録する")

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
basic_pay = base_hourly_wage * diff_hours
total_back = (douhan_count * 3000) + (shimei_count * shimei_unit_price)
total_supply = basic_pay + total_back
deduction = calculate_deduction(total_supply)
final_pay = total_supply - deduction - etc_deduction

# データ保存
if submit_button:
    new_data = pd.DataFrame([[
        work_date, 
        target_staff, 
        start_time.strftime("%H:%M"), 
        end_time.strftime("%H:%M"), 
        f"{diff_hours:.2f}",
        total_supply, 
        deduction + etc_deduction, 
        final_pay
    ]], columns=["日付", "スタッフ名", "出勤", "退勤", "勤務時間", "支給額", "控除額", "手取り"])
    st.session_state.data_log = pd.concat([st.session_state.data_log, new_data], ignore_index=True)
    st.success(f"{target_staff} のデータを保存しました")

# --- メイン画面：表示エリア ---
tab1, tab2 = st.tabs(["全体サマリー", "履歴データ"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("総支払額", f"{int(st.session_state.data_log['支給額'].sum()):,} 円")
    col2.metric("総控除額", f"{int(st.session_state.data_log['控除額'].sum()):,} 円")
    col3.metric("登録スタッフ数", len(st.session_state.staff_list))

    if not st.session_state.data_log.empty:
        st.subheader("スタッフ別 支給ランキング")
        staff_summary = st.session_state.data_log.groupby("スタッフ名")["手取り"].sum()
        st.bar_chart(staff_summary)

with tab2:
    st.
