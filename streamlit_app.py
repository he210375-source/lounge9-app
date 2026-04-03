import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="ラウンジ給与管理（時給変更機能付）", layout="wide")

# --- 1. データの保持設定（セッション） ---
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

# --- メイン画面 ---
st.title("📅 勤務・給与管理システム")

tab_cal, tab_input, tab_staff, tab_log = st.tabs(["📅 カレンダー", "📝 給与入力", "👭 スタッフ管理", "📊 月間集計"])

# --- タブ3: スタッフ管理（時給変更機能を追加） ---
with tab_staff:
    st.subheader("👭 スタッフの登録・時給変更")
    
    # 新規登録セクション
    with st.expander("✨ 新しくスタッフを登録する", expanded=False):
        c1, c2, c3 = st.columns([2, 2, 1])
        new_name = c1.text_input("名前", key="add_name")
        new_wage = c2.number_input("基本時給", min_value=0, value=3000, step=100, key="add_wage")
        if c3.button("登録", use_container_width=True):
            if new_name and new_name not in st.session_state.staff_data:
                st.session_state.staff_data[new_name] = new_wage
                st.rerun()
            else:
                st.error("名前が空か、既に登録されています")

    st.markdown("---")
    
    # 既存スタッフの編集・削除セクション
    st.write("### 📋 登録スタッフ一覧・設定変更")
    if st.session_state.staff_data:
        #
