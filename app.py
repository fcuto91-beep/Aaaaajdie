from datetime import datetime
import os
import pandas as pd
from PIL import Image
import streamlit as st
 
# 페이지 설정 (모바일 최적화)
st.set_page_config(
    page_title="포장재 착인 박리 검사 시스템", page_icon="📦", layout="centered"
)
 
# 저장 폴더 설정
IMAGE_DIR = "inspection_images"
DATA_FILE = "inspection_data.csv"
 
if not os.path.exists(IMAGE_DIR):
  os.makedirs(IMAGE_DIR)
 
# 기존 데이터 불러오기 함수
 
 
def load_data():
  if os.path.exists(DATA_FILE):
    return pd.read_csv(DATA_FILE)
  else:
    return pd.DataFrame(
        columns=[
            "검사일시",
            "구분",
            "자재명/로트",
            "판정결과",
            "비고",
            "사진파일경로",
        ]
    )
 
 
st.title("📦 포장재 착인 박리 검사 이력 관리")
st.markdown("현장에서 스마트폰으로 간편하게 검사 결과를 기록하세요.")
 
# --- [1] 입력 폼 세션 ---
with st.form("inspection_form", clear_on_submit=True):
  st.subheader("📝 신규 검사 등록")
 
  # 구분 (단상자 / 용기)
  item_type = st.radio("검사 구분", ["단상자", "용기"], horizontal=True)
 
  # 자재명 및 로트번호
  material_name = st.text_input(
      "자재명 및 로트번호 (예: 콜마 뉴트리 단상자 / Lot.202610)", ""
  )
 
  # 판정 결과 (양호 / 불량)
  judgment = st.selectbox("착인 상태 판정", ["양호", "박리(불량)"])
 
  # 비고
  note = st.text_input("특이사항 (선택사항)", "")
 
  # 사진 촬영 및 업로드 (스마트폰 카메라 연동)
  # 스마트폰 브라우저에서 이 버튼을 누르면 즉시 카메라 촬영 선택지가 뜹니다.
  uploaded_file = st.file_uploader(
      "박리 검사 부위 사진 촬영/첨부", type=["jpg", "jpeg", "png"]
  )
 
  submitted = st.form_submit_button("검사 결과 저장하기")
 
  if submitted:
    if not material_name:
      st.error("자재명 및 로트번호를 입력해주세요!")
    elif uploaded_file is None:
      st.error("검사 사진을 첨부해주세요!")
    else:
      # 현재 시간
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
 
      # 이미지 저장
      image_filename = f"{file_timestamp}_{uploaded_file.name}"
      image_path = os.path.join(IMAGE_DIR, image_filename)
 
      image = Image.open(uploaded_file)
      image.save(image_path)
 
      # 데이터프레임에 추가
      df = load_data()
      new_row = {
          "검사일시": now_str,
          "구분": item_type,
          "자재명/로트": material_name,
          "판정결과": judgment,
          "비고": note,
          "사진파일경로": image_path,
      }
 
      df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
      df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
 
      st.success("✅ 검사 이력이 성공적으로 저장되었습니다!")
 
# --- [2] 저장된 이력 조회 및 엑셀 다운로드 ---
st.markdown("---")
st.subheader("📊 검사 이력 조회 및 내보내기")
 
df_display = load_data()
 
if not df_display.empty:
  # 엑셀 다운로드 버튼 생성
  csv = df_display.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      label="📥 전체 이력 엑셀(CSV) 다운로드",
      data=csv,
      file_name=f"착인검사_이력_{datetime.now().strftime('%Y%m%d')}.csv",
      mime="text/csv",
  )
 
  # 데이터 표 출력
  st.dataframe(df_display, use_container_width=True)
 
  # 최근 사진 미리보기
  st.markdown("### 📸 최근 등록된 사진 확인")
  for idx, row in df_display.head(5).iterrows():
    with st.expander(
        f"[{row['검사일시']}] {row['자재명/로트']} - {row['판정결과']}"
    ):
      st.write(f"**구분:** {row['구분']} | **비고:** {row['비고']}")
      if os.path.exists(row["사진파일경로"]):
        st.image(row["사진파일경로"], width=300)
      else:
        st.warning("이미지 파일을 찾을 수 없습니다.")
else:
  st.info("아직 등록된 검사 이력이 없습니다.")