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
        
        image_filename = "none"
        if uploaded_file is not None:
            safe_lot = "".join(c for c in material_lot if c.isalnum() or c in ('_', '-'))
            t_str = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
            image_filename = f"{safe_lot}_{t_str}_{uploaded_file.name}"
            
            img_path = os.path.join(IMAGE_DIR, image_filename)
            with open(img_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        new_data = pd.DataFrame([{
            "검사일시": inspection_date,
            "자재/LOT명": material_lot,
            "손톱박리": nail_peel_result,
            "테이프박리": tape_peel_result,
            "사진파일명": image_filename,
            "특이사항": remarks,
        }])

        if os.path.exists(DATA_FILE):
            try:
                df_ex = pd.read_csv(DATA_FILE)
                df_combined = pd.concat([df_ex, new_data], ignore_index=True)
            except:
                df_combined = new_data
        else:
            df_combined = new_data

        df_combined.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        st.success("Saved successfully!")
        st.rerun()

st.markdown("---")
st.subheader("📋 전체 검사 내역 리스트")

if os.path.exists(DATA_FILE):
    df_load = pd.read_csv(DATA_FILE)
    
    search_query = st.text_input("🔍 이력 검색", placeholder="검색어 입력...")
    if search_query:
        df_filtered = df_load[
            df_load.astype(str).apply(
                lambda r: r.str.contains(search_query, case=False).any(),
                axis=1
            )
        ].reset_index(drop=True)
    else:
        df_filtered = df_load.reset_index
