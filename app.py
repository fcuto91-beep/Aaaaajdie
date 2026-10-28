import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection System", layout="centered")
st.title("🛡️ 공정 검사 및 이력 관리")

DATA_FILE = "inspection_history.csv"
IMAGE_DIR = "inspection_images"

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

KST = timezone(timedelta(hours=9))
current_time_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

st.info(f"⏰ 현재 검사 시각 (한국 시간): **{current_time_str}**")

material_lot = st.text_input("자재 / LOT명 입력")

st.markdown("---")
st.subheader("📝 시험 항목별 결과 판정")

nail_peel_result = st.selectbox("1️⃣ 손톱박리 검사 결과", ["적합", "부적합"])
tape_peel_result = st.selectbox("2️⃣ 테이프 박리 검사 결과", ["적합", "부적합"])

st.markdown("---")
uploaded_file = st.file_uploader("현장 사진 첨부", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="사진 미리보기", width=250)

remarks = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

submitted = st.button("💾 검사 이력 저장하기", type="primary")

if submitted:
    if not material_lot:
        st.warning("Please enter LOT name.")
    else:
        inspection_date = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        
        image_
