import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import io
import zipfile

st.set_page_config(page_title="Inspection", layout="centered")

F = "inspection_history.csv"
D = "inspection_images"
LOGO_PATH = "logo.png"
ADMIN_PW = "1234"  # 💡 관리자 비밀번호

if not os.path.exists(D):
    os.makedirs(D)

KST = timezone(timedelta(hours=9))

# 💡 1단계: 맨 윗줄 정중앙에 CI 로고 배치
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_column_width=True)

st.markdown("")

# 💡 2단계: 제목 글자 크기를 더 키우고 모바일에서 보기 좋게 줄바꿈 적용
st.markdown("<h1 style='text-align: center; font-size: 36px !important; font-weight: bold; margin-bottom: 10px; line-height: 1.3;'>포장재 착인 검사 이력<br>관리 📦🧴</h1>", unsafe_allow_html=True)

st.info(f"⏰ 일자: **{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}**")

with st.form("f1", clear_on_submit=True):
    st.subheader("📝 시험 결과 입력")
    mat_no = st.text_input("포장재 번호")
    pack_name = st.text_input("포장재 약호")
    nail = st.selectbox("손톱 박리 결과", ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)"])
    tape = st.selectbox("테이프 박리 결과", ["🟢 적합 (PASS)", "🔴 부적합 (FAIL)"])
    up_file = st.file_uploader("검사 사진", type=["jpg", "jpeg", "png"])
    rem = st.text_area("특이사항")
    ok = st.form_submit_button("💾 Save", type="primary")

if ok:
    if not mat_no.strip():
        st.warning("⚠️ 포장재 번호를 입력해 주세요!")
    else:
        dt_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        fn = "none"
        if up_file:
            s_lot = "".join(c for c in mat_no if c.isalnum())
            t_str = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            fn = f"{s_lot}_{t_str}_{up_file.name}"
            file_path = os.path.join(D, fn)
            with open(file_path, "wb") as f:
                f.write(up_file.getbuffer())

        nd = pd.DataFrame([{
            "검사일시": dt_str,
            "포장재번호": mat_no,
            "포장재약호": pack_name if pack_name.strip() else "-",
            "손톱박리": nail,
            "테이프박리": tape,
            "사진파일명": fn,
            "특이사항": rem,
        }])

        df_c = nd
        if os.path.exists(F):
            try:
                df_ex = pd.read_csv(F)
                if not df_ex.empty:
                    df_c = pd.concat([df_ex, nd], ignore_index=True)
            except:
                pass

        df_c.to_csv(F, index=False, encoding="utf-8-sig")
        st.success("✅ Saved!")
        st.rerun()

# 💡 사진 팝업 모달 함수
@st.dialog("📸 사진 미리보기")
def show_image_popup(img_path, m_name, p_name, date_str):
    st.markdown(f"📦 **포장재 번호: {m_name}**")
    st.
