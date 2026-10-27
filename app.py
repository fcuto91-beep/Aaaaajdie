from datetime import datetime, timedelta, timezone
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

KST = timezone(timedelta(hours=9))
current_time_kst = datetime.now(KST)
current_time_str = current_time_kst.strftime("%Y-%m-%d %H:%M:%S")

st.info(f"⏰ 현재 검사 시각 (한국 시간): **{current_time_str}**")

material_lot = st.text_input("자재 / LOT명 입력")

st.markdown("---")
st.subheader("📝 시험 항목별 결과 판정")

nail_peel_result = st.selectbox(
    "1️⃣ 손톱박리 검사 결과", ["적합", "부적합"]
)

tape_peel_result = st.selectbox(
    "2️⃣ 테이프 박리 검사 결과", ["적합", "부적합"]
)

st.markdown("---")
uploaded_file = st.file_uploader(
    "현장 사진 첨부 (촬영 또는 파일 선택)", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="첨부된 사진 미리보기", width=250)

remarks = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

submitted = st.button("💾 검사 이력 저장하기", type="primary")

if submitted:
    if not material_lot:
        st.warning("⚠️ 자재/LOT명을 입력해 주세요.")
    else:
        inspection_date = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        
        image_filename = "없음"
        if uploaded_file is not None:
            safe_lot_name = "".join(c for c in material_lot if c.isalnum() or c in ('_', '-'))
            timestamp = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
            image_filename = f"{safe_lot_name}_{timestamp}_{uploaded_file.name}"
            
            image_path = os.path.join(IMAGE_DIR, image_filename)
            with open(image_path, "wb") as f:
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
                df_existing = pd.read_csv(DATA_FILE)
                df_combined = pd.concat([df_existing, new_data], ignore_index=True)
            except Exception:
                df_combined = new_data
        else:
            df_combined = new_data

        df_combined.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        st.success("🎉 검사 이력이 성공적으로 저장되었습니다!")
        st.rerun()

st.markdown("---")
st.subheader("📋 전체 검사 내역 리스트")

if os.path.exists(DATA_FILE):
    try:
        df_load = pd.read_csv(DATA_FILE)
        
        search_query = st.text_input("🔍 이력 검색 (LOT명 또는 특이사항 입력)", placeholder="검색어를 입력하세요...")
        if search_query:
            df_filtered = df_load[
                df_load.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            ].reset_index(drop=True)
        else:
            df_filtered = df_load.reset_index(drop=True)

        # 💡 깔끔한 기본 표 형식 그대로 출력
        st.dataframe(df_filtered, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔍 현장 사진 미리보기")
        st.markdown("저장된 이력의 사진을 확인하려면 아래에서 해당 돋보기 버튼을 눌러주세요.")

        # 세션 상태 관리 (미리보기용)
        if "preview_img" not in st.session_state:
            st.session_state.preview_img = None
        if "preview_title" not in st.session_state:
            st.session_state.preview_title = ""

        # 표 아래에 각 항목별로 파일명과 돋보기(미리보기) 버튼을 깔끔하게 행 형태로 배치
        for idx, row in df_filtered.iterrows():
            lot_val = row["자재/LOT명"]
            file_val = row["사진파일명"]
            date_val = row["검사일시"]

            if file_val != "없음":
                col1, col2, col3 = st.columns([2, 4, 1])
                with col1:
                    st.write(f"[{idx}] {lot_val}")
                with col2:
                    st.write(f"<small>{file_val}</small>", unsafe_allow_html=True)
                with col3:
                    # 💡 마우스를 올리면 "미리보기" 글자가 뜨는 돋보기 버튼
                    if st.button("🔍", key=f"zoom_{idx}", help="미리보기"):
                        st.session_state.preview_img = file_val
                        st.session_state.preview_title = f"LOT: {lot_val} ({date_val})"

        # 돋보기 버튼을 눌렀을 때 사진이 나타나는 영역
        if st.session_state.preview_img:
            st.markdown("---")
            st.markdown(f"🖼️ **미리보기 — {st.session_state.preview_title}**")
            target_path = os.path.join(IMAGE_DIR, st.session_state.preview_img)
            if os.path.exists(target_path):
                st.image(target_path, width=400)
                if st.button("❌ 미리보기 닫기"):
                    st.session_state.preview_img = None
                    st.rerun()
            else:
                st.warning("⚠️ 사진 파일을 찾을 수 없습니다.")

        st.markdown("---")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            if os.path.exists(DATA_FILE):
                zip_file.write(DATA_FILE, arcname="inspection_history.csv")
            if os.path.exists(IMAGE_DIR):
                for root, dirs, files in os.walk(IMAGE_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join("inspection_images", file)
                        zip_file.write(file_path, arcname=arcname)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 [전체 데이터 + 현장 사진] ZIP 다운로드",
            data=zip_buffer,
            file_name=f"inspection_backup_{datetime.now(KST).strftime('%Y%m%d')}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("")
        if st.button("🗑️ 데이터 파일 초기화하기 (오류 복구용)", use_container_width=True):
            os.remove(DATA_FILE)
            st.success("초기화 완료! 페이지를 새로고침 해주세요.")
            st.rerun()
            
    except Exception as e:
        st.error(f"데이터 파일 읽기 오류: {e}")
        if st.button("🗑️ 손상된 데이터 삭제하기"):
            os.remove(DATA_FILE)
            st.rerun()
else:
  st.info("아직 저장된 검사 이력이 없습니다.")
