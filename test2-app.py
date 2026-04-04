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
        # 編集用のデータフレーム作成
        staff_df = pd.DataFrame(list(st.session_state.staff_data.items()), columns=["名前", "基本時給"])
        
        # st.data_editor を使って、その場で時給を編集できるようにする
        edited_staff_df = st.data_editor(
            staff_df,
            use_container_width=True,
            column_config={
                "名前": st.column_config.TextColumn("名前", disabled=True), # 名前は変更不可（削除→再登録を推奨）
                "基本時給": st.column_config.NumberColumn("基本時給 (円)", min_value=0, step=100, format="%d")
            },
            key="staff_editor",
            num_rows="fixed"
        )
        
        col_save, col_del_btn = st.columns([1, 1])
        
        # 時給更新ボタン
        if col_save.button("💾 時給の変更を保存する", use_container_width=True):
            # 編集後のデータをセッションに反映
            st.session_state.staff_data = dict(zip(edited_staff_df["名前"], edited_staff_df["基本時給"]))
            st.success("時給設定を更新しました！")
            st.rerun()
            
        # 削除セクション
        with col_del_btn:
            del_target = st.selectbox("削除するスタッフを選択", ["---"] + list(st.session_state.staff_data.keys()), key="del_select")
            if st.button("🗑️ 選択したスタッフを削除", use_container_width=True):
                if del_target != "---":
                    del st.session_state.staff_data[del_target]
                    st.rerun()
    else:
        st.info("登録されているスタッフはいません。")

# --- タブ2: 給与入力 ---
with tab_input:
    st.subheader("📝 本日の勤務データ入力")
    if not st.session_state.staff_data:
        st.warning("先にスタッフ管理タブからスタッフを登録してください。")
    else:
        selected_staff = st.selectbox("スタッフを選択", list(st.session_state.staff_data.keys()))
        work_date = st.date_input("勤務日", datetime.now())
        
        c_t1, c_t2 = st.columns(2)
        with c_t1: start_time = st.time_input("出勤", datetime.strptime("20:00", "%H:%M").time())
        with c_t2: end_time = st.time_input("退勤", datetime.strptime("01:00", "%H:%M").time())

        # 登録されている最新の時給が自動で初期値として入る
        current_wage = st.number_input("今回の適用時給", value=st.session_state.staff_data[selected_staff])
        
        douhan = st.number_input("同伴回数 (3,000円/回)", min_value=0)
        shimei = st.number_input("指名回数", min_value=0)
        shimei_p = st.number_input("指名手当単価", value=1000)
        etc_deduction = st.number_input("その他控除(送迎等)", min_value=0)

        if st.button("💾 このデータを保存する"):
            s_dt = datetime.combine(work_date, start_time)
            e_dt = datetime.combine(work_date, end_time)
            if e_dt <= s_dt: e_dt += timedelta(days=1)
            h = (e_dt - s_dt).total_seconds() / 3600
            gross = (current_wage * h) + (douhan * 3000) + (shimei * shimei_p)
            tax = calculate_deduction(gross)
            net = gross - tax - etc_deduction
            
            new_entry = pd.DataFrame([[
                work_date, selected_staff, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
                round(h, 2), current_wage, int(gross), int(tax + etc_deduction), int(net)
            ]], columns=st.session_state.data_log.columns)
            st.session_state.data_log = pd.concat([st.session_state.data_log, new_entry], ignore_index=True)
            st.success("保存完了！")

# --- タブ1: カレンダー (以前の修正を維持) ---
with tab_cal:
    calendar_events = []
    if not st.session_state.data_log.empty:
        for _, row in st.session_state.data_log.iterrows():
            res_dict = row.to_dict()
            res_dict["日付"] = str(res_dict["日付"])
            calendar_events.append({
                "title": f"{row['スタッフ名']} ({int(row['手取り']):,}円)",
                "start": str(row["日付"]),
                "end": str(row["日付"]),
                "resource": res_dict
            })
    cal = calendar(events=calendar_events, options={"initialView": "dayGridMonth"}, key="calendar_view")
    if cal.get("eventClick"):
        st.info("👇 詳細")
        ed = cal["eventClick"]["event"]["extendedProps"]["resource"]
        st.write(f"**{ed['スタッフ名']}** | {ed['日付']} | {ed['出勤']}～{ed['退勤']} ({ed['勤務時間']}h)")
        st.write(f"手取り: {int(ed['手取り']):,}円 (支給:{int(ed['支給額']):,} / 控除:{int(ed['控除額']):,})")

# --- タブ4: 月間集計 ---
with tab_log:
    if not st.session_state.data_log.empty:
        df = st.session_state.data_log.copy()
        df['日付'] = pd.to_datetime(df['日付'])
        df['年月'] = df['日付'].dt.strftime('%Y-%m')
        target_month = st.selectbox("集計月を選択", sorted(df['年月'].unique(), reverse=True))
        month_df = df[df['年月'] == target_month]
        st.dataframe(month_df.groupby("スタッフ名")[["支給額", "控除額", "手取り"]].sum(), use_container_width=True)
    else:
        st.write("データがありません。")
