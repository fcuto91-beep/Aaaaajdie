import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile
import requests
import json

st.set_page_config(page_title="Inspection", layout="centered")

D = "inspection_images"
LOGO_PATH = "logo.png"
ADMIN_PW = "1234"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxxZFR3sBQRIMZxBiZfamJiIvPwTI4UGrVaHkfQnMQJqFm8ZFnUJyScN-fShF2ZoyLHBw/exec"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))

def load_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                return df
    except Exception as e:
        print(f"Load error: {e}")
    
    return pd.DataFrame(columns=["검사일시", "포장재번호", "포장재약호", "손톱박리", "테이프박리", "사진파일명", "특이사항"])

def append_to_sheet(row_data):
    try:
        payload = {"action": "append", "row": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Append error: {e}")
        return False

def update_sheet(date_val, mat_val, row_data):
    try:
        payload = {"action": "update", "date": str(date_val), "mat_no": str(mat_val), "row": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Update error: {e}")
        return False

# UI 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_column_width=True)

st.markdown("")
st.markdown("<h1 style='text-align: center; font-size: 24px !important; font-weight: bold; margin-bottom: 10px; word-break: keep-all;'>📦🧴 포장재 착인 검사 이력 관리</h1>", unsafe_allow_html=True)

# 💡 텍스트 분리형으로 문법 오류 원천 차단
current_time_str = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
st.info(f"⏰ 일자: **{current_time_str}**")

@st.dialog("🎉 저장 완료")
def show_save_success_popup():
    st.success("검사 결과가 구글 시트에 실시간으로 안전하게 저장되었습니다!")
    if st.button("확인", type="primary", use_container_width=True):
        st.rerun()

@st.dialog("✏️ 수정 완료")
def show_edit_success_popup():
    st.success("검사 내역이 구글 시트에 성공적으로 수정 반영되었습니다!")
    if st.button("확인", type="primary", use_container_width=True):
        st.rerun()

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    mat_no = st.text_input("포장재 번호", placeholder="예: 5115558")
    pack_name = st.text_input("포장재 약호", placeholder="예: ANA-TBMBM(F)E 용기(공용)")
    
    nail = st.selectbox("손톱 박리 결과", ["선택해주세요", "🟢 적합 (PASS)", "🔴 부적합 (FAIL)"])
    tape = st.selectbox("테이프 박리 결과", ["선택해주세요", "🟢 적합 (PASS)", "🔴 부적합 (FAIL)"])
    
    up_file = st.file_uploader("검사 사진", type=["jpg", "jpeg", "png"])
    rem = st.text_area("특이사항")
    ok = st.form_submit_button("💾 Save", type="primary")

if ok:
    if not mat_no.strip():
        st.warning("⚠️ 포장재 번호를 입력해 주세요!")
    elif nail == "선택해주세요" or tape == "선택해주세요":
        st.warning("⚠️ 손톱 및 테이프 박리 결과를 선택해 주세요!")
    else:
        dt_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in mat_no if c.isalnum())
            t_str = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            file_path = os.path.join(D, fn
