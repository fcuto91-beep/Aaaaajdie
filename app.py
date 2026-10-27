from datetime import datetime
import io
import os
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="현장 검사 시스템", layout="centered")
st.title("🛡️ 공정 검사 및 이력 관리")

DATA_FILE = "inspection_history.csv"
IMAGE_DIR = "inspection_images"

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 1. 입력 항목들
inspection_date = datetime.now().strftime("%Y-%m-%d %H:%M")
material_lot = st.text_input("자재 / LOT명 입력")

# 💡 시험 방법 2가지 구분 (손톱박리 / 테이프 박리)
test_method = st.selectbox(
    "시험 방법", ["손톱박리", "테이프 박리"]
)

# 💡 선택 항목 (적합 / 부적합 구분)
inspection_result = st.selectbox(
    "검사 결과", ["적합", "부적합"]
)

uploaded_file = st.file_uploader(
    "현장 사진 첨부 (촬영 또는 파일 선택)", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="첨부된 사진 미리보기", width=250)

remarks = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

# 2. 저장 버튼
submitted = st.button("💾 검사 이력 저장하기", type="primary")

if submitted:
    if not material_lot:
        st.warning("⚠️ 자재/LOT명을 입력해 주세요.")
    else:
        image_filename = "없음"
        if uploaded_file is not None:
            # 💡 자재/LOT명과 날짜시간이 조합된 자동 파일명 생성
            safe_lot_name = "".join(c for c in material_lot if c.isalnum() or c in ('_', '-'))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_filename = f"{safe_lot_name}_{timestamp}_{uploaded_file.name}"
            
            image_path = os.path.join(IMAGE_DIR, image_filename)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        # 💡 데이터프레임에 시험방법 항목 추가
        new_data = pd.DataFrame([{
            "검사일시": inspection_date,
            "자재/LOT명": material_lot,
            "시험방법": test_method,
            "검사결과": inspection_result,
            "사진파일명": image_filename,
            "특이사항": remarks,
        }])

        if os.path.exists(DATA_FILE):
            try:
                df_existing = pd.read_csv(DATA_FILE)
                df_combined = pd.concat([df_existing, new_data], ignore_index=True)
            except Exception:
                df_combined = new_data
        else:
            df_combined = new_data

        df_combined.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        st.success("🎉 검사 이력이 성공적으로 저장되었습니다!")
        st.rerun()

# 3. 이력 조회 및 다운로드, 초기화 기능
st.markdown("---")
st.subheader("📋 검사 이력 조회 및 다운로드")

if os.path.exists(DATA_FILE):
    try:
        df_load = pd.read_csv(DATA_FILE)
        st.dataframe(df_load)
        
        # 📦 전체 데이터(엑셀 + 사진 폴더)를 ZIP 파일로 한 번에 다운로드하는 버튼
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            if os.path.exists(DATA_FILE):
                zip_file.write(DATA_FILE, arcname="inspection_history.csv")
            if os.path.exists(IMAGE_DIR):
                for root, dirs, files in os.walk(IMAGE_DIR
