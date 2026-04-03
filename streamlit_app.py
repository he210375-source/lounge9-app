import streamlit as st
import math

st.title("ラウンジ給与計算アプリ")

# --- 入力セクション ---
st.header("1. 勤務データの入力")
col1, col2 = st.columns(2)

with col1:
    base_hourly_wage = st.number_input("時給 (円)", min_value=0, value=3000, step=100)
    working_hours = st.number_input("勤務時間 (h)", min_value=0.0, value=4.0, step=0.5)

with col2:
    douhan_count = st.number_input("同伴回数", min_value=0, value=0, step=1)
    shimei_count = st.number_input("指名回数", min_value=0, value=0, step=1)
    shimei_unit_price = st.number_input("指名手当単価 (円)", min_value=0, value=1000, step=100)

# --- 計算ロジック ---
# 1. 基本給とバックの計算
basic_pay = base_hourly_wage * working_hours
douhan_pay = douhan_count * 3000
shimei_pay = shimei_count * shimei_unit_price
total_supply = basic_pay + douhan_pay + shimei_pay # 総支給額

# 2. 控除（税金・手数料）の計算
def calculate_deduction(amount):
    if amount < 5000:
        return 0
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
        # 30400円超の場合: (支給額 - 5000) * 10.21% の切り上げ
        return math.ceil((amount - 5000) * 0.1021)

deduction = calculate_deduction(total_supply)
take_home_pay = total_supply - deduction

# --- 結果表示セクション ---
st.header("2. 計算結果")
st.subheader(f"本日のお給料（手取り）: {int(take_home_pay):,} 円")

with st.expander("詳細内訳"):
    st.write(f"・基本給: {int(basic_pay):,} 円")
    st.write(f"・同伴手当: {int(douhan_pay):,} 円")
    st.write(f"・指名手当: {int(shimei_pay):,} 円")
    st.write(f"・総支給額: {int(total_supply):,} 円")
    st.write(f"・控除額（源泉等）: {int(deduction):,} 円")

# --- 追加オプション（必要に応じて） ---
# 送迎代などの固定引きがある場合
st.header("3. その他調整")
etc_deduction = st.number_input("その他引かれるもの (送迎・ヘアメなど)", min_value=0, value=0, step=500)
final_amount = take_home_pay - etc_deduction
if etc_deduction > 0:
    st.success(f"最終受け取り額: {int(final_amount):,} 円")
