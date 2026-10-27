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
  st.image(uploaded_file, caption="첨부된 현장 검사 사진 미리보기")

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

    new_data = pd.DataFrame([{
        "검사일시": inspection_date,
        "자재/LOT명": material_lot,
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

# --- 📋 검사 이력 조회 ---
st.markdown("---")
st.subheader("📋 검사 이력 조회")

if os.path.exists(DATA_FILE):
  try:
    df_load = pd.read_csv(DATA_FILE)
    st.dataframe(df_load)
  except Exception as e:
    st.error(f"데이터 로드 중 에러 발생: {e}")
else:
  st.info("아직 저장된 검사 이력이 없습니다.")
