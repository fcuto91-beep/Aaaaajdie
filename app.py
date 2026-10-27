import os
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="현장 검사 및 이력 관리", layout="centered")

st.title("🛡️ 모바일 공정 검사 및 이력 관리")

DATA_FILE = "inspection_history.csv"
IMAGE_DIR = "inspection_images"

if not os.path.exists(IMAGE_DIR):
  os.makedirs(IMAGE_DIR)

# 1. 검사일시 자동 생성
inspection_date = datetime.now().strftime("%Y-%m-%d %H:%M")

# 2. 자재/LOT명 입력
material_lot = st.text_input("자재 / LOT명 입력")

# 3. 검사결과 선택
inspection_result = st.selectbox(
    "검사 결과", ["Pass (적합)", "Fail (부적합)", "Warning (주의)"]
)

# 4. 사진 촬영 및 업로드
uploaded_file = st.file_uploader(
    "현장 사진 첨부 (촬영 또는 파일 선택)", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  st.markdown("---")
  # 안전하게 이미지 미리보기 출력
  try:
    st.image(uploaded_file, caption="첨부된 현장 검사 사진 미리보기")
  except Exception:
    st.image(uploaded_file)

# 5. 특이사항
remarks = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

# 제출 버튼
submitted = st.button("💾 검사 이력 저장하기", type="primary")

if submitted:
  if not material_lot:
    st.warning("⚠️ 자재/LOT명을 입력해 주세요.")
  else:
    image_filename = "없음"
    if uploaded_file is not None:
      image_filename = (
          f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
      )
      image_path = os.path.join(IMAGE_DIR, image_filename)
      with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    new_data = {
        "검사일시": [inspection_date],
        "자재/LOT명": [material_lot],
        "검사결과": [inspection_result],
        "사진파일명": [image_filename],
        "특이사항": [remarks],
    }

    df_new = pd.DataFrame(new_data)

    if os.path.exists(DATA_FILE):
      try:
        df_existing = pd.read_csv(DATA_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
      except Exception:
        df_combined = df_new
    else:
      df_combined = df_new

    df_combined.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    st.success("🎉 검사 이력이 성공적으로 저장되었습니다!")

# --- 📋 검사 이력 조회 및 엑셀 다운로드 ---
st.markdown("---")
st.subheader("📋 검사 이력 조회 및 다운로드")

if os.path.exists(DATA_FILE):
  try:
    df_load = pd.read_csv(DATA_FILE)
    st.dataframe(df_load)

    if not df_load.empty:
      if st.button("📥 엑셀 파일 다운로드 생성"):
        excel_path = "inspection_report.xlsx"

        from openpyxl import Workbook
        from openpyxl.drawing.image import Image as OpxImage

        wb = Workbook()
        ws = wb.active
        ws.title = "검사 이력"

        headers = ["검사일시", "자재/LOT명", "검사결과", "첨부사진", "특이사항"]
        ws.append(headers)

        for r_idx, row in df_load.iterrows():
          # 데이터가 없거나 누락되어도 에러 안 나게 안전하게 가져오기
          val_date = str(row.get("검사일시", ""))
          val_lot = str(row.get("자재/LOT명", ""))
          val_res = str(row.get("검사결과", ""))
          val_rem = str(row.get("특이사항", ""))
          img_filename = str(row.get("사진파일명", "없음"))

          row_data = [val_date, val_lot, val_res, "", val_rem]
          ws.append(row_data)

          current_row = r_idx + 2
          ws.row_dimensions[current_row].height = 80
          ws.column_dimensions["D"].width = 16

          # 이미지 삽입 안전 처리
          if (
              img_filename
              and img_filename != "없음"
              and img_filename != "nan"
              and img_filename.strip() != ""
          ):
            img_path = os.path.join(IMAGE_DIR, img_filename)
            if os.path.exists(img_path):
              try:
                img = OpxImage(img_path)
                img.width = 90
                img.height = 90
                ws.add_image(img, f"D{current_row}")
              except Exception as img_err:
                ws.cell(
                    row=current_row,
                    column=4,
                    value=f"[이미지 에러: {str(img_err)}]",
                )

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
        st.success("✨ 엑셀 파일 준비 완료!")
  except Exception as e:
    st.error(
        f"데이터를 읽어오는 중 문제가 발생했습니다. (파일을 초기화하면 해결됩니다) 에러내용: {e}"
    )
    if st.button("🗑️ 기존 손상된 데이터 초기화하기"):
      if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.success("초기화 완료! 페이지를 새로고침 해주세요.")
        st.rerun()
else:
  st.info("아직 저장된 검사 이력이 없습니다.")
