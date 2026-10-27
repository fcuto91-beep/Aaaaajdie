import os
import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image

# 페이지 설정
st.set_page_config(page_title="포장재 착인 박리 검사 이력 관리", layout="centered")

# 데이터 저장을 위한 파일 경로 설정
EXCEL_FILE = "inspection_data.xlsx"
IMAGE_DIR = "captured_images"

# 폴더가 없을 때만 생성하도록 안전하게 수정 (에러 해결!)
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR, exist_ok=True)

# 엑셀 파일 초기화
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(
        columns=[
            "검사일시",
            "자재/LOT명",
            "검사결과",
            "사진파일명",
            "특이사항",
        ]
    )
    df_init.to_excel(EXCEL_FILE, index=False)

st.title("📦 포장재 착인 박리 검사 이력 관리")
st.write("현장 검사 데이터를 간편하게 기록하고 관리하는 모바일 전용 시스템입니다.")

with st.form("inspection_form", clear_on_submit=True):
    st.subheader("📝 검사 결과 입력")

    # 1. 검사일시 자동 입력 (수정 가능)
    default_date = datetime.now()
    inspection_date = st.text_input(
        "검사 일시", value=default_date.strftime("%Y-%m-%d %H:%M")
    )

    # 2. 자재/LOT명 입력
    material_lot = st.text_input(
        "자재 및 LOT명", placeholder="예: 박스 포장재 / LOT-20261027"
    )

    # 3. 검사 결과 (Pass / Fail)
    inspection_result = st.selectbox("검사 결과 (박리 테스트)", ["Pass (적합)", "Fail (부적합)"])

    # 4. 사진 촬영 및 업로드 (모바일 카메라 직접 연동 지원)
    uploaded_file = st.file_uploader(
        "현장 사진 첨부 (촬영 또는 파일 선택)", type=["jpg", "jpeg", "png"]
    )

    # 5. 특이사항
    remarks = st.text_area("특이사항 및 조치 내용", placeholder="특이사항이 없으면 비워두세요.")

    # 제출 버튼
    submitted = st.form_submit_button("💾 검사 기록 저장하기")

if submitted:
    if not material_lot:
        st.warning("⚠️ 자재/LOT명을 입력해 주세요.")
    else:
        # 사진 저장 처리
        image_filename = "없음"
        if uploaded_file is not None:
            # 파일 이름 중복 방지를 위한 타임스탬프 추가
            time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{time_tag}_{uploaded_file.name}"
            image_path = os.path.join(IMAGE_DIR, image_filename)

            # 이미지 저장
            img = Image.open(uploaded_file)
            img.save(image_path)

        # 엑셀 데이터에 추가
        new_data = {
            "검사일시": [inspection_date],
            "자재/LOT명": [material_lot],
            "검사결과": [inspection_result],
            "사진파일명": [image_filename],
            "특이사항": [remarks],
        }

        df_new = pd.DataFrame(new_data)

        # 기존 엑셀에 데이터 누적 저장
        df_existing = pd.read_excel(EXCEL_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(EXCEL_FILE, index=False)

        st.success("🎉 검사 이력이 성공적으로 저장되었습니다!")

# --- 저장된 이력 조회 및 다운로드 세션 ---
st.markdown("---")
st.subheader("📊 검사 이력 조회 및 엑셀 다운로드")

if os.path.exists(EXCEL_FILE):
    df_load = pd.read_excel(EXCEL_FILE)
    st.dataframe(df_load)

    if not df_load.empty:
        with open(EXCEL_FILE, "rb") as f:
            st.download_button(
                label="📥 전체 검사 이력 엑셀(Excel) 다운로드",
                data=f,
                file_name="packaging_inspection_history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
