import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection", layout="centered")
st.title("📦🧴 포장재 착인 검사 이력 관리")

F = "inspection_history.csv"
D = "inspection_images"

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))
st.info(f"⏰ 일자: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    mat_no = st.text_input("포장재 번호")
    pack_name = st.text_input("포장재 약호")
    nail = st.selectbox("손톱 박리 결과", ["적합", "부적합"])
    tape = st.selectbox("테이프 박리 결과", ["적합", "부적합"])
    up_file = st.file_uploader("검사 사진", type=["jpg", "jpeg", "png"])
    rem = st.text_area("특이사항")
    ok = st.form_submit_button("💾 Save", type="primary")

if ok:
    if not mat_no.strip():
        st.warning("⚠️ 포장재 번호를 입력해 주세요!")
    else:
        dt_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in mat_no if c.isalnum())
            t_str = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            file_path = os.path.join(D, fn)
            with open(file_path, "wb") as f:
                f.write(up_file.getbuffer())

        nd = pd.DataFrame([{
            "검사일시": dt_str,
            "포장재번호": mat_no,
            "포장재약호": pack_name if pack_name.strip() else "-",
            "손톱박리": nail,
            "테이프박리": tape,
            "사진파일명": fn,
            "특이사항": rem,
        }])

        df_c = nd
        if os.path.exists(F):
            try:
                df_ex = pd.read_csv(F)
                if "포장재명" in df_ex.columns and "포장재약호" not in df_ex.columns
