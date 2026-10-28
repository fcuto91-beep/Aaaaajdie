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
now_kst = datetime.now(KST)
current_time_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")

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
    "현장 사진 첨부", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="사진 미리보기", width=250)

remarks = st.text_area("특이사항 및 조치 내용", placeholder="특이사항 입력")

submitted = st.button("💾 검사 이력 저장하기", type="primary")

if submitted:
    if not material_lot:
        st.warning("Please enter LOT name.")
    else:
        d_now = datetime.now(KST)
        inspection_date = d_now.strftime("%Y-%m-%d %H:%M:%S")
        
        image_filename = "none"
        if uploaded_file is not None:
            safe_lot = "".join(
                c for c in material_lot if c.isalnum() or c in ('_', '-')
            )
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
            except Exception:
                df_combined = new_data
        else:
            df_combined = new_data

        df_combined.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        st.success("Saved successfully!")
        st.rerun()

st.markdown("---")
st.subheader("📋 전체 검사 내역 리스트")

if os.path.exists(DATA_FILE):
    try:
        df_load = pd.read_csv(DATA_FILE)
        
        search_query = st.text_input(
            "🔍 이력 검색", placeholder="검색어 입력..."
        )
        if search_query:
            df_filtered = df_load[
                df_load.astype(str).apply(
                    lambda r: r.str.contains(search_query, case=False).any(),
                    axis=1
                )
            ].reset_index(drop=True)
        else:
            df_filtered = df_load.reset_index(drop=True)

        if "preview_img" not in st.session_state:
            st.session_state.preview_img = None
        if "preview_title" not in st.session_state:
            st.session_state.preview_title = ""

        cols_spec = [2.2, 1.5, 1.0, 1.0, 3.2, 0.8, 1.3]
        h_cols = st.columns(cols_spec)
        h_cols[0].markdown("**검사일시**")
        h_cols[1].markdown("**자재/LOT명**")
        h_cols[2].markdown("**손톱**")
        h_cols[3].markdown("**테이프**")
        h_cols[4].markdown("**사진파일명**")
        h_cols[5].markdown("**보기**")
        h_cols[6].markdown("**특이사항**")
        st.markdown(
            "<hr style='margin: 0px 0 10px 0; border: 1px solid #ddd;'>",
            unsafe_allow_html=True
        )

        for idx, row in df_filtered.iterrows():
            r_cols = st.columns(cols_spec)
            r_cols[0].write(str(row["검사일시"]))
            r_cols[1].write(str(row["자재/LOT명"]))
            r_cols[2].write(str(row["손톱박리"]))
            r_cols[3].write(str(row["테이프박리"]))
            r_cols[4].write(str(row["사진파일명"]))
            
            with r_cols[5]:
                fname = str(row["사진파일명"])
                if fname != "none":
                    # 💡 돋보기 이모지와 미리보기 툴팁 적용
                    if st.button("🔍", key=f"zoom_{idx}", help="미리보기"):
                        st.session_state.preview_img = fname
