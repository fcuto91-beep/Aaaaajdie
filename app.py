from datetime import datetime
import os
import pandas as pd
from PIL import Image
import streamlit as st

# 페이지 설정 (모바일 최적화)
st.set_page_config(
    page_title="포장재 착인 박리 검사 시스템",
    layout="centered",
)

# 저장 폴더 및 파일 설정 (CSV 형식으로 변경하여 오류 원천 차단)
IMAGE_DIR = "inspection_images"
DATA_FILE = "inspection_data.csv"

# 폴더가 없으면 생성
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR, exist_ok=True)

# 데이터 파일 초기화
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(
        columns=[
            "검사일시",
            "자재/LOT명",
            "검사결과",
            "사진파일명",
            "특이사항",
        ]
    )
    df_init.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

st.title("📦 포장재 착인 박리 검사 시스템")
st.write("현장 검사 데이터를 간편하게 기록하고 관리하는 모바일 전용 시스템입니다.")

with st.form("inspection_form", clear_on_submit=True):
    st.subheader("📝 검사 결과 입력")

    # 1. 검사일시 자동 입력
    default_date = datetime.now()
    inspection_date = st.text_input(
        "검사 일시", value=default_date.strftime("%Y-%m-%d %H:%M")
    )

    # 2. 자재/LOT명 입력
    material_lot = st.text_input(
        "자재 및 LOT명", placeholder="예: 박스 포장재 / LOT-20261027"
    )

    # 3. 검사 결과 (Pass / Fail)
    inspection_result = st.selectbox(
        "검사 결과 (박리 테스트)", ["Pass (적합)", "Fail (부적합)"]
    )

    # 4. 사진 촬영 및 업로드
    uploaded_file = st.file_uploader(
        "현장 사진 첨부 (촬영 또는 파일 선택)", type=["jpg", "jpeg", "png"]
    )
    if uploaded_file is not None:
      st.markdown("---")
      st.text(f"• 파일 명: {uploaded_file.name}")
      st.image(
          uploaded_file,
          caption="첨부된 현장 검사 사진 미리보기",
          use_container_width=True,
      )

    # 5. 특이사항
    remarks = st.text_area(
        "특이사항 및 조치 내용", placeholder="특이사항이 없으면 비워두세요."
    )

    # 제출 버튼
    submitted = st.form_submit_button("💾 검사 기록 저장하기")

if submitted:
    if not material_lot:
        st.warning("⚠️ 자재/LOT명을 입력해 주세요.")
    else:
        # 사진 저장 처리
        image_filename = "없음"
        if uploaded_file is not None:
            time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{time_tag}_{uploaded_file.name}"
            image_path = os.path.join(IMAGE_DIR, image_filename)

            img = Image.open(uploaded_file)
            img.save(image_path)

        # 데이터 추가
        new_data = {
            "검사일시": [inspection_date],
            "자재/LOT명": [material_lot],
            "검사결과": [inspection_result],
            "사진파일명": [image_filename],
            "특이사항": [remarks],
        }

        df_new = pd.DataFrame(new_data)

        # CSV 파일에 누적 저장
        df_existing = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

        st.success("🎉 검사 이력이 성공적으로 저장되었습니다!")

# --- 📋 검사 이력 조회 및 사진 포함 엑셀 다운로드 ---
st.markdown("---")
st.subheader("📋 검사 이력 조회 및 사진 포함 엑셀 다운로드")

if os.path.exists(DATA_FILE):
  df_load = pd.read_csv(DATA_FILE)
  st.dataframe(df_load)

  if not df_load.empty:
    if st.button("📥 사진이 포함된 엑셀 다운로드 생성"):
      excel_path = "inspection_report.xlsx"

      from openpyxl import Workbook
      from openpyxl.drawing.image import Image as OpxImage

      wb = Workbook()
      ws = wb.active
      ws.title = "검사 이력"

      # 엑셀 헤더 (사진파일명 텍스트 대신 '첨부사진'으로 지정)
      headers = ["검사일시", "자재/LOT명", "검사결과", "첨부사진", "특이사항"]
      ws.append(headers)

      # 데이터 행 추가 및 이미지 삽입
      for r_idx, row in df_load.iterrows():
        # 파일명 텍스트는 빼고 빈 칸으로 둠
        row_data = [
            row["검사일시"],
            row["자재/LOT명"],
            row["검사결과"],
            "",  # 텍스트 대신 빈 칸
            row["특이사항"],
        ]
        ws.append(row_data)

        # 이미지 파일 삽입 작업
        img_filename = row["사진파일명"]
        if (
            pd.notna(img_filename)
            and img_filename != "없음"
            and str(img_filename).strip() != ""
        ):
          img_path = os.path.join(IMAGE_DIR, str(img_filename))
          if os.path.exists(img_path):
            try:
              img = OpxImage(img_path)
              img.width = 90
              img.height = 90
              # D열에 사진 삽입
              cell_location = f"D{r_idx + 2}"
              ws.add_image(img, cell_location)
            except Exception as e:
              pass

        # 사진이 잘 보이도록 행 높이와 D열 너비 조절
        ws.row_dimensions[r_idx + 2].height = 75

      ws.column_dimensions["D"].width = 16

      wb.save(excel_path)

      with open(excel_path, "rb") as f:
        st.download_button(
            label="💾 엑셀 파일 다운로드 받기",
            data=f,
            file_name="inspection_report_with_images.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
      st.success("✨ 사진이 포함된 엑셀 파일 준비 완료!")
else:
  st.info("아직 저장된 검사 이력이 없습니다.")
